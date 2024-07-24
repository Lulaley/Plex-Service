from flask import Flask
from routes import RouteLogin as login
from static import Controleur
# Importez d'autres Blueprints ici

app = Flask(__name__)

# Enregistrez les Blueprints
app.register_blueprint(login)
# Enregistrez d'autres Blueprints ici

@app.route('/')
def hello_world():
    return 'Hello, World!'


if __name__ == '__main__':
    app.run(debug=True, port=5001, host='0.0.0.0')