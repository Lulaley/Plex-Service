from flask import render_template, request, redirect, url_for, flash, session
from static.Controleur.ControleurLdap import ControleurLdap
from static.Controleur.ControleurConf import ControleurConf
from static.Controleur.ControleurLog import write_log

def register(app):
    @app.route('/register', methods=['GET', 'POST'])
    def inner_register():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            email = request.form['email']

            conf = ControleurConf()
            base_dn = conf.get_config('LDAP', 'base_dn')
            ds = ControleurLdap()
            # Vérifier si le compte existe déjà
            write_log(f"Verif")
            if ds.search_user(username):
                write_log(f"Ce nom d'utilisateur existe déjà")
                ds.disconnect()
                return redirect(url_for('index'))
            else:
                write_log(f"Ce nom d'utilisateur n'existe pas")
            # Construire le DN et les attributs de l'utilisateur
            write_log(f"Construction de l'utilisateur")
            dn = f"uid={username},dmdName=users,{base_dn}"
            attributes = [
                ('objectClass', [b'inetOrgPerson', b'organizationalPerson', b'person']),
                ('uid', [username.encode('utf-8')]),
                ('sn', [username.encode('utf-8')]),  # Nom de famille
                ('cn', [username.encode('utf-8')]),  # Nom complet
                ('userPassword', [password.encode('utf-8')]),  # Mot de passe en clair
                ('mail', [email.encode('utf-8')])
            ]

            # Créer une instance de ControleurLdap et ajouter l'utilisateur
            userAdd = False
            write_log(f"Ajout de l'utilisateur")
            if ds.add_entry(dn, attributes):
                write_log(f"Utilisateur ajouté: {username}")
                userAdd = True
            else:
                write_log(f"Erreur lors de l'ajout de l'utilisateur1: {username}")
            ds.disconnect()
            if userAdd:
                session['username'] = username
                return redirect(url_for('home'))
            else:
                return redirect(url_for('index'))

        return redirect(url_for('index'))