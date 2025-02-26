from flask import request, jsonify, render_template, session, redirect, url_for
from static.Controleur.ControleurTMDB import ControleurTMDB
from static.Controleur.ControleurLog import write_log

def search_routes(app):
    @app.route('/search', methods=['GET'])
    def search_page():
        if 'username' not in session:
            write_log("Aucun utilisateur connecté, redirection vers l'index")
            return redirect(url_for('index'))
        return render_template('search.html')

    @app.route('/search_tmdb', methods=['GET'])
    def search_tmdb():
        query = request.args.get('query')
        if not query:
            return jsonify([])

        tmdb_controller = ControleurTMDB()
        movie_results = tmdb_controller.search_movie_name(query)
        tv_results = tmdb_controller.search_serie_name(query)

        results = {
            'movies': movie_results,
            'tv_shows': tv_results
        }
        return jsonify(results)