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

            conf = ControleurConf()
            base_dn = conf.get_config('LDAP', 'base_dn')
            # Construire le DN et les attributs de l'utilisateur

            dn = f"uid={username},dmdName=users,{base_dn}"
            attributes = [
                ('objectClass', [b'inetOrgPerson', b'organizationalPerson', b'person']),
                ('uid', [username.encode('utf-8')]),
                ('sn', [username.encode('utf-8')]),  # Nom de famille
                ('cn', [username.encode('utf-8')]),  # Nom complet
                ('userPassword', [password.encode('utf-8')]),
                ('mail', [email.encode('utf-8')])
            ]

            # Créer une instance de ControleurLdap et ajouter l'utilisateur
            userAdd = False
            while True:
                ds = ControleurLdap()
                try:
                    ds.bind_as_root()
                    if (ds.add_entry(dn, attributes)):
                        write_log(f"Utilisateur ajouté: {username}")
                        flash('Utilisateur ajouté avec succès.')
                        userAdd = True
                    else:
                        write_log(f"Erreur lors de l'ajout de l'utilisateur: {username}")
                        flash('Erreur lors de l\'ajout de l\'utilisateur. Veuillez réessayer.')
                    ds.disconnect()
                    break
                except Exception as e:
                    write_log(f"Erreur lors de l'ajout de l'utilisateur: {str(e)}")
                    flash('Erreur lors de l\'ajout de l\'utilisateur. Veuillez réessayer.')
                    ds.disconnect()
                    return render_template('register.html')
            if userAdd:
                session['username'] = username
                return redirect(url_for('home'))
            else:
                return render_template('index.html')

        return render_template('register.html')