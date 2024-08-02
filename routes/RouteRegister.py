from flask import render_template, request, redirect, url_for, flash, session
from static.Controleur.ControleurLdap import ControleurLdap
from static.Controleur.ControleurConf import ControleurConf
from static.Controleur.ControleurLog import write_log
<<<<<<< HEAD
from passlib.hash import ldap_salted_sha1 , ldap_sha1 # pip install passlib
=======
from passlib.hash import ldap_salted_sha1, ldap_sha1
import re

def is_hashed(password):
    # Vérifie si le mot de passe est déjà haché avec SHA, SSHA, MD5, CRYPT ou SMD5
    hash_patterns = [
        r'^\{SHA\}', r'^\{SSHA\}', r'^\{MD5\}', r'^\{CRYPT\}', r'^\{SMD5\}'
    ]
    return any(re.match(pattern, password) for pattern in hash_patterns)
>>>>>>> eaa6a103abe8f21046e83079deb17542c5938097

def register(app):
    @app.route('/register', methods=['GET', 'POST'])
    def inner_register():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['createPassword']
            email = request.form['email']

            if not is_hashed(password):
                hashed_password = ldap_salted_sha1.hash(password)
            else:
                hashed_password = password

            conf = ControleurConf()
            base_dn = conf.get_config('LDAP', 'base_dn')
            ds = ControleurLdap()
            # Vérifier si le compte existe déjà
            if ds.search_user(username):
                write_log(f"Ce nom d'utilisateur existe déjà")
                ds.disconnect()
                return redirect(url_for('index'))
            # Construire le DN et les attributs de l'utilisateur
            dn = f"uid={username},dmdName=users,{base_dn}"
            attributes = [
                ('objectClass', [b'inetOrgPerson', b'organizationalPerson', b'person']),
                ('uid', [username.encode('utf-8')]),
                ('sn', [username.encode('utf-8')]),  # Nom de famille
                ('cn', [username.encode('utf-8')]),  # Nom complet
                ('userPassword', [hashed_password.encode('utf-8')]),  # Mot de passe en clair
                ('mail', [email.encode('utf-8')])
            ]

            # Créer une instance de ControleurLdap et ajouter l'utilisateur
            userAdd = False
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