from flask_login import login_user, logout_user, login_required, current_user
from static.Controleur.ControleurUser import User
from flask import Blueprint, render_template, request, flash, session, redirect, url_for
from static.Controleur.ControleurLdap import ControleurLdap
from static.Controleur.ControleurConf import ControleurConf
from static.Controleur.ControleurLog import write_log
from datetime import timedelta
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Blueprint pour l'authentification
auth_bp = Blueprint('auth', __name__)

# Le limiter sera injecté depuis app.py
limiter = None

def init_limiter(app_limiter):
    """Initialise le limiter depuis app.py"""
    global limiter
    limiter = app_limiter

@auth_bp.route('/index', methods=['GET', 'POST'])
def login():
    # Rate limiting pour login : max 5 tentatives par minute
    # Désactive le blocage pour localhost
    if limiter and request.method == 'POST':
        ip = get_remote_address()
        if ip != '127.0.0.1':
            try:
                limiter.check()
            except Exception:
                write_log(f"Rate limit dépassé pour IP: {ip}", "WARNING")
                flash('Trop de tentatives de connexion. Réessayez dans 1 minute.', 'error')
                return render_template('index.html'), 429
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember_me = 'remember_me' in request.form

        write_log(f"Tentative de connexion pour l'utilisateur: {username}")

        conf = ControleurConf()
        base_dn = conf.get_config('LDAP', 'base_dn')
        ds = ControleurLdap()
        if ds.authenticate_user(username, password):
            # Récupérer les droits de l'utilisateur depuis LDAP (ou logique existante)
            user_info = ds.search_user(username)
            rights = user_info.get('rights', 'PlexService::User') if user_info else 'PlexService::User'
            write_log(f"Connexion réussie pour l'utilisateur: {username} (droits: {rights})")
            # Log debug pour vérifier le droit exact
            write_log(f"DEBUG DROIT: username={username}, rights={rights}")
            user = User(username, rights)
            login_user(user, remember=remember_me)
            if remember_me:
                from flask import current_app
                current_app.permanent_session_lifetime = timedelta(days=7)
            session['from_index'] = True
            ds.disconnect()
            return redirect(url_for('home.home'))
        else:
            write_log(f"Échec de la connexion pour l'utilisateur: {username}", 'ERROR')
            flash("Échec de la connexion. Veuillez vérifier vos identifiants et réessayer.", 'error')
        ds.disconnect()
    else:
        write_log("Affichage du formulaire de connexion")
    # Rendu du formulaire de connexion
    return render_template('index.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    from passlib.hash import ldap_salted_sha1
    import re
    
    def is_hashed(password):
        hash_patterns = [
            r'^\{SHA\}', r'^\{SSHA\}', r'^\{MD5\}', r'^\{CRYPT\}', r'^\{SMD5\}'
        ]
        return any(re.match(pattern, password) for pattern in hash_patterns)
    
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
        
        if '  ' in username:
            write_log(f"Nom d'utilisateur invalide (espaces multiples): {username}", 'ERROR')
            flash('Le nom d\'utilisateur ne peut pas contenir plusieurs espaces consécutifs')
            return redirect(url_for('auth.login'))
        
        if not re.match(r'^[a-zA-Z0-9 _.-]+$', username):
            write_log(f"Nom d'utilisateur invalide (caractères non autorisés): {username}", 'ERROR')
            flash('Le nom d\'utilisateur ne peut contenir que des lettres, chiffres, espaces, tirets et underscores')
            return redirect(url_for('auth.login'))
        
        if not is_hashed(password):
            hashed_password = ldap_salted_sha1.hash(password)
        else:
            hashed_password = password

        ds = ControleurLdap()
        
        if ds.user_exists(username):
            write_log(f"Nom d'utilisateur déjà existant: {username}", 'ERROR')
            flash('Ce nom d\'utilisateur existe déjà')
            ds.disconnect()
            return redirect(url_for('auth.login'))

        if ds.add_user(username, hashed_password, email):
            write_log(f"Inscription réussie pour l'utilisateur: {username}")
            flash('Inscription réussie ! Vous pouvez maintenant vous connecter.')
        else:
            write_log(f"Échec de l'inscription pour l'utilisateur: {username}", 'ERROR')
            flash('Échec de l\'inscription. Veuillez réessayer.')
        
        ds.disconnect()
        return redirect(url_for('auth.login'))

@auth_bp.route('/logout')
def logout():
    username = session.get('username', 'Utilisateur inconnu')
    write_log(f"Déconnexion de l'utilisateur: {username}")
    session.clear()
    return redirect(url_for('auth.login'))
