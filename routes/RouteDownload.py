from flask import render_template, request, session, redirect, url_for
from static.Controleur.ControleurYGG import ControleurYGG
from static.Controleur.ControleurLog import write_log



def download(app):
    @app.route('/download')
    def inner_download():
        username = session['username']
        write_log(f"Affichage de la page de téléchargements pour l'utilisateur: {username}")
        # Vous pouvez ajouter ici la logique pour afficher les téléchargements
        return render_template('download.html', username=username)

def search(app):
    @app.route('/search', methods=['GET'])
    def inner_search():
        # Récupérer la requête de recherche
        titre = request.args.get('titre')
        uploader = request.args.get('uploader')
        categorie = request.args.get('categorie')
        sous_categorie = request.args.get('sous_categorie')

        write_log(f"Recherche de '{titre}' par '{uploader}' dans la catégorie '{categorie}' et sous-catégorie '{sous_categorie}'")
        # Utiliser le contrôleur YGG pour effectuer la recherche
        controleur_ygg = ControleurYGG()
        if controleur_ygg.login():
            results = controleur_ygg.search(titre, uploader, categorie, sous_categorie)
            return render_template('download.html', results=results)
        return redirect(url_for('download'))