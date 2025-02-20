from flask import render_template, request, session, jsonify, redirect, url_for, flash, Response, stream_with_context
import threading
from static.Controleur.ControleurLog import write_log
from static.Controleur.ControleurTorrent import download_torrent
import os

def download(app):
    @app.route('/download')
    def inner_download():
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
        username = session.get('username')
        session['is_downloading'] = False
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
            session['torrent_file_path'] = file_path
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
                write_log(f"Envoi d'une requête de téléchargement pour l'utilisateur: {username}")
                
                if session.get('is_downloading'):
                    write_log(f"Téléchargement déjà en cours pour {username}")
                    flash('Un téléchargement est déjà en cours')
                    return redirect(url_for('inner_download'))
                
                torrent_file_path = session.get('torrent_file_path')
                if not torrent_file_path:
                    raise Exception("Chemin du fichier .torrent non trouvé dans la session")
                
                session['is_downloading'] = True
                try:
                    write_log(f"Téléchargement du fichier .torrent pour {username}")
                    for status in download_torrent(torrent_file_path):
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