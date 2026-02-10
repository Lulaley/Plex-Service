from flask_login import login_required, current_user
from static.Controleur.ControleurDroits import admin_required
from flask import Blueprint, request, jsonify, render_template, session, redirect, url_for
from static.Controleur.ControleurWish import ControleurWish
from static.Controleur.ControleurLog import write_log
from static.Controleur.ControleurTMDB import ControleurTMDB
from datetime import datetime

# Blueprint pour les demandes (wishes)
wishes_bp = Blueprint('wishes', __name__)

# Le limiter sera injecté depuis app.py
limiter = None

def init_limiter(app_limiter):
    """Initialise le limiter depuis app.py"""
    global limiter
    limiter = app_limiter

def extract_uid_from_dn(dn):
    # Assuming the DN is in the format "uid=<username>,..."
    parts = dn.split(',')
    for part in parts:
        if part.startswith('uid='):
            return part.split('=')[1]
    return dn

def format_date(date_str):
    # Convert the date string to a datetime object
    date_obj = datetime.strptime(date_str, '%Y%m%d%H%M%SZ')
    # Format the datetime object to the desired format
    return date_obj.strftime('%d-%m-%Y')

@wishes_bp.route('/demande', methods=['GET'])
@login_required
def manage_wishes():
    if 'username' not in session:
        write_log("Aucun utilisateur connecté, redirection vers l'index")
        return redirect(url_for('auth.login'))

    username = session.get('username')
    rights_agreement = session.get('rights_agreement')
    write_log(f"Affichage des demandes pour l'utilisateur: {username} avec les droits: {rights_agreement}")

    if rights_agreement not in ['PlexService::User', 'PlexService::Admin', 'PlexService::SuperAdmin']:
        write_log(f"Utilisateur {username} n'a pas les droits nécessaires pour accéder à cette page", 'ERROR')
        return redirect(url_for('auth.login'))

    # Récupérer paramètres de pagination
    page = request.args.get('page', 1, type=int)
    per_page = 10  # 10 wishes par page (avec images, on limite)
    
    return list_wishes(username, rights_agreement, page, per_page)

@wishes_bp.route('/create_wish', methods=['POST'])
@login_required
def create_wish():
    # Rate limiting : max 10 créations de demandes par minute
    if limiter:
        try:
            limiter.check()
        except Exception:
            write_log(f"Rate limit dépassé pour create_wish", "WARNING")
            return jsonify({'success': False, 'message': 'Trop de requêtes. Réessayez dans 1 minute.'}), 429
    
    if 'username' not in session:
        return jsonify({'success': False, 'message': 'Utilisateur non connecté'})

    data = request.get_json()
    title = data.get('title')
    wish_type = data.get('type')
    username = session.get('username')

    wish_controller = ControleurWish()
    success = wish_controller.create_wish(username, title, wish_type)

    return jsonify({'success': success})

@wishes_bp.route('/wish_details/<wish_id>', methods=['GET'])
@login_required
def wish_details(wish_id):
    """Récupère les détails d'une wish avec cache TMDB (TTL 24h)."""
    if 'username' not in session:
        return jsonify({'success': False, 'message': 'Utilisateur non connecté'})

    wish_controller = ControleurWish()
    wish = wish_controller.get_wish_by_id(wish_id)

    if not wish:
        return jsonify({'success': False, 'message': 'Demande non trouvée'})

    # Cache TMDB pour éviter appels répétés à l'API
    from static.Controleur.ControleurCache import cache
    cache_key = f"tmdb:{wish['wishType']}:{wish['plexTitle']}"
    
    # 1. Chercher dans cache Redis (TTL 24h)
    details = cache.get(cache_key)
    
    if not details:
        # 2. CACHE MISS : appel TMDB
        tmdb = ControleurTMDB()
        if wish['wishType'] == 'movie':
            details = tmdb.search_movie(wish['plexTitle'])
        elif wish['wishType'] == 'series':
            details = tmdb.search_serie(wish['plexTitle'])
        
        # 3. Sauver dans cache pour 24h
        if details:
            cache.set(cache_key, details, timeout=86400)

    if not details:
        details = {}

    details['status'] = wish['status']
    details['wishId'] = wish['wishId']
    details['requestDate'] = format_date(wish['requestDate'])
    details['wishOwner'] = extract_uid_from_dn(wish['wishOwner'])

    return jsonify(details)

@wishes_bp.route('/validate_wish/<wish_id>', methods=['POST'])
@login_required
@admin_required
def validate_wish(wish_id):
    # Rate limiting : max 30 validations par minute
    if limiter:
        try:
            limiter.check()
        except Exception:
            write_log(f"Rate limit dépassé pour validate_wish", "WARNING")
            return jsonify({'success': False, 'message': 'Trop de requêtes. Réessayez dans 1 minute.'}), 429
    
    if 'username' not in session:
        return jsonify({'success': False, 'message': 'Utilisateur non connecté'})

    rights_agreement = session.get('rights_agreement')
    if rights_agreement not in ['PlexService::Admin', 'PlexService::SuperAdmin']:
        return jsonify({'success': False, 'message': 'Droits insuffisants'})

    wish_controller = ControleurWish()
    wish = wish_controller.get_wish_by_id(wish_id)

    if not wish:
        return jsonify({'success': False, 'message': 'Demande non trouvée'})

    success = wish_controller.validate_wish(extract_uid_from_dn(wish['wishOwner']), wish_id)

    return jsonify({'success': success})

def list_wishes(username, rights_agreement, page=1, per_page=10):
    """Liste les wishes avec pagination"""
    wish_controller = ControleurWish()
    if rights_agreement in ['PlexService::Admin', 'PlexService::SuperAdmin']:
        all_wishes = wish_controller.get_all_wishes()
    else:
        all_wishes = wish_controller.get_user_wishes(username)

    # Calculer pagination
    total_wishes = len(all_wishes)
    total_pages = (total_wishes + per_page - 1) // per_page
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    
    paginated_wishes = all_wishes[start_idx:end_idx]
    
    tmdb = ControleurTMDB()
    wish_details = []
    for wish in paginated_wishes:
        if wish['wishType'] == 'movie':
            details = tmdb.search_movie(wish['plexTitle'])
        elif wish['wishType'] == 'series':
            details = tmdb.search_serie(wish['plexTitle'])
        details['status'] = wish['status']
        details['wishId'] = wish['wishId']
        details['poster_path'] = details.get('poster_path', '')
        details['title'] = details.get('title', wish['plexTitle'])
        details['requestDate'] = format_date(wish['requestDate'])
        details['wishOwner'] = extract_uid_from_dn(wish['wishOwner'])
        wish_details.append(details)
    
    session['from_index'] = False
    write_log(f"Liste des demandes récupérée: page {page}/{total_pages}, {len(wish_details)} wishes")
    
    return render_template('wishes.html', 
                         wishes=wish_details,
                         current_page=page,
                         total_pages=total_pages,
                         total_wishes=total_wishes)
