from flask import render_template, request, session, jsonify, redirect, url_for, flash, Response, stream_with_context
import threading
from static.Controleur.ControleurLog import write_log
from static.Controleur.ControleurTorrent import download_torrent, stop_download
import os

# Créer un verrou pour synchroniser l'accès à la session
session_lock = threading.Lock()

# Variable globale pour stocker l'état du téléchargement
download_state = {
    'is_downloading': False,
    'handle': None,
    'save_path': None,
    'torrent_file_path': None,
    'downloaded_files': []
}

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
            download_state['is_downloading'] = False
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
                download_state['torrent_file_path'] = file_path
                file.save(file_path)
                write_log(f"Fichier .torrent déposé par {username} : {file_path}")
                return jsonify({'success': True, 'message': 'Fichier téléchargé avec succès', 'redirect_url': url_for('inner_start_download')})
            else:
                write_log(f"Format de fichier non supporté par {username}")
                return jsonify({'success': False, 'message': 'Format de fichier non supporté'}), 400

def start_download(app):
    @app.route('/start_download')
    def inner_start_download():
        try:
            username = session.get('username')
            
            @stream_with_context
            def generate():
                with session_lock:
                    write_log(f"Envoi d'une requête de téléchargement pour l'utilisateur: {username}")
                    
                    if download_state['is_downloading']:
                        write_log(f"Téléchargement déjà en cours pour {username}")
                        flash('Un téléchargement est déjà en cours')
                        return redirect(url_for('inner_download'))
                    
                    torrent_file_path = download_state['torrent_file_path']
                    if not torrent_file_path:
                        raise Exception("Chemin du fichier .torrent non trouvé dans l'état de téléchargement")
                    
                    download_state['is_downloading'] = True
                    try:
                        write_log(f"Téléchargement du fichier .torrent pour {username}")
                        for status in download_torrent(torrent_file_path, download_state):
                            yield status
                    except Exception as e:
                        write_log(f"Erreur lors du téléchargement du fichier .torrent pour {username}: {str(e)}")
                        flash('Erreur lors du téléchargement du fichier .torrent')
                        return redirect(url_for('inner_download'))
            
            return Response(generate(), mimetype='text/event-stream')
        except Exception as e:
            write_log(f"Erreur lors de la récupération du chemin du fichier .torrent pour {username}: {str(e)}")
            flash('Erreur lors de la récupération du chemin du fichier .torrent')
            return redirect(url_for('inner_download'))

def stop_download_route(app):
    @app.route('/stop_download', methods=['POST'])
    def inner_stop_download():
        with session_lock:
            write_log("Requête d'annulation de téléchargement reçue")
            write_log(f"État de l'état de téléchargement avant annulation: {download_state}")
            if stop_download(download_state):
                download_state['is_downloading'] = False
                write_log("Téléchargement annulé avec succès")
                return jsonify(success=True)
            else:
                write_log("Erreur lors de l'annulation du téléchargement")
                return jsonify(success=False)

    @app.route('/get_download_state', methods=['GET'])
    def get_download_state():
        with session_lock:
            return jsonify(download_state)