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
        ds = ControleurLdap()
        
        try:
            rights = ds.get_user_rights(session['username'])
            write_log(f"Droits récupérés: {rights}")
            session['rights_agreement'] = rights
            session['from_index'] = False
        except Exception as e:
            write_log(f"Erreur lors de la récupération des droits: {str(e)}", 'ERROR')
            session['rights_agreement'] = None
        finally:
            ds.disconnect()
    
    write_log(f"Affichage de la page d'accueil pour l'utilisateur: {session['username']}")
    return render_template('home.html', username=session['username'])
