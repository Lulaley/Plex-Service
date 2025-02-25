from flask import request, jsonify, render_template, session, redirect, url_for
from static.Controleur.ControleurWish import ControleurWish
from static.Controleur.ControleurLog import write_log
from static.Controleur.ControleurTMDB import ControleurTMDB
from datetime import datetime

def extract_uid_from_dn(dn):
    # Assuming the DN is in the format "uid=<username>,..."
    parts = dn.split(',')
    for part in parts:
        if part.startswith('uid='):
            return part.split('=')[1]
    return dn

def format_date(date_str):
    # Convert the date string to a datetime object
    date_obj = datetime.strptime(date_str, '%Y%m%d%H%M%SZ')
    # Format the datetime object to the desired format
    return date_obj.strftime('%d-%m-%Y')

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

    @app.route('/wish_details/<wish_id>', methods=['GET'])
    def wish_details(wish_id):
        if 'username' not in session:
            return jsonify({'success': False, 'message': 'Utilisateur non connecté'})

        wish_controller = ControleurWish()
        wish = wish_controller.get_wish_by_id(wish_id)

        if not wish:
            return jsonify({'success': False, 'message': 'Demande non trouvée'})

        tmdb = ControleurTMDB()
        if wish['wishType'] == 'movie':
            details = tmdb.search_movie(wish['plexTitle'])
        elif wish['wishType'] == 'series':
            details = tmdb.search_serie(wish['plexTitle'])

        details['status'] = wish['status']
        details['wishId'] = wish['wishId']
        details['requestDate'] = format_date(wish['requestDate'])
        details['wishOwner'] = extract_uid_from_dn(wish['wishOwner'])

        return jsonify(details)

    @app.route('/validate_wish/<wish_id>', methods=['POST'])
    def validate_wish(wish_id):
        if 'username' not in session:
            return jsonify({'success': False, 'message': 'Utilisateur non connecté'})

        rights_agreement = session.get('rights_agreement')
        if rights_agreement not in ['PlexService::Admin', 'PlexService::SuperAdmin']:
            return jsonify({'success': False, 'message': 'Droits insuffisants'})

        wish_controller = ControleurWish()
        wish = wish_controller.get_wish_by_id(wish_id)

        if not wish:
            return jsonify({'success': False, 'message': 'Demande non trouvée'})

        success = wish_controller.validate_wish(extract_uid_from_dn(wish['wishOwner']), wish_id)

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
        details['poster_path'] = details.get('poster_path', '')
        details['title'] = details.get('title', wish['plexTitle'])
        details['requestDate'] = format_date(wish['requestDate'])
        details['wishOwner'] = extract_uid_from_dn(wish['wishOwner'])
        wish_details.append(details)
    
    session['from_index'] = False
    return render_template('wishes.html', wishes=wish_details)