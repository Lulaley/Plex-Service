
from flask import Blueprint, render_template, request, session, jsonify, redirect, url_for, flash, Response, stream_with_context
download_bp = Blueprint('download', __name__)

from flask_login import login_required
from static.Controleur.ControleurDroits import superadmin_required
import shutil
from static.Controleur.ControleurConf import ControleurConf
from static.Controleur.ControleurLog import write_log
from static.Controleur.ControleurTorrent import download_torrent, stop_download, downloads, downloads_lock, get_all_downloads
from static.Controleur.ControleurSecurity import sanitize_filename, validate_path
import threading
import uuid
import os
import time

# Créer un verrou pour synchroniser l'accès à la session
session_lock = threading.Lock()

# Espace disque restant (API)
@download_bp.route('/api/disk_space')
@login_required
@superadmin_required
def api_disk_space():
    conf = ControleurConf()
    try:
        movies_path = conf.get_config('DLT', 'movies')
        series_path = conf.get_config('DLT', 'series')
        # Vérifier si les deux chemins sont sur le même disque
        def same_disk(path1, path2):
            import os
            if os.name == 'nt':
                return os.path.splitdrive(path1)[0].lower() == os.path.splitdrive(path2)[0].lower()
            else:
                return os.stat(path1).st_dev == os.stat(path2).st_dev
        same = same_disk(movies_path, series_path)
        movies_usage = shutil.disk_usage(movies_path)
        series_usage = shutil.disk_usage(series_path)
        if same:
            # Déterminer le dossier parent commun
            import os
            common_path = os.path.commonpath([movies_path, series_path])
            return {
                'success': True,
                'same_disk': True,
                'free': movies_usage.free,
                'total': movies_usage.total,
                'path': common_path
            }
        else:
            return {
                'success': True,
                'same_disk': False,
                'movies': {
                    'path': movies_path,
                    'free': movies_usage.free
                },
                'series': {
                    'path': series_path,
                    'free': series_usage.free
                }
            }
    except Exception as e:
        return {'success': False, 'error': str(e)}, 500

# Stocker les handles de téléchargement dans une variable globale
download_handles = {}

@download_bp.route('/download')
@login_required
@superadmin_required
def download_page():
    with session_lock:
        if 'username' not in session:
            write_log("Aucun utilisateur connecté, redirection vers l'index")
            return redirect(url_for('auth.login'))

        username = session.get('username')
        rights_agreement = session.get('rights_agreement')

        if rights_agreement != 'PlexService::SuperAdmin':
            write_log(f"Accès refusé pour l'utilisateur {username} avec droits {rights_agreement}, redirection vers /home", 'ERROR')
            session['from_index'] = False
            return redirect(url_for('home.home'))

        write_log(f"Affichage de la page de téléchargement pour l'utilisateur: {username}")
        session['from_index'] = False
        return render_template('download.html')

@download_bp.route('/upload', methods=['POST'])
@login_required
@superadmin_required
def upload_torrent():
    with session_lock:
        username = session.get('username')
        write_log(f"Affichage de la page d'upload pour l'utilisateur: {username}")
        
        if 'torrent-file' not in request.files:
            write_log(f"Aucun fichier sélectionné par {username}")
            return jsonify({'success': False, 'message': 'Aucun fichier sélectionné'}), 400
        
        file = request.files['torrent-file']
        if file.filename == '':
            write_log(f"Aucun fichier sélectionné par {username}")
            return jsonify({'success': False, 'message': 'Aucun fichier sélectionné'}), 400
        
        if file and file.filename.endswith('.torrent'):
            # Sécuriser le nom de fichier
            filename = sanitize_filename(file.filename.replace(' ', '_'))
            
            # Vérifier que le fichier a toujours l'extension .torrent après nettoyage
            if not filename.endswith('.torrent'):
                write_log(f"Nom de fichier suspect rejeté: {file.filename}", "ERROR")
                return jsonify({'success': False, 'message': 'Nom de fichier invalide'}), 400
            
            tmp_dir = "/var/www/public/Plex-Service/tmp/"
            file_path = os.path.join(tmp_dir, filename)
            
            # Valider que le chemin final est bien dans tmp/
            if not validate_path(file_path, [tmp_dir]):
                write_log(f"Tentative d'accès à un chemin non autorisé: {file_path}", "ERROR")
                return jsonify({'success': False, 'message': 'Chemin non autorisé'}), 403
            
            file.save(file_path)
            write_log(f"Fichier .torrent déposé par {username} : {file_path}")
            
            # Générer un ID unique pour ce téléchargement
            download_id = str(uuid.uuid4())
            
            return jsonify({
                'success': True,
                'message': 'Fichier téléchargé avec succès',
                'redirect_url': url_for('download.start_download_route', torrent_file_path=file_path, download_id=download_id),
                'download_id': download_id
            })

        else:
            write_log(f"Format de fichier non supporté par {username}")
            return jsonify({'success': False, 'message': 'Format de fichier non supporté'}), 400

def background_download(torrent_file_path, save_path, handle, username):
    """Fonction qui tourne en arrière-plan pour gérer le téléchargement."""
    download_id = handle.get('id')
    try:
        write_log(f"Thread de téléchargement démarré pour {username} (download_id: {download_id})")
        for status in download_torrent(torrent_file_path, save_path, handle):
            # Extraire le message de status
            if status.startswith('data: '):
                message = status[6:].strip()
                handle['progress_message'] = message
                
                # Si c'est le message final
                if message in ['done', 'cancelled', 'not enough space', 'error']:
                    handle['final_message'] = message
                    handle['is_downloading'] = False
                    handle['finished_at'] = time.time()
                    break
        
        write_log(f"Thread de téléchargement terminé pour {username} (download_id: {download_id})")
        
        # Cleanup automatique après 10 minutes
        time.sleep(600)
        with downloads_lock:
            if download_id in downloads:
                write_log(f"Nettoyage automatique du download {download_id}")
                del downloads[download_id]
                
    except Exception as e:
        write_log(f"Erreur dans le thread de téléchargement: {str(e)}", "ERROR")
        handle['is_downloading'] = False
        handle['final_message'] = 'error'
        handle['finished_at'] = time.time()

@download_bp.route('/start_download')
def start_download_route():
    try:
        username = session.get('username')
        torrent_file_path = request.args.get('torrent_file_path')
        save_path = request.args.get('save_path')
        download_id = request.args.get('download_id')  # Récupérer l'ID depuis l'URL
        
        if not download_id:
            download_id = str(uuid.uuid4())  # Générer un ID si manquant
        
        write_log(f"Démarrage du téléchargement avec ID: {download_id}")
        
        # Créer le handle avant de lancer le thread
        handle = {
            'id': download_id,
            'is_downloading': True,
            'is_active': True,
            'handle': None,
            'save_path': save_path,
            'torrent_file_path': torrent_file_path,
            'downloaded_files': [],
            'username': username,
            'name': 'Unknown',
            'finished_at': None
        }
        with downloads_lock:
            downloads[download_id] = handle
        
        # Lancer le téléchargement dans un thread séparé
        download_thread = threading.Thread(
            target=background_download,
            args=(torrent_file_path, save_path, handle, username),
            daemon=True
        )
        download_thread.start()
        
        # Retourner un flux de statut
        @stream_with_context
        def generate():
            write_log(f"Client connecté au stream de téléchargement {download_id}")
            last_progress = -1
            
            while downloads.get(download_id, {}).get('is_downloading', False):
                handle_data = downloads.get(download_id)
                if not handle_data:
                    break
                
                if 'progress_message' in handle_data:
                    msg = handle_data['progress_message']
                    if msg != last_progress:
                        yield f"data: {msg}\n\n"
                        last_progress = msg
                
                time.sleep(1)
            
            # Envoyer le message final
            handle_data = downloads.get(download_id)
            if handle_data and 'final_message' in handle_data:
                yield f"data: {handle_data['final_message']}\n\n"
            else:
                yield "data: done\n\n"
            
            write_log(f"Client déconnecté du stream {download_id}")
        
        return Response(generate(), mimetype='text/event-stream')
    except Exception as e:
        write_log(f"Erreur lors du démarrage du téléchargement: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@download_bp.route('/stop_download', methods=['POST'])
def stop_download_route():
    from static.Controleur.ControleurTorrent import load_persisted_downloads, save_persisted_downloads
    write_log("Requête d'annulation de téléchargement reçue")
    data = request.get_json()
    download_id = data.get('download_id')  # Récupérer l'identifiant du téléchargement
    
    write_log(f"Tentative d'annulation pour download_id: {download_id}")
    write_log(f"Downloads actifs dans ce worker: {list(downloads.keys())}")
    
    # Vérifier d'abord dans le worker actuel
    with downloads_lock:
        handle = downloads.get(download_id)
    
    if handle:
        username = handle.get('username', 'unknown')
        write_log(f"Annulation du téléchargement pour l'utilisateur: {username} (trouvé dans ce worker)")
        if stop_download(handle):
            write_log("Téléchargement annulé avec succès")
            return jsonify(success=True)
        else:
            write_log("Erreur lors de l'annulation du téléchargement")
            return jsonify(success=False)
    
    # Si pas trouvé dans ce worker, marquer comme annulé dans le fichier de persistance
    write_log(f"Download non trouvé dans ce worker, marquage dans le fichier de persistance")
    try:
        persisted_downloads = load_persisted_downloads()
        if download_id in persisted_downloads:
            persisted_downloads[download_id]['is_active'] = False
            # Sauvegarder manuellement dans le fichier
            import json
            import os
            DOWNLOADS_PERSISTENCE_FILE = "/var/www/public/Plex-Service/tmp/active_downloads.json"
            os.makedirs(os.path.dirname(DOWNLOADS_PERSISTENCE_FILE), exist_ok=True)
            with open(DOWNLOADS_PERSISTENCE_FILE, 'w') as f:
                json.dump(persisted_downloads, f, indent=4)
            write_log(f"Download {download_id} marqué comme inactif dans la persistance")
            return jsonify(success=True)
        else:
            write_log(f"Aucun téléchargement trouvé pour l'identifiant {download_id}")
            return jsonify(success=False, message="Téléchargement introuvable")
    except Exception as e:
        write_log(f"Erreur lors de la mise à jour de la persistance: {str(e)}", "ERROR")
        return jsonify(success=False, message=str(e))

@download_bp.route('/stream_download/<download_id>')
def stream_download(download_id):
    """Stream les mises à jour d'un téléchargement existant."""
    write_log(f"Client se connecte au stream du download {download_id}")
    
    @stream_with_context
    def generate():
        write_log(f"Génération du stream pour {download_id}")
        last_progress = -1
        
        # Vérifier si le download existe (soit en mémoire, soit dans la persistance)
        from static.Controleur.ControleurTorrent import load_persisted_downloads
        
        while True:
            # Vérifier dans le worker actuel
            handle_data = downloads.get(download_id)
            
            # Si pas trouvé localement, vérifier dans la persistance
            if not handle_data:
                persisted = load_persisted_downloads()
                if download_id not in persisted:
                    write_log(f"Download {download_id} non trouvé")
                    yield "data: not_found\n\n"
                    break
                
                # Utiliser les données de la persistance
                persisted_data = persisted[download_id]
                if not persisted_data.get('is_active', True):
                    write_log(f"Download {download_id} n'est plus actif")
                    yield "data: done\n\n"
                    break
                
                # Construire un message à partir des stats persistées
                stats = persisted_data.get('stats', {})
                progress = stats.get('progress', 0)
                download_rate = stats.get('download_rate', 0)
                upload_rate = stats.get('upload_rate', 0)
                peers = stats.get('peers', 0)
                state = stats.get('state', 'downloading')
                
                msg = f"{progress:.2f}% complete (down: {download_rate:.1f} kB/s up: {upload_rate:.1f} kB/s peers: {peers}) {state}"
                if msg != last_progress:
                    yield f"data: {msg}\n\n"
                    last_progress = msg
            else:
                # Données du worker actuel
                if not handle_data.get('is_downloading', False):
                    final_msg = handle_data.get('final_message', 'done')
                    yield f"data: {final_msg}\n\n"
                    break
                
                if 'progress_message' in handle_data:
                    msg = handle_data['progress_message']
                    if msg != last_progress:
                        yield f"data: {msg}\n\n"
                        last_progress = msg
            
            time.sleep(1)
        
        write_log(f"Stream terminé pour {download_id}")
    
    return Response(generate(), mimetype='text/event-stream')

@download_bp.route('/get_downloads', methods=['GET'])
def get_downloads():
    """Retourne la liste de tous les downloads actifs."""
    try:
        downloads_list = get_all_downloads()
        return jsonify({'success': True, 'downloads': downloads_list})
    except Exception as e:
        write_log(f"Erreur lors de la récupération des downloads: {str(e)}", "ERROR")
        return jsonify({'success': False, 'message': str(e)}), 500

def restore_downloads_on_startup():
    """Restaure et relance automatiquement les téléchargements interrompus au démarrage."""
    
    # Utiliser un verrou atomique pour éviter que plusieurs workers restaurent en même temps
    RESTORE_LOCK_FILE = "/var/www/public/Plex-Service/tmp/downloads_restore.lock"
    
    try:
        # Créer le fichier de verrou de manière atomique (échoue si existe déjà)
        fd = os.open(RESTORE_LOCK_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        os.write(fd, f"{os.getpid()}\n".encode())
        os.close(fd)
        
        write_log("Vérification des téléchargements interrompus au démarrage (verrou acquis)")
        
        try:
            from static.Controleur.ControleurTorrent import load_persisted_downloads
            import json
            DOWNLOADS_PERSISTENCE_FILE = "/var/www/public/Plex-Service/tmp/active_downloads.json"
            
            persisted = load_persisted_downloads()
            
            if not persisted:
                write_log("Aucun téléchargement à restaurer")
                return
            
            write_log(f"Trouvé {len(persisted)} téléchargement(s) à vérifier")
            
            # Compter combien de downloads on va réellement relancer
            downloads_to_restore = []
            
            # Vérifier chaque download
            for download_id, download_info in list(persisted.items()):
                # Vérifier si le téléchargement est terminé (100%)
                stats = download_info.get('stats', {})
                progress = stats.get('progress', 0)
                
                if progress >= 100:
                    write_log(f"Download {download_id} déjà terminé (100%), nettoyage")
                    persisted[download_id]['is_active'] = False
                    with open(DOWNLOADS_PERSISTENCE_FILE, 'w') as f:
                        json.dump(persisted, f, indent=4)
                    continue
                
                # Si inactif mais pas terminé, vérifier si on peut le reprendre
                if not download_info.get('is_active', True):
                    write_log(f"Download {download_id} marqué comme inactif mais incomplet ({progress:.1f}%)")
                    # Vérifier si resume_data existe
                    resume_file = f"/var/www/public/Plex-Service/tmp/resume_data/{download_id}.resume"
                    if os.path.exists(resume_file):
                        write_log(f"Resume data trouvé pour {download_id}, tentative de relance")
                        # Continuer pour relancer
                    else:
                        write_log(f"Pas de resume_data pour {download_id}, ignoré", "WARNING")
                        continue
                
                # Récupérer les informations
                torrent_path = download_info.get('torrent_path', '')
                save_path = download_info.get('save_path', '')
                
                # Vérifier que le fichier torrent existe toujours
                if not os.path.exists(torrent_path):
                    write_log(f"Fichier torrent {torrent_path} introuvable, téléchargement {download_id} ignoré", "WARNING")
                    continue
                
                # Ajouter à la liste
                downloads_to_restore.append({
                    'id': download_id,
                    'name': download_info.get('name', 'Unknown'),
                    'torrent_path': torrent_path,
                    'save_path': save_path,
                    'progress': progress
                })
            
            # Ne restaurer QUE si on a trouvé des downloads à restaurer
            if not downloads_to_restore:
                write_log("Aucun téléchargement à restaurer après vérification")
                return
            
            write_log(f"Relance de {len(downloads_to_restore)} téléchargement(s)")
            
            # Relancer chaque download
            for dl_info in downloads_to_restore:
                download_id = dl_info['id']
                
                # Vérifier que ce download n'est pas déjà en cours dans ce worker
                with downloads_lock:
                    if download_id in downloads and downloads[download_id].get('is_downloading', False):
                        write_log(f"Téléchargement {download_id} déjà en cours dans ce worker, skip")
                        continue
                
                write_log(f"Relance du téléchargement {download_id} ({dl_info['name']}) - {dl_info['progress']:.1f}% complété")
                
                # Créer un handle et relancer le téléchargement dans un thread
                handle = {
                    'id': download_id,
                    'is_downloading': True,
                    'is_active': True,
                    'handle': None,
                    'save_path': dl_info['save_path'],
                    'torrent_file_path': dl_info['torrent_path'],
                    'downloaded_files': [],
                    'username': 'system',  # Utilisateur système pour restauration
                    'name': dl_info['name']
                }
                
                with downloads_lock:
                    downloads[download_id] = handle
                
                # Lancer dans un thread
                download_thread = threading.Thread(
                    target=background_download,
                    args=(dl_info['torrent_path'], dl_info['save_path'], handle, 'system'),
                    daemon=True
                )
                download_thread.start()
                
                write_log(f"Téléchargement {download_id} relancé avec succès")
            
            write_log("Restauration des téléchargements terminée")
            
            # Garder le verrou pendant 2 secondes pour éviter que d'autres workers restaurent
            time.sleep(2)
            
        finally:
            # Libérer le verrou en supprimant le fichier
            if os.path.exists(RESTORE_LOCK_FILE):
                try:
                    os.remove(RESTORE_LOCK_FILE)
                    write_log("Verrou de restauration libéré")
                except OSError as e:
                    write_log(f"Erreur lors de la suppression du verrou: {e}", "WARNING")
                
    except FileExistsError:
        # Un autre worker est déjà en train de restaurer (le fichier existe déjà)
        write_log("Un autre worker restaure déjà les téléchargements, skip")
        return
    except Exception as e:
        write_log(f"Erreur lors de la restauration des téléchargements: {str(e)}", "ERROR")
        # Libérer le verrou en cas d'erreur
        if os.path.exists(RESTORE_LOCK_FILE):
            try:
                os.remove(RESTORE_LOCK_FILE)
            except OSError as e:
                write_log(f"Erreur lors de la libération du verrou: {e}", "WARNING")
