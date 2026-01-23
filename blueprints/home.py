from flask import Blueprint, render_template, session, redirect, url_for
from static.Controleur.ControleurLog import write_log

# Blueprint pour la page home
home_bp = Blueprint('home', __name__)

@home_bp.route('/home')
def home():
    if 'username' not in session:
        write_log("Aucun utilisateur connecté, redirection vers l'index")
        return redirect(url_for('auth.login'))
    
    # Si l'utilisateur vient de se connecter, vérifier ses droits
    if session.get('from_index'):
        write_log(f"Vérification des droits pour l'utilisateur: {session['username']}")
        from static.Controleur.ControleurLdap import ControleurLdap
        from static.Controleur.ControleurConf import ControleurConf
        ds = ControleurLdap()
        
        try:
            # Récupérer les droits depuis LDAP
            conf = ControleurConf()
            res = ds.search_user(session['username'])
            if res:
                user_dn = f"(uid={session['username']})"
                search_base = conf.get_config('LDAP', 'base_dn')
                user_entry = ds.search_entry(search_base, user_dn)
                
                if user_entry:
                    attributes = user_entry[0][1]
                    rights_agreement = attributes.get('rightsAgreement', [b''])[0].decode('utf-8')
                    write_log(f"Droits récupérés: {rights_agreement}")
                    session['rights_agreement'] = rights_agreement
                else:
                    write_log(f"Entrée utilisateur non trouvée", 'ERROR')
                    session['rights_agreement'] = None
            else:
                write_log(f"Utilisateur non trouvé dans LDAP", 'ERROR')
                session['rights_agreement'] = None
            
            session['from_index'] = False
        except Exception as e:
            write_log(f"Erreur lors de la récupération des droits: {str(e)}", 'ERROR')
            session['rights_agreement'] = None
        finally:
            ds.disconnect()
    
    write_log(f"Affichage de la page d'accueil pour l'utilisateur: {session['username']}")
    return render_template('home.html', username=session['username'])
