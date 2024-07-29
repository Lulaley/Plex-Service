from flask import render_template, request, flash , session, redirect, url_for
from static.Controleur.ControleurLdap import ControleurLdap
from static.Controleur.ControleurConf import ControleurConf


def login(app):
    @app.route('/index', methods=['GET', 'POST'])
    def inner_login():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']

            conf = ControleurConf()
            base_dn = conf.get_config('LDAP', 'base_dn')
            # Créer une instance de ControleurLdap et tenter de se connecter
            ds = ControleurLdap()
            # Utilisation de authenticate_user pour vérifier les identifiants
            filter = f"(uid={username},dmdName=users,{base_dn})"
            if ds.authenticate_user(filter, password):
                # Déconnexion de l'instance LDAP
                ds.disconnect()
                # Initialiser la variable de session
                session['username'] = username
                # Rediriger vers la page d'accueil
                return redirect(url_for('home'))
            else:
                # Affichage d'un message d'erreur en cas d'échec
                flash('Échec de la connexion. Veuillez vérifier vos identifiants et réessayer.')
            ds.disconnect()
        # Rendu du formulaire de connexion
        return render_template('index.html')