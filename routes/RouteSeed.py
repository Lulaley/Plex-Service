from flask import render_template, request, session, jsonify, redirect, url_for, flash
from static.Controleur.ControleurLog import write_log
from static.Controleur.ControleurSeed import (
    start_seed, stop_seed, get_all_seeds, get_seed_stats,
    get_all_media_paths, find_torrent_file, restore_seeds
)
import threading
import uuid

# Créer un verrou pour synchroniser l'accès à la session
session_lock = threading.Lock()

def seed(app):
    @app.route('/seed')
    def inner_seed():
        with session_lock:
            if 'username' not in session:
                write_log("Aucun utilisateur connecté, redirection vers l'index")
                return redirect(url_for('index'))

            username = session.get('username')
            rights_agreement = session.get('rights_agreement')

            if rights_agreement != 'PlexService::SuperAdmin':
                write_log(f"Accès refusé pour l'utilisateur {username} avec droits {rights_agreement}, redirection vers /home", 'ERROR')
                session['from_index'] = False
                return redirect(url_for('home'))

            write_log(f"Affichage de la page de seeding pour l'utilisateur: {username}")
            session['from_index'] = False
            
            # Récupérer la liste des seeds actifs
            active_seeds = get_all_seeds()
            
            return render_template('seed.html', active_seeds=active_seeds)

def get_media_list(app):
    @app.route('/get_media_list', methods=['GET'])
    def inner_get_media_list():
        with session_lock:
            username = session.get('username')
            write_log(f"Récupération de la liste des médias pour {username}")
            
            try:
                media_paths = get_all_media_paths()
                return jsonify({'success': True, 'media_list': media_paths})
            except Exception as e:
                write_log(f"Erreur lors de la récupération de la liste des médias: {str(e)}", "ERROR")
                return jsonify({'success': False, 'message': str(e)}), 500

def start_seed_route(app):
    @app.route('/start_seed', methods=['POST'])
    def inner_start_seed():
        with session_lock:
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

def stop_seed_route(app):
    @app.route('/stop_seed', methods=['POST'])
    def inner_stop_seed():
        with session_lock:
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

def get_seeds_stats_route(app):
    @app.route('/get_seeds_stats', methods=['GET'])
    def inner_get_seeds_stats():
        try:
            seeds = get_all_seeds()
            return jsonify({'success': True, 'seeds': seeds})
        except Exception as e:
            write_log(f"Erreur lors de la récupération des stats: {str(e)}", "ERROR")
            return jsonify({'success': False, 'message': str(e)}), 500

def upload_torrent_for_seed(app):
    @app.route('/upload_torrent_for_seed', methods=['POST'])
    def inner_upload_torrent_for_seed():
        with session_lock:
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
                    filename = file.filename.replace(' ', '_')
                    file_path = f"/var/www/public/Plex-Service/tmp/{filename}"
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
