from flask_login import login_required
from static.Controleur.ControleurDroits import superadmin_required
from flask import Blueprint, render_template, request, session, jsonify, redirect, url_for, flash
from static.Controleur.ControleurLog import write_log
from static.Controleur.ControleurSeed import (
    start_seed, stop_seed, get_all_seeds, get_seed_stats,
    get_all_media_paths, find_torrent_file, restore_seeds
)
from static.Controleur.ControleurSecurity import sanitize_filename, validate_path
import threading
import uuid

seed_bp = Blueprint('seed', __name__)

# Le limiter sera injecté depuis app.py
limiter = None

def init_limiter(app_limiter):
    """Initialise le limiter depuis app.py"""
    global limiter
    limiter = app_limiter

@seed_bp.route('/seed')
@login_required
@superadmin_required
def seed_page():
    if 'username' not in session:
        write_log("Aucun utilisateur connecté, redirection vers l'index")
        return redirect(url_for('auth.login'))

    username = session.get('username')
    rights_agreement = session.get('rights_agreement')

    if rights_agreement != 'PlexService::SuperAdmin':
        write_log(f"Accès refusé pour l'utilisateur {username} avec droits {rights_agreement}, redirection vers /home", 'ERROR')
        session['from_index'] = False
        return redirect(url_for('home.home'))

    write_log(f"Affichage de la page de seeding pour l'utilisateur: {username}")
    session['from_index'] = False
    
    # Récupérer la liste des seeds actifs
    active_seeds = get_all_seeds()
    
    return render_template('seed.html', active_seeds=active_seeds)

@seed_bp.route('/get_media_list', methods=['GET'])
@login_required
@superadmin_required
def get_media_list():
    username = session.get('username')
    write_log(f"Récupération de la liste des médias pour {username}")
    
    try:
        media_paths = get_all_media_paths()
        return jsonify({'success': True, 'media_list': media_paths})
    except Exception as e:
        write_log(f"Erreur lors de la récupération de la liste des médias: {str(e)}", "ERROR")
        return jsonify({'success': False, 'message': str(e)}), 500

@seed_bp.route('/start_seed', methods=['POST'])
@login_required
@superadmin_required
def start_seed_route():
    username = session.get('username')
    write_log(f"Requête de démarrage de seed pour {username}")
    
    try:
        data = request.get_json()
        data_path = data.get('data_path')
        torrent_file_path = data.get('torrent_file_path')
        
        if not data_path:
            return jsonify({'success': False, 'message': 'Chemin des données manquant'}), 400
        
        # Si pas de fichier torrent fourni, essayer de le trouver
        if not torrent_file_path:
            torrent_file_path = find_torrent_file(data_path)
            if not torrent_file_path:
                return jsonify({'success': False, 'message': 'Aucun fichier .torrent trouvé'}), 400
        
        # Générer un ID unique pour le seed
        seed_id = str(uuid.uuid4())
        
        # Démarrer le seed
        if start_seed(seed_id, torrent_file_path, data_path):
            write_log(f"Seed {seed_id} démarré avec succès pour {username}")
            return jsonify({'success': True, 'seed_id': seed_id, 'message': 'Seed démarré avec succès'})
        else:
            return jsonify({'success': False, 'message': 'Erreur lors du démarrage du seed'}), 500
    except Exception as e:
        write_log(f"Erreur lors du démarrage du seed pour {username}: {str(e)}", "ERROR")
        return jsonify({'success': False, 'message': str(e)}), 500

@seed_bp.route('/stop_seed', methods=['POST'])
@login_required
@superadmin_required
def stop_seed_route():
    username = session.get('username')
    write_log(f"Requête d'arrêt de seed pour {username}")
    
    try:
        data = request.get_json()
        seed_id = data.get('seed_id')
        
        if not seed_id:
            return jsonify({'success': False, 'message': 'ID du seed manquant'}), 400
        
        if stop_seed(seed_id):
            write_log(f"Seed {seed_id} arrêté avec succès pour {username}")
            return jsonify({'success': True, 'message': 'Seed arrêté avec succès'})
        else:
            return jsonify({'success': False, 'message': 'Erreur lors de l\'arrêt du seed'}), 500
    except Exception as e:
        write_log(f"Erreur lors de l'arrêt du seed pour {username}: {str(e)}", "ERROR")
        return jsonify({'success': False, 'message': str(e)}), 500

@seed_bp.route('/get_seeds_stats', methods=['GET'])
def get_seeds_stats():
    try:
        seeds = get_all_seeds()
        return jsonify({'success': True, 'seeds': seeds})
    except Exception as e:
        write_log(f"Erreur lors de la récupération des stats: {str(e)}", "ERROR")
        return jsonify({'success': False, 'message': str(e)}), 500

@seed_bp.route('/upload_torrent_for_seed', methods=['POST'])
def upload_torrent():
    username = session.get('username')
    write_log(f"Upload de fichier .torrent pour seed par {username}")
    
    try:
        if 'torrent-file' not in request.files:
            return jsonify({'success': False, 'message': 'Aucun fichier sélectionné'}), 400
        
        file = request.files['torrent-file']
        data_path = request.form.get('data_path')
        
        if file.filename == '':
            return jsonify({'success': False, 'message': 'Aucun fichier sélectionné'}), 400
        
        if not data_path:
            return jsonify({'success': False, 'message': 'Chemin des données manquant'}), 400
        
        if file and file.filename.endswith('.torrent'):
            # Sécuriser le nom de fichier
            filename = sanitize_filename(file.filename.replace(' ', '_'))
            
            # Vérifier l'extension après nettoyage
            if not filename.endswith('.torrent'):
                write_log(f"Nom de fichier suspect rejeté: {file.filename}", "ERROR")
                return jsonify({'success': False, 'message': 'Nom de fichier invalide'}), 400
            
            tmp_dir = "/var/www/public/Plex-Service/tmp/"
            file_path = f"{tmp_dir}{filename}"
            
            # Valider le chemin
            if not validate_path(file_path, [tmp_dir]):
                write_log(f"Tentative d'accès à un chemin non autorisé: {file_path}", "ERROR")
                return jsonify({'success': False, 'message': 'Chemin non autorisé'}), 403
            
            file.save(file_path)
            write_log(f"Fichier .torrent uploadé: {file_path}")
            
            # Générer un ID unique pour le seed
            seed_id = str(uuid.uuid4())
            
            # Démarrer le seed
            if start_seed(seed_id, file_path, data_path):
                return jsonify({
                    'success': True,
                    'seed_id': seed_id,
                    'torrent_file_path': file_path,
                    'message': 'Seed démarré avec succès'
                })
            else:
                return jsonify({'success': False, 'message': 'Erreur lors du démarrage du seed'}), 500
        else:
            return jsonify({'success': False, 'message': 'Format de fichier non supporté'}), 400
    except Exception as e:
        write_log(f"Erreur lors de l'upload du torrent: {str(e)}", "ERROR")
        return jsonify({'success': False, 'message': str(e)}), 500

def restore_seeds_on_startup():
    """Fonction pour restaurer les seeds au démarrage de l'application."""
    write_log("Restauration des seeds au démarrage de l'application")
    try:
        restore_seeds()
    except Exception as e:
        write_log(f"Erreur lors de la restauration des seeds: {str(e)}", "ERROR")
