from flask import request, jsonify, render_template, session, redirect, url_for
from static.Controleur.ControleurLdap import ControleurLdap
from static.Controleur.ControleurLog import write_log

def users(app):
    @app.route('/users', methods=['GET', 'DELETE', 'POST'])
    def manage_users():
        if 'username' in session:
            username = session.get('username')
            write_log(f"Affichage de la page de gestion des utilisateurs pour l'utilisateur: {username}")
            if request.method == 'GET':
                return list_users()
            elif request.method == 'DELETE':
                return delete_user()
            elif request.method == 'POST':
                return validate_user()
        else:
            write_log("Aucun utilisateur connecté, redirection vers l'index")
            return redirect(url_for('index'))

def validate_user():
    data = request.json
    username = data.get('username')

    if not username:
        write_log("Informations manquantes pour la validation du compte", 'ERROR')
        return jsonify({'error': 'Informations manquantes'}), 400

    ldap = ControleurLdap()
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
    user_deleted = ldap.delete_user(username)
    if not user_deleted:
        write_log("Erreur lors de la suppression de l'utilisateur dans la base LDAP", 'ERROR')
        return jsonify({'error': 'Erreur lors de la suppression du compte'}), 500

    write_log(f"Compte supprimé pour l'utilisateur {username}")
    ldap.disconnect()
    return jsonify({'message': 'Compte supprimé avec succès'}), 200