from flask import redirect, url_for, session

def logout(app):
    @app.route('/logout')
    def logout_user():
        # Supprimer les informations de session de l'utilisateur
        session.pop('username', None)
        # Rediriger vers la page d'accueil
        return redirect(url_for('index'))
