import os
import sys
import signal
import atexit
chemin_actuel = os.path.dirname(__file__)
chemin_routes = os.path.join(chemin_actuel, '../routes')
sys.path.append(chemin_routes)
from flask import Flask, render_template, session, redirect, url_for, request
from flask_wtf.csrf import CSRFProtect
from flask_talisman import Talisman

# Importation des routes
from routes.RouteLogin import login
from routes.RouteRegister import register
from routes.RouteLogout import logout
from routes.RouteHome import home
from routes.RouteDownload import download, upload, start_download, stop_download_route, get_downloads_route, stream_download_route, restore_downloads_on_startup
from routes.RouteSeed import seed, get_media_list, start_seed_route, stop_seed_route, get_seeds_stats_route, upload_torrent_for_seed, restore_seeds_on_startup
from routes.RouteUsers import users
from routes.RouteWish import wishes
from routes.RouteSearch import search_routes

# Importation des controleurs
from static.Controleur.ControleurConf import ControleurConf

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

@app.route('/')
def root():
    return redirect(url_for('index'))

@app.route('/index')
def index():
    return render_template('index.html')

""" @app.route('/home')
def home():
    if 'username' in session:
        return render_template('home.html', username=session['username'])
    else:
        return redirect(url_for('index')) """

# Enregistrement des routes
login(app)
register(app)
logout(app)
home(app)
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

