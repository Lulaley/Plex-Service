from flask import render_template, request, redirect, url_for, flash, session
from static.Controleur.ControleurLdap import ControleurLdap
from static.Controleur.ControleurConf import ControleurConf
from static.Controleur.ControleurLog import write_log
import hashlib
import base64

def register(app):
    @app.route('/register', methods=['GET', 'POST'])
    def inner_register():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            email = request.form['email']

            # Hacher le mot de passe avec SHA-256
            sha256 = hashlib.sha256()
            sha256.update(password.encode('utf-8'))
            hashed_password = base64.b64encode(sha256.digest()).decode('utf-8')
            ldap_password = f"{{SHA}}{hashed_password}"

            conf = ControleurConf()
            base_dn = conf.get_config('LDAP', 'base_dn')
            # Construire le DN et les attributs de l'utilisateur

            dn = f"uid={username},dmdName=users,{base_dn}"
            attributes = [
                ('objectClass', [b'inetOrgPerson']),
                ('objectClass', [b'organizationalPerson']),
                ('objectClass', [b'person']),
                ('uid', [username.encode('utf-8')]),
                ('sn', [username.encode('utf-8')]),  # Nom de famille
                ('cn', [username.encode('utf-8')]),  # Nom complet
                ('userPassword', [ldap_password.encode('utf-8')]),
                ('mail', [email.encode('utf-8')])
            ]

            # Créer une instance de ControleurLdap et ajouter l'utilisateur
            while True:
                ds = ControleurLdap()
                try:
                    ds.bind_as_root()
                    ds.add_entry(dn, attributes)
                    ds.disconnect()
                    break
                except Exception as e:
                    write_log(f"Erreur lors de l'ajout de l'utilisateur: {str(e)}")
                    flash('Erreur lors de l\'ajout de l\'utilisateur. Veuillez réessayer.')
                    ds.disconnect()
                    return render_template('register.html')
            session['username'] = username
            return redirect(url_for('home'))

        return render_template('register.html')