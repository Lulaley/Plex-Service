from flask import render_template, request, session, jsonify, redirect, url_for, flash, Response, stream_with_context
from static.Controleur.ControleurLog import write_log
from static.Controleur.ControleurTorrent import download_torrent, stop_download, downloads, downloads_lock
import threading
import uuid
import os

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
                return jsonify({'success': True, 'message': 'Fichier téléchargé avec succès', 'redirect_url': url_for('inner_start_download', torrent_file_path=file_path), 'download_id': str(uuid.uuid4())})

            else:
                write_log(f"Format de fichier non supporté par {username}")
                return jsonify({'success': False, 'message': 'Format de fichier non supporté'}), 400

def start_download(app):
    @app.route('/start_download')
    def inner_start_download():
        try:
            username = session.get('username')
            torrent_file_path = request.args.get('torrent_file_path')
            save_path = request.args.get('save_path')
            download_id = str(uuid.uuid4())  # Générer un identifiant unique pour le téléchargement
            
            @stream_with_context
            def generate():
                with session_lock:
                    write_log(f"Envoi d'une requête de téléchargement pour l'utilisateur: {username}")
                    
                    handle = {
                        'id': download_id,
                        'is_downloading': True,
                        'handle': None,
                        'save_path': save_path,
                        'torrent_file_path': torrent_file_path,
                        'downloaded_files': []
                    }
                    downloads[download_id] = handle  # Stocker le handle dans le dictionnaire global downloads
                    try:
                        write_log(f"Téléchargement du fichier .torrent pour {username}")
                        for status in download_torrent(torrent_file_path, save_path, handle):
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
            data = request.get_json()
            download_id = data.get('download_id')  # Récupérer l'identifiant du téléchargement
            handle = downloads.get(download_id)  # Utiliser le dictionnaire global downloads
            if handle:
                write_log(f"Annulation du téléchargement pour l'utilisateur: {handle['username']}")
                if stop_download(handle):
                    write_log("Téléchargement annulé avec succès")
                    return jsonify(success=True)
                else:
                    write_log("Erreur lors de l'annulation du téléchargement")
                    return jsonify(success=False)
            else:
                write_log("Aucun téléchargement en cours pour cet identifiant")
                return jsonify(success=False)