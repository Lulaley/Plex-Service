from flask import render_template, request, redirect, url_for, flash
from static.Controleur.ControleurLdap import ControleurLdap
from static.Controleur.ControleurConf import ControleurConf


def login(app):
    @app.route('/', methods=['GET', 'POST'])
    def inner_login():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']

            conf = ControleurConf.__init__()
            base_dn = conf.get_config('ldap', 'base_dn')
            # Créer une instance de ControleurLdap et tenter de se connecter
            ds = ControleurLdap.__init__()
            # Utilisation de authenticate_user pour vérifier les identifiants
            filter = f"(uid={username},dmdName=users,{base_dn})"
            if ds.authenticate_user(filter, password):
                # Redirection vers la page d'accueil en cas de succès
                return redirect(url_for('home'))
            else:
                # Affichage d'un message d'erreur en cas d'échec
                flash('Échec de la connexion. Veuillez vérifier vos identifiants et réessayer.')
        # Rendu du formulaire de connexion
        return render_template('home.html')