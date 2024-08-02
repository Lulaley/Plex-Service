from flask import render_template, request, flash, session, redirect, url_for
from static.Controleur.ControleurLdap import ControleurLdap
from static.Controleur.ControleurConf import ControleurConf
from static.Controleur.ControleurLog import write_log

def get_user_rights(username):
    ds = ControleurLdap()
    conf = ControleurConf()
    write_log(f"Recherche des droits pour l'utilisateur: {username}")
    if ds.search_user(username):
        user_dn = f"(uid={username})"
        search_base = conf.get_config('LDAP', 'base_dn')
        user_entry = ds.search_entry(search_base, user_dn)
        rights_agreement = user_entry.get('rightsAgreement', [None])[0]
        write_log(f"Droits trouvés pour l'utilisateur {username}: {rights_agreement}")
        ds.disconnect()
        return rights_agreement
    write_log(f"Utilisateur {username} non trouvé dans LDAP")
    ds.disconnect()
    return None

def home(app):
    write_log("Affichage de la page d'accueil")
    @app.route('/home')
    def inner_home():
        if 'username' in session:
            username = session['username']
            write_log(f"Utilisateur connecté: {username}")
            rights_agreement = get_user_rights(username)
            if rights_agreement == 'PlexService::SuperAdmin':
                write_log(f"Utilisateur {username} est SuperAdmin")
                return render_template('home.html', show_download=True, show_users=True)
            elif rights_agreement == 'PlexService::Admin':
                write_log(f"Utilisateur {username} est Admin")
                return render_template('home.html', show_download=True, show_users=False)
            else:
                write_log(f"Utilisateur {username} n'a pas de droits spécifiques")
                return render_template('home.html', show_download=False, show_users=False)
        else:
            write_log("Aucun utilisateur connecté, redirection vers l'index")
            return redirect(url_for('index'))