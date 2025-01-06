from flask import render_template, request, flash, session, redirect, url_for
from static.Controleur.ControleurLdap import ControleurLdap
from static.Controleur.ControleurConf import ControleurConf
from static.Controleur.ControleurLog import write_log
from routes.RouteHome import home
from datetime import timedelta

def login(app):
    @app.route('/index', methods=['GET', 'POST'])
    def inner_login():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            remember_me = 'remember_me' in request.form

            write_log(f"Tentative de connexion pour l'utilisateur: {username}")

            conf = ControleurConf()
            base_dn = conf.get_config('LDAP', 'base_dn')
            # Créer une instance de ControleurLdap et tenter de se connecter
            ds = ControleurLdap()
            # Utilisation de authenticate_user pour vérifier les identifiants
            if ds.authenticate_user(username, password):
                write_log(f"Connexion réussie pour l'utilisateur: {username}")
                # Initialiser la variable de session
                session['username'] = username
                session.permanent = remember_me  # La session sera permanente si "remember_me" est coché
                if remember_me:
                    app.permanent_session_lifetime = timedelta(days=7)  # Durée de la session
                # Rediriger vers la page d'accueil pour vérifier les droits
                return redirect(url_for('inner_home'))
            else:
                write_log(f"Échec de la connexion pour l'utilisateur: {username}")
                # Affichage d'un message d'erreur en cas d'échec
                write_log('Échec de la connexion. Veuillez vérifier vos identifiants et réessayer.')
            ds.disconnect()
        else:
            write_log("Affichage du formulaire de connexion")
        # Rendu du formulaire de connexion
        return render_template('index.html')