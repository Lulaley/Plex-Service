from flask import render_template, request, flash, session, redirect, url_for
from static.Controleur.ControleurLdap import ControleurLdap
from static.Controleur.ControleurConf import ControleurConf
from static.Controleur.ControleurLog import write_log

def get_user_rights(username):
    ds = ControleurLdap()
    conf = ControleurConf()
    write_log(f"Recherche des droits pour l'utilisateur: {username}")
    res = ds.search_user(username)
    if res:
        user_dn = f"(uid={username})"
        search_base = conf.get_config('LDAP', 'base_dn')
        user_entry = ds.search_entry(search_base, user_dn)
        
        # Log the content of user_entry
        write_log(f"Contenu de user_entry pour l'utilisateur {username}: {user_entry}")
        
        if user_entry:
            # Extract the attributes dictionary from the first tuple
            attributes = user_entry[0][1]
            rights_agreement = attributes.get('rightsAgreement', [b''])[0].decode('utf-8')
            write_log(f"Droits trouvés pour l'utilisateur {username}: {rights_agreement}")
            ds.disconnect()
            return rights_agreement
    write_log(f"Utilisateur {username} non trouvé dans LDAP")
    ds.disconnect()
    return None

def home(app):
    write_log(f"{session["username"]} - Affichage de la page d'accueil")
    @app.route('/home')
    def inner_home():
        write_log("Vérification de l'utilisateur connecté")
        if 'username' in session:
            username = session['username']
            write_log(f"Utilisateur connecté: {username}")
            rights_agreement = get_user_rights(username)
            if rights_agreement == 'PlexService::SuperAdmin':
                write_log(f"Utilisateur {username} est SuperAdmin")
                return render_template('home.html', show_download=True, show_users=True, username=username)
            elif rights_agreement == 'PlexService::Admin':
                write_log(f"Utilisateur {username} est Admin")
                return render_template('home.html', show_download=True, show_users=False, username=username)
            else:
                write_log(f"Utilisateur {username} n'a pas de droits spécifiques")
                return render_template('home.html', show_download=False, show_users=False, username=username)
        else:
            write_log("Aucun utilisateur connecté, redirection vers l'index")
            return redirect(url_for('index'))