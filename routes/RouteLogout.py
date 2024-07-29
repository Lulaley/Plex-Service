from flask import session, redirect, url_for

def logout(app):
    @app.route('/logout')
    def inner_logout():
        # Supprimer la session de l'utilisateur
        session.pop('username', None)
        # Rediriger vers la route racine
        return redirect(url_for('index'))
