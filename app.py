from flask import render_template

from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from static.Controleur.ControleurUser import User
import os
import sys
import signal
import atexit
from datetime import timedelta
chemin_actuel = os.path.dirname(__file__)
chemin_routes = os.path.join(chemin_actuel, '../routes')
chemin_blueprints = os.path.join(chemin_actuel, 'blueprints')
sys.path.append(chemin_routes)
sys.path.append(chemin_blueprints)
from flask import Flask, render_template, session, redirect, url_for, request
from flask_wtf.csrf import CSRFProtect
from flask_talisman import Talisman
from flask_compress import Compress
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import redis

# Importation des blueprints
from blueprints.auth import auth_bp
from blueprints.home import home_bp
from blueprints.admin import admin_bp
from blueprints.wishes import wishes_bp
from blueprints.search import search_bp
from blueprints.seed import seed_bp, restore_seeds_on_startup
from blueprints.download import download_bp, restore_downloads_on_startup
from blueprints.health import health_bp

# Importation des controleurs
from static.Controleur.ControleurConf import ControleurConf
from static.Controleur.ControleurLog import write_log


app = Flask(__name__)
conf = ControleurConf()
app.secret_key = conf.get_config('APP', 'secret_key')

# Configuration des sessions
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)  # 24h par défaut
app.config['SESSION_PERMANENT'] = True  # Marquer sessions comme permanentes
app.config['SESSION_COOKIE_SECURE'] = True  # HTTPS uniquement (mettre False en dev local)
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Pas accessible en JavaScript
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Protection CSRF supplémentaire

# Gestion de l’erreur 403 Forbidden
@app.errorhandler(403)
def forbidden(e):
    return render_template('403.html'), 403

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    """Charge un utilisateur avec cache LDAP (TTL 5min)."""
    try:
        from static.Controleur.ControleurCache import cache
        
        # 1. Chercher dans cache Redis
        cache_key = f"user:{user_id}"
        user_info = cache.get(cache_key)
        
        if user_info:
            # CACHE HIT : pas d'appel LDAP
            rights = user_info.get('rights', 'PlexService::User')
            return User(user_id, rights)
        
        # 2. CACHE MISS : appel LDAP
        try:
            from static.Controleur.ControleurLdap import ControleurLdap
            ds = ControleurLdap()
            user_info = ds.search_user(user_id)
            ds.disconnect()
            
            if user_info:
                # 3. Sauver dans cache pour 5 minutes
                cache.set(cache_key, user_info, timeout=300)
                rights = user_info.get('rights', 'PlexService::User')
            else:
                rights = 'PlexService::User'
        except Exception as e:
            write_log(f"Erreur LDAP dans load_user: {e}", "ERROR")
            rights = 'PlexService::User'
        
        return User(user_id, rights)
    except Exception as e:
        write_log(f"Erreur load_user: {e}", "ERROR")
        return User(user_id, rights="PlexService::User")

# Compression Gzip pour réduire la taille des réponses
Compress(app)

# Connexion Redis pour cache et rate limiting
try:
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    redis_client.ping()
    write_log("Connexion Redis réussie")
except redis.ConnectionError:
    write_log("Redis non disponible, rate limiting désactivé", "WARNING")
    redis_client = None

# Rate limiting - Protection brute-force
if redis_client:
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        storage_uri="redis://localhost:6379",
        storage_options={"socket_connect_timeout": 30},
        strategy="fixed-window"
    )
    write_log("Rate limiting activé")
else:
    # Limiter sans storage (en mémoire, moins fiable multi-workers)
    limiter = Limiter(
        app=app,
        key_func=get_remote_address
    )
    write_log("Rate limiting activé (mode mémoire)")

# Cache pour assets statiques
@app.after_request
def add_cache_headers(response):
    """Ajoute les headers de cache pour les fichiers statiques"""
    if 'static' in request.path:
        # Cache les assets statiques pendant 1 an
        response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
    else:
        # Pas de cache pour les pages dynamiques
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response

# Protection CSRF
csrf = CSRFProtect(app)

# Headers de sécurité HTTP
csp = {
    'default-src': "'self'",
    'script-src': ["'self'", "'unsafe-inline'"],  # Nécessaire pour onclick inline
    'style-src': ["'self'", "'unsafe-inline'"],
    'img-src': ["'self'", 'data:', 'https:'],
    'font-src': ["'self'", 'data:'],
}
Talisman(app, 
    force_https=True,  # À mettre True en production avec HTTPS
    content_security_policy=csp,
    content_security_policy_nonce_in=[]  # Désactiver les nonces pour permettre onclick
)

# Enregistrer les blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(home_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(wishes_bp)
app.register_blueprint(search_bp)
app.register_blueprint(seed_bp, url_prefix='')
app.register_blueprint(download_bp, url_prefix='')
app.register_blueprint(health_bp, url_prefix='')  # Healthcheck /health

# Initialiser le limiter unique dans tous les blueprints qui en ont besoin
from blueprints.auth import init_limiter as init_limiter_auth
from blueprints.download import init_limiter as init_limiter_download
from blueprints.seed import init_limiter as init_limiter_seed
from blueprints.wishes import init_limiter as init_limiter_wishes

init_limiter_auth(limiter)
init_limiter_download(limiter)
init_limiter_seed(limiter)
init_limiter_wishes(limiter)

# Enregistrer les handlers d'erreurs globaux
from static.Controleur.ControleurErrors import register_error_handlers
register_error_handlers(app)

@app.route('/')
def root():
    return redirect(url_for('auth.login'))

# Route index (redirection legacy)
@app.route('/index')
def index():
    return redirect(url_for('auth.login'))

# Restaurer les seeds au démarrage
restore_seeds_on_startup()

# Restaurer les téléchargements au démarrage
restore_downloads_on_startup()

# Gestion de l'arrêt propre du service
def cleanup():
    """Fonction de nettoyage appelée lors de l'arrêt du service"""
    from static.Controleur.ControleurLog import write_log
    from static.Controleur.ControleurLibtorrent import cleanup_session
    write_log("Arrêt du service Plex-Service - Nettoyage en cours...")
    
    # Nettoyer la session libtorrent
    cleanup_session()
    
    # Arrêter tous les téléchargements en cours
    try:
        from static.Controleur.ControleurTorrent import downloads, downloads_lock
        with downloads_lock:
            for download_id in list(downloads.keys()):
                if 'handle' in downloads[download_id]:
                    downloads[download_id]['cancelled'] = True
            write_log(f"Arrêt de {len(downloads)} téléchargements en cours")
    except Exception as e:
        write_log(f"Erreur lors de l'arrêt des téléchargements: {e}", "ERROR")
    
    write_log("Nettoyage terminé")

def signal_handler(signum, frame):
    """Gestion des signaux SIGTERM et SIGINT"""
    cleanup()
    sys.exit(0)

# Enregistrer les handlers pour les signaux
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)
atexit.register(cleanup)

if __name__ == '__main__':
    app.run(debug=True, port=conf.get_config('APP', 'port'), host='0.0.0.0')

