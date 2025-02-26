from flask import request, jsonify, render_template, session, redirect, url_for
from static.Controleur.ControleurWish import ControleurWish
from static.Controleur.ControleurLog import write_log
from static.Controleur.ControleurTMDB import ControleurTMDB

def wishes(app):
    @app.route('/demande', methods=['GET'])
    def manage_wishes():
        if 'username' not in session:
            write_log("Aucun utilisateur connecté, redirection vers l'index")
            return redirect(url_for('index'))

        username = session.get('username')
        rights_agreement = session.get('rights_agreement')
        write_log(f"Affichage des demandes pour l'utilisateur: {username} avec les droits: {rights_agreement}")

        if rights_agreement not in ['PlexService::User', 'PlexService::Admin', 'PlexService::SuperAdmin']:
            write_log(f"Utilisateur {username} n'a pas les droits nécessaires pour accéder à cette page", 'ERROR')
            return redirect(url_for('index'))

        return list_wishes(username, rights_agreement)

    @app.route('/create_wish', methods=['POST'])
    def create_wish():
        if 'username' not in session:
            return jsonify({'success': False, 'message': 'Utilisateur non connecté'})

        data = request.get_json()
        title = data.get('title')
        wish_type = data.get('type')
        username = session.get('username')

        wish_controller = ControleurWish()
        success = wish_controller.create_wish(username, title, wish_type)

        return jsonify({'success': success})

def list_wishes(username, rights_agreement):
    wish_controller = ControleurWish()
    if rights_agreement in ['PlexService::Admin', 'PlexService::SuperAdmin']:
        wishes = wish_controller.get_all_wishes()
    else:
        wishes = wish_controller.get_user_wishes(username)

    tmdb = ControleurTMDB()
    wish_details = []
    for wish in wishes:
        if wish['wishType'] == 'movie':
            details = tmdb.search_movie(wish['plexTitle'])
        elif wish['wishType'] == 'series':
            details = tmdb.search_serie(wish['plexTitle'])
        details['status'] = wish['status']
        details['wishId'] = wish['wishId']
        wish_details.append(details)
    
    session['from_index'] = False
    return render_template('wishes.html', wishes=wish_details)