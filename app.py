import os
import sys
chemin_actuel = os.path.dirname(__file__)
chemin_routes = os.path.join(chemin_actuel, '../routes')
sys.path.append(chemin_routes)
from flask import Flask, render_template, session, redirect, url_for

# Importation des routes
from routes.RouteLogin import login
from routes.RouteRegister import register
from routes.RouteLogout import logout
from routes.RouteHome import home
from routes.RouteDownload import download, upload, start_download, stop_download_route
from routes.RouteSeed import seed, get_media_list, start_seed_route, stop_seed_route, get_seeds_stats_route, upload_torrent_for_seed, restore_seeds_route
from routes.RouteUsers import users
from routes.RouteWish import wishes
from routes.RouteSearch import search_routes

# Importation des controleurs
from static.Controleur.ControleurConf import ControleurConf

app = Flask(__name__)
conf = ControleurConf()
app.secret_key = conf.get_config('APP', 'secret_key')

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
seed(app)
get_media_list(app)
start_seed_route(app)
stop_seed_route(app)
get_seeds_stats_route(app)
upload_torrent_for_seed(app)
restore_seeds_route(app)
users(app)
wishes(app)
search_routes(app)

if __name__ == '__main__':
    app.run(debug=True, port=conf.get_config('APP', 'port'), host='0.0.0.0')

