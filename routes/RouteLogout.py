from flask import session, redirect, url_for
from static.Controleur.ControleurLog import write_log

def logout(app):
    @app.route('/logout')
    def inner_logout():
        # Supprimer la session de l'utilisateur
        write_log(f"Utilisateur déconnecté: {session['username']}")
        session.pop('username', None)
        # Rediriger vers la route racine
        return redirect(url_for('index'))
