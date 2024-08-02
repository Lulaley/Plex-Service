from flask import render_template, request
from static.Controleur.ControleurYGG import ControleurYGG



def download(app):
    @app.route('/download')
    def inner_download():
        # Vous pouvez ajouter ici la logique pour afficher les téléchargements
        return render_template('download.html')

def search(app):
    @app.route('/search', methods=['GET'])
    def inner_search():
        # Récupérer la requête de recherche
        titre = request.args.get('titre')
        uploader = request.args.get('uploader')
        categorie = request.args.get('categorie')
        sous_categorie = request.args.get('sous_categorie')


        # Utiliser le contrôleur YGG pour effectuer la recherche
        controleur_ygg = ControleurYGG()
        controleur_ygg.login()
        results = controleur_ygg.search(titre, uploader, categorie, sous_categorie)
        return render_template('download.html', results=results)