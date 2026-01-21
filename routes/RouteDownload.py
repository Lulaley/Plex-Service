from flask import render_template, request, session, jsonify, redirect, url_for, flash, Response, stream_with_context
from static.Controleur.ControleurLog import write_log
from static.Controleur.ControleurTorrent import download_torrent, stop_download, downloads, downloads_lock, get_all_downloads
import threading
import uuid
import os
import time

# Créer un verrou pour synchroniser l'accès à la session
session_lock = threading.Lock()

# Stocker les handles de téléchargement dans une variable globale
download_handles = {}

def download(app):
    @app.route('/download')
    def inner_download():
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

            write_log(f"Affichage de la page de téléchargement pour l'utilisateur: {username}")
            session['from_index'] = False
            return render_template('download.html')

def upload(app):
    @app.route('/upload', methods=['POST'])
    def inner_upload():
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
                filename = file.filename.replace(' ', '_')
                file_path = os.path.join("/var/www/public/Plex-Service/tmp/", filename)
                file.save(file_path)
                write_log(f"Fichier .torrent déposé par {username} : {file_path}")
                
                # Générer un ID unique pour ce téléchargement
                download_id = str(uuid.uuid4())
                
                return jsonify({
                    'success': True,
                    'message': 'Fichier téléchargé avec succès',
                    'redirect_url': url_for('inner_start_download', torrent_file_path=file_path, download_id=download_id),
                    'download_id': download_id
                })

            else:
                write_log(f"Format de fichier non supporté par {username}")
                return jsonify({'success': False, 'message': 'Format de fichier non supporté'}), 400

def background_download(torrent_file_path, save_path, handle, username):
    """Fonction qui tourne en arrière-plan pour gérer le téléchargement."""
    try:
        write_log(f"Thread de téléchargement démarré pour {username} (download_id: {handle.get('id')})")
        for status in download_torrent(torrent_file_path, save_path, handle):
            # Extraire le message de status
            if status.startswith('data: '):
                message = status[6:].strip()
                handle['progress_message'] = message
                
                # Si c'est le message final
                if message in ['done', 'cancelled', 'not enough space', 'error']:
                    handle['final_message'] = message
                    handle['is_downloading'] = False
                    break
        
        write_log(f"Thread de téléchargement terminé pour {username} (download_id: {handle.get('id')})")
    except Exception as e:
        write_log(f"Erreur dans le thread de téléchargement: {str(e)}", "ERROR")
        handle['is_downloading'] = False
        handle['final_message'] = 'error'

def start_download(app):
    @app.route('/start_download')
    def inner_start_download():
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
                'name': 'Unknown'
            }
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

def stop_download_route(app):
    @app.route('/stop_download', methods=['POST'])
    def inner_stop_download():
        from static.Controleur.ControleurTorrent import load_persisted_downloads, save_persisted_downloads
        write_log("Requête d'annulation de téléchargement reçue")
        data = request.get_json()
        download_id = data.get('download_id')  # Récupérer l'identifiant du téléchargement
        
        write_log(f"Tentative d'annulation pour download_id: {download_id}")
        write_log(f"Downloads actifs dans ce worker: {list(downloads.keys())}")
        
        # Vérifier d'abord dans le worker actuel
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

def get_downloads_route(app):
    @app.route('/get_downloads', methods=['GET'])
    def inner_get_downloads():
        """Retourne la liste de tous les downloads actifs."""
        try:
            downloads_list = get_all_downloads()
            return jsonify({'success': True, 'downloads': downloads_list})
        except Exception as e:
            write_log(f"Erreur lors de la récupération des downloads: {str(e)}", "ERROR")
            return jsonify({'success': False, 'message': str(e)}), 500