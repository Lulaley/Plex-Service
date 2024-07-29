import os
import sys
chemin_actuel = os.path.dirname(__file__)
chemin_routes = os.path.join(chemin_actuel, '../routes')
sys.path.append(chemin_routes)
from flask import Flask, render_template


# Importation des routes
from routes.RouteLogin import login
from routes.RouteRegister import register
from routes.RouteLogout import logout

# Importation des controleurs
from static.Controleur.ControleurConf import ControleurConf

app = Flask(__name__)
conf = ControleurConf()
app.secret_key = conf.get_config('APP', 'secret_key')

@app.route('/')
def index():
    return render_template('index.html')
register(app)

@app.route('/home')
def home():
    login(app)
    return render_template('home.html')

if __name__ == '__main__':
    app.run(debug=True, port=conf.get_config('APP', 'port'), host='0.0.0.0')