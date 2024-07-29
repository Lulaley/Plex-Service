from flask import render_template, request, flash , session
from static.Controleur.ControleurLdap import ControleurLdap
from static.Controleur.ControleurConf import ControleurConf


def login(app):
    @app.route('/home', methods=['GET', 'POST'])
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
                # Rendu de la page d'accueil en cas de succès
                ds.disconnect()
                session['username'] = username
                return render_template('home.html', username=session['username'])
            else:
                # Affichage d'un message d'erreur en cas d'échec
                flash('Échec de la connexion. Veuillez vérifier vos identifiants et réessayer.')
            ds.disconnect()
        # Rendu du formulaire de connexion
        return render_template('index.html')