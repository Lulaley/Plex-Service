import os
import sys
chemin_actuel = os.path.dirname(__file__)
chemin_routes = os.path.join(chemin_actuel, '../routes')
sys.path.append(chemin_routes)
from flask import Flask, render_template
from routes.RouteLogin import login

app = Flask(__name__)


@app.route('/')
def hello_world():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True, port=5001, host='0.0.0.0')