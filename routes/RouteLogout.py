from flask import session, render_template

def logout(app):
    @app.route('/logout')
    def logout_user():
        # Supprimer les informations de session de l'utilisateur
        session.pop('username', None)
        # Rediriger vers la page d'accueil
        return render_template('index.html')
