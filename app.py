import os
import sys
import signal
import atexit
chemin_actuel = os.path.dirname(__file__)
chemin_routes = os.path.join(chemin_actuel, '../routes')
chemin_blueprints = os.path.join(chemin_actuel, 'blueprints')
sys.path.append(chemin_routes)
sys.path.append(chemin_blueprints)
from flask import Flask, render_template, session, redirect, url_for, request
from flask_wtf.csrf import CSRFProtect
from flask_talisman import Talisman

# Importation des blueprints
from blueprints.auth import auth_bp
from blueprints.home import home_bp

# Importation des routes legacy (à migrer progressivement)
from routes.RouteDownload import download, upload, start_download, stop_download_route, get_downloads_route, stream_download_route, restore_downloads_on_startup
from routes.RouteSeed import seed, get_media_list, start_seed_route, stop_seed_route, get_seeds_stats_route, upload_torrent_for_seed, restore_seeds_on_startup
from routes.RouteUsers import users
from routes.RouteWish import wishes
from routes.RouteSearch import search_routes

# Importation des controleurs
from static.Controleur.ControleurConf import ControleurConf
from static.Controleur.ControleurLog import write_log

app = Flask(__name__)
conf = ControleurConf()
app.secret_key = conf.get_config('APP', 'secret_key')

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
    force_https=False,  # À mettre True en production avec HTTPS
    content_security_policy=csp,
    content_security_policy_nonce_in=[]  # Désactiver les nonces pour permettre onclick
)

# Enregistrer les blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(home_bp)

# Gestionnaires d'erreurs personnalisés
@app.errorhandler(404)
def page_not_found(e):
    write_log(f"Erreur 404: Page non trouvée - {request.url}", 'WARNING')
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    write_log(f"Erreur 500: Erreur serveur - {str(e)}", 'ERROR')
    return render_template('errors/500.html', error=str(e) if app.debug else None), 500

@app.errorhandler(Exception)
def handle_exception(e):
    write_log(f"Exception non gérée: {str(e)}", 'ERROR')
    # Retourner 500 pour toutes les exceptions non gérées
    return render_template('errors/500.html', error=str(e) if app.debug else None), 500

@app.route('/')
def root():
    return redirect(url_for('auth.login'))

# Route index (redirection legacy)
@app.route('/index')
def index():
    return redirect(url_for('auth.login'))

# Enregistrement des routes legacy (à migrer progressivement vers blueprints)
download(app)
upload(app)
start_download(app)
stop_download_route(app)
stream_download_route(app)
get_downloads_route(app)
seed(app)
get_media_list(app)
start_seed_route(app)
stop_seed_route(app)
get_seeds_stats_route(app)
upload_torrent_for_seed(app)
users(app)
wishes(app)
search_routes(app)

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
        from routes.RouteDownload import active_downloads
        for download_id in list(active_downloads.keys()):
            active_downloads[download_id]['cancelled'] = True
        write_log(f"Arrêt de {len(active_downloads)} téléchargements en cours")
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

