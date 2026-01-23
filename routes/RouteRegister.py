from flask import render_template, request, redirect, url_for, flash, session
from static.Controleur.ControleurLdap import ControleurLdap
from static.Controleur.ControleurConf import ControleurConf
from static.Controleur.ControleurLog import write_log
from passlib.hash import ldap_salted_sha1, ldap_sha1
import re

def is_hashed(password):
    # Vérifie si le mot de passe est déjà haché avec SHA, SSHA, MD5, CRYPT ou SMD5
    hash_patterns = [
        r'^\{SHA\}', r'^\{SSHA\}', r'^\{MD5\}', r'^\{CRYPT\}', r'^\{SMD5\}'
    ]
    return any(re.match(pattern, password) for pattern in hash_patterns)

def register(app):
    @app.route('/register', methods=['GET', 'POST'])
    def inner_register():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['createPassword']
            email = request.form['email']

            write_log(f"Tentative d'inscription pour l'utilisateur: {username}")
            
            # Validation du nom d'utilisateur
            if not username or len(username.strip()) < 3:
                write_log(f"Nom d'utilisateur invalide (trop court): {username}", 'ERROR')
                flash('Le nom d\'utilisateur doit contenir au moins 3 caractères')
                return redirect(url_for('auth.login'))
            
            if len(username) > 50:
                write_log(f"Nom d'utilisateur invalide (trop long): {username}", 'ERROR')
                flash('Le nom d\'utilisateur ne peut pas dépasser 50 caractères')
                return redirect(url_for('auth.login'))
            
            # Vérifier que le nom ne contient pas trop d'espaces consécutifs
            if '  ' in username:
                write_log(f"Nom d'utilisateur invalide (espaces multiples): {username}", 'ERROR')
                flash('Le nom d\'utilisateur ne peut pas contenir plusieurs espaces consécutifs')
                return redirect(url_for('auth.login'))
            
            # Vérifier que le nom ne contient que des caractères autorisés (lettres, chiffres, espaces, tirets, underscores)
            if not re.match(r'^[a-zA-Z0-9 _.-]+$', username):
                write_log(f"Nom d'utilisateur invalide (caractères non autorisés): {username}", 'ERROR')
                flash('Le nom d\'utilisateur ne peut contenir que des lettres, chiffres, espaces, tirets et underscores')
                return redirect(url_for('auth.login'))
            
            if not is_hashed(password):
                hashed_password = ldap_salted_sha1.hash(password)
            else:
                hashed_password = password

            conf = ControleurConf()
            base_dn = conf.get_config('LDAP', 'base_dn')
            ds = ControleurLdap()
            # Vérifier si le compte existe déjà
            if ds.search_user(username):
                write_log(f"L'utilisateur {username} existe déjà")
                ds.disconnect()
                flash('Ce nom d\'utilisateur existe déjà')
                return redirect(url_for('auth.login'))
            write_log(f"L'utilisateur {username} n'existe pas, ajout en cours")
            # Construire le DN et les attributs de l'utilisateur
            dn = f"uid={username},dmdName=users,{base_dn}"
            attributes = [
                ('objectClass', [b'inetOrgPerson', b'organizationalPerson', b'person', b'otherUserInfos']),
                ('uid', [username.encode('utf-8')]),
                ('sn', [username.encode('utf-8')]),  # Nom de famille
                ('cn', [username.encode('utf-8')]),  # Nom complet
                ('userPassword', [hashed_password.encode('utf-8')]),  # Mot de passe en clair
                ('mail', [email.encode('utf-8')]),
                ('rightsAgreement', [b'PlexService::New']),  # Accord de droits par défaut
            ]

            # Créer une instance de ControleurLdap et ajouter l'utilisateur
            userAdd = False
            if ds.add_entry(dn, attributes):
                write_log(f"Utilisateur ajouté: {username}")
                userAdd = True
            else:
                write_log(f"Erreur lors de l'ajout de l'utilisateur: {username}", 'ERROR')
                ds.disconnect()
            if userAdd:
                session['username'] = username
                return redirect(url_for('home.home'))
            else:
                return redirect(url_for('auth.login'))