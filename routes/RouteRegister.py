from flask import render_template, request, redirect, url_for, flash, session
from static.Controleur.ControleurLdap import ControleurLdap
from static.Controleur.ControleurConf import ControleurConf

def register(app):
    @app.route('/register', methods=['GET', 'POST'])
    def inner_register():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            email = request.form['email']

            conf = ControleurConf()
            base_dn = conf.get_config('ldap', 'base_dn')
            # Construire le DN et les attributs de l'utilisateur

            dn = f"uid={username},dmdName=users,{base_dn}"
            attributes = [
                ('objectClass', [b'inetOrgPerson']),
                ('uid', [username.encode('utf-8')]),
                ('sn', [username.encode('utf-8')]),  # Nom de famille
                ('cn', [username.encode('utf-8')]),  # Nom complet
                ('userPassword', [password.encode('utf-8')]),
                ('mail', [email.encode('utf-8')])
            ]

            # Créer une instance de ControleurLdap et ajouter l'utilisateur
            ds = ControleurLdap()
            ds.add_entry(dn, attributes)
            ds.disconnect()
            session['username'] = username
            return redirect(url_for('home'))

        return render_template('register.html')