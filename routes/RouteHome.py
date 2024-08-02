from flask import render_template, request, flash, session, redirect, url_for
from static.Controleur.ControleurLdap import ControleurLdap
from static.Controleur.ControleurConf import ControleurConf

def get_user_rights(username):
    ds = ControleurLdap()
    conf = ControleurConf()
    if ds.search_user(username):
        user_dn = f"(uid={username})"
        search_base = conf.get_config('LDAP', 'base_dn')
        user_entry = ds.search_entry(search_base, user_dn)
        rights_agreement = user_entry.get('rightsAgreement', [None])[0]
        ds.disconnect()
        return rights_agreement
    ds.disconnect()
    return None

def home(app):
    @app.route('/home')
    def inner_home():
        if 'username' in session:
            username = session['username']
            rights_agreement = get_user_rights(username)
            if rights_agreement == 'PlexService::SuperAdmin':
                return render_template('home.html', show_download=True, show_users=True)
            elif rights_agreement == 'PlexService::Admin':
                return render_template('home.html', show_download=True, show_users=False)
            else:
                return render_template('home.html', show_download=False, show_users=False)
        else:
            return redirect(url_for('index'))