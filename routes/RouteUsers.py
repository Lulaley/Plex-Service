from flask import request, jsonify, render_template, session, redirect, url_for
from static.Controleur.ControleurLdap import ControleurLdap
from static.Controleur.ControleurLog import write_log

def users(app):
    @app.route('/users', methods=['GET', 'DELETE', 'POST'])
    def manage_users():
        if 'username' not in session:
            write_log("Aucun utilisateur connecté, redirection vers l'index")
            return redirect(url_for('auth.login'))

        username = session.get('username')
        rights_agreement = session.get('rights_agreement')

        if rights_agreement != 'PlexService::SuperAdmin':
            write_log(f"Accès refusé pour l'utilisateur {username} avec droits {rights_agreement}, redirection vers /home", 'ERROR')
            session['from_index'] = False
            return redirect(url_for('home'))

        write_log(f"Affichage de la page de gestion des utilisateurs pour l'utilisateur: {username}")
        session['from_index'] = False

        if request.method == 'GET':
            return list_users()
        elif request.method == 'DELETE':
            return delete_user()
        elif request.method == 'POST':
            action = request.json.get('action')
            if action == 'validate':
                return validate_user()
            elif action == 'make_admin':
                return make_admin()

    @app.route('/check_new_users', methods=['GET'])
    def check_new_users():
        if 'username' not in session:
            return jsonify({'new_users_count': 0})

        ldap = ControleurLdap()
        users = ldap.get_all_users()
        new_users_count = sum(1 for user in users if not user.get('rightsAgreement'))
        ldap.disconnect()
        return jsonify({'new_users_count': new_users_count})

def make_admin():
    if 'username' not in session or session.get('rights_agreement') != 'PlexService::SuperAdmin':
        write_log("Accès refusé: l'utilisateur n'est pas SuperAdmin", 'ERROR')
        return jsonify({'error': 'Accès refusé'}), 403

    data = request.json
    username = data.get('username')

    if not username:
        write_log("Informations manquantes pour rendre l'utilisateur admin", 'ERROR')
        return jsonify({'error': 'Informations manquantes'}), 400

    ldap = ControleurLdap()
    user_entry = ldap.search_user(username)
    if not user_entry:
        write_log(f"Utilisateur {username} non trouvé", 'ERROR')
        return jsonify({'error': 'Utilisateur non trouvé'}), 404

    # Vérifier si l'utilisateur est déjà admin
    if 'rightsAgreement' in user_entry[0][1] and user_entry[0][1]['rightsAgreement'][0].decode('utf-8') == 'PlexService::Admin':
        write_log(f"L'utilisateur {username} est déjà admin", 'ERROR')
        return jsonify({'error': 'Utilisateur déjà admin'}), 400

    # Remplacer l'attribut rightsAgreement avec la valeur PlexService::Admin
    ldap_attribute_replaced = ldap.replace_attribute(username, 'rightsAgreement', 'PlexService::Admin')
    if not ldap_attribute_replaced:
        write_log("Erreur lors de la mise à jour de l'attribut LDAP", 'ERROR')
        return jsonify({'error': 'Erreur lors de la mise à jour du compte'}), 500

    write_log(f"Utilisateur {username} est maintenant admin")
    ldap.disconnect()
    return jsonify({'message': 'Utilisateur promu admin avec succès'}), 200

def validate_user():
    data = request.json
    username = data.get('username')

    if not username:
        write_log("Informations manquantes pour la validation du compte", 'ERROR')
        return jsonify({'error': 'Informations manquantes'}), 400

    ldap = ControleurLdap()
    user_entry = ldap.search_user(username)
    if not user_entry:
        write_log(f"Utilisateur {username} non trouvé", 'ERROR')
        return jsonify({'error': 'Utilisateur non trouvé'}), 404

    # Vérifier si l'utilisateur a déjà un attribut rightsAgreement
    if 'rightsAgreement' in user_entry[0][1]:
        write_log(f"L'utilisateur {username} a déjà un attribut rightsAgreement", 'ERROR')
        return jsonify({'error': 'Utilisateur déjà validé'}), 400

    # Ajouter l'objectClass otherUserInfos si nécessaire
    if 'otherUserInfos' not in user_entry[0][1]['objectClass']:
        ldap_object_class_added = ldap.add_attribute(username, 'objectClass', 'otherUserInfos')
        if not ldap_object_class_added:
            write_log("Erreur lors de l'ajout de l'objectClass otherUserInfos", 'ERROR')
            return jsonify({'error': 'Erreur lors de la validation du compte'}), 500

    # Ajouter l'attribut rightsAgreement
    ldap_attribute_added = ldap.add_attribute(username, 'rightsAgreement', 'PlexService::User')
    if not ldap_attribute_added:
        write_log("Erreur lors de l'ajout de l'attribut LDAP", 'ERROR')
        return jsonify({'error': 'Erreur lors de la validation du compte'}), 500

    write_log(f"Compte validé pour l'utilisateur {username}")
    ldap.disconnect()
    return jsonify({'message': 'Compte validé avec succès'}), 200

def list_users():
    ldap = ControleurLdap()
    users = ldap.get_all_users()
    ldap.disconnect()
    return render_template('users.html', users=users)

def delete_user():
    data = request.json
    username = data.get('username')

    if not username:
        write_log("Informations manquantes pour la suppression du compte", 'ERROR')
        return jsonify({'error': 'Informations manquantes'}), 400

    ldap = ControleurLdap()
    user_entry = ldap.search_user(username)
    if not user_entry:
        write_log(f"Utilisateur {username} non trouvé", 'ERROR')
        return jsonify({'error': 'Utilisateur non trouvé'}), 404

    # Vérifier les droits de l'utilisateur connecté
    current_user_rights = session.get('rights_agreement')
    user_rights = user_entry[0][1].get('rightsAgreement', [b''])[0].decode('utf-8')

    if current_user_rights == 'PlexService::SuperAdmin':
        if user_rights == 'PlexService::SuperAdmin':
            write_log(f"Impossible de supprimer l'utilisateur {username} car il est SuperAdmin", 'ERROR')
            return jsonify({'error': 'Impossible de supprimer un SuperAdmin'}), 403
    elif current_user_rights == 'PlexService::Admin':
        if user_rights in ['PlexService::Admin', 'PlexService::SuperAdmin']:
            write_log(f"Impossible de supprimer l'utilisateur {username} car il a des droits égaux ou supérieurs", 'ERROR')
            return jsonify({'error': 'Impossible de supprimer cet utilisateur'}), 403

    user_deleted = ldap.delete_user(username)
    if not user_deleted:
        write_log("Erreur lors de la suppression de l'utilisateur dans la base LDAP", 'ERROR')
        return jsonify({'error': 'Erreur lors de la suppression du compte'}), 500

    write_log(f"Compte supprimé pour l'utilisateur {username}")
    ldap.disconnect()
    return jsonify({'message': 'Compte supprimé avec succès'}), 200