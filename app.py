import os
import sys
chemin_actuel = os.path.dirname(__file__)
chemin_routes = os.path.join(chemin_actuel, '../routes')
sys.path.append(chemin_routes)

from flask import Flask, Blueprint

from routes.RouteLogin import login
# Importez d'autres Blueprints ici

app = Flask(__name__)

login = Blueprint('login', __name__)

@app.route('/')
def hello_world():
    return 'Hello, World!'

@login.route('/login', methods=['GET', 'POST'])
def login_page():
    # Votre logique de traitement ici
    return 'Page de connexion'

if __name__ == '__main__':
    app.run(debug=True, port=5001, host='0.0.0.0')