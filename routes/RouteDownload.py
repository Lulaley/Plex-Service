from flask import render_template, request, session, redirect, url_for, flash, Response, stream_with_context
import threading
from static.Controleur.ControleurLog import write_log
from static.Controleur.ControleurTorrent import download_torrent
import os

def download(app):
    @app.route('/download')
    def inner_download():
        username = session.get('username')
        write_log(f"Affichage de la page de téléchargement pour l'utilisateur: {username}")
        return render_template('download.html', username=username)

def upload(app):
    @app.route('/upload', methods=['POST'])
    def inner_upload():
        username = session.get('username')
        session['is_downloading'] = False
        write_log(f"Affichage de la page d'upload pour l'utilisateur: {username}")
        
        if 'torrent-file' not in request.files:
            write_log(f"Aucun fichier sélectionné par {username}")
            flash('Aucun fichier sélectionné')
            return redirect(url_for('inner_download'))
        
        file = request.files['torrent-file']
        if file.filename == '':
            write_log(f"Aucun fichier sélectionné par {username}")
            flash('Aucun fichier sélectionné')
            return redirect(url_for('inner_download'))
        
        if file and file.filename.endswith('.torrent'):
            filename = file.filename.replace(' ', '_')
            file_path = os.path.join("/var/www/public/Plex-Service/tmp/", filename)
            session['torrent_file_path'] = file_path
            write_log(f"Téléchargement du fichier .torrent par {username} : {file_path}")
            file.save(file_path)
            write_log(f"Fichier .torrent téléchargé par {username} : {filename}")
            flash('Fichier .torrent téléchargé avec succès')
            return redirect(url_for('inner_start_download'))
        else:
            write_log(f"Format de fichier non supporté par {username}")
            flash('Format de fichier non supporté')
            return redirect(url_for('inner_download'))

def start_download(app):
    @app.route('/start_download')
    def inner_start_download():
        try:
            username = session.get('username')
            write_log(f"Envoi d'une requête de téléchargement pour l'utilisateur: {username}")
            
            if session.get('is_downloading'):
                write_log(f"Téléchargement déjà en cours pour {username}")
                flash('Un téléchargement est déjà en cours')
                return redirect(url_for('inner_download'))
            
            torrent_file_path = session.get('torrent_file_path')
            if not torrent_file_path:
                raise Exception("Chemin du fichier .torrent non trouvé dans la session")
            
            session['is_downloading'] = True
            response = generate(torrent_file_path)
            session['is_downloading'] = False
            return response
        except Exception as e:
            write_log(f"Erreur lors de la récupération du chemin du fichier .torrent pour {username}: {str(e)}")
            flash('Erreur lors de la récupération du chemin du fichier .torrent')
            return redirect(url_for('inner_download'))
        
    def generate(torrent_file_path):
        try:
            username = session.get('username')
            write_log(f"Téléchargement du fichier .torrent pour {username}")
            response = Response(download_torrent(torrent_file_path), mimetype='text/event-stream')
            response.headers['Content-Disposition'] = f'attachment; filename={torrent_file_path.split("/")[-1]}'
            write_log(f"Téléchargement du fichier .torrent terminé pour {username}")
            return response
        except Exception as e:
            write_log(f"Erreur lors du téléchargement du fichier .torrent pour {username}: {str(e)}")
            flash('Erreur lors du téléchargement du fichier .torrent')
            return redirect(url_for('inner_download'))
            

        #return Response(stream_with_context(generate()), mimetype='text/event-stream')
        
"""         try:
            write_log(f"Téléchargement du fichier .torrent pour {username}")
            response = Response(download_torrent(torrent_file_path), mimetype='text/event-stream')
            
            # Marquer la fin du téléchargement
            session['is_downloading'] = False
            
            # Supprimer le fichier .torrent après le téléchargement
            if os.path.exists(torrent_file_path):
                os.remove(torrent_file_path)
                write_log(f"Fichier .torrent supprimé pour {username} : {torrent_file_path}")
            
            return response
        except Exception as e:
            write_log(f"Erreur lors du téléchargement du fichier .torrent pour {username}: {str(e)}")
            flash('Erreur lors du téléchargement du fichier .torrent')
            session['is_downloading'] = False
            
            # Supprimer le fichier .torrent en cas d'erreur
            if os.path.exists(torrent_file_path):
                os.remove(torrent_file_path)
                write_log(f"Fichier .torrent supprimé pour {username} : {torrent_file_path}")
            return redirect(url_for('inner_download'))
        
        flash('Téléchargement démarré')
        return redirect(url_for('inner_download')) """
    
"""     def generate():
            try:
                for chunk in download_torrent(torrent_file_path):
                    yield chunk
                write_log(f"Téléchargement du fichier .torrent terminé pour {username}")
            except Exception as e:
                write_log(f"Erreur lors du téléchargement du fichier .torrent pour {username}: {str(e)}")
                flash('Erreur lors du téléchargement du fichier .torrent')
            finally:
                # Marquer la fin du téléchargement
                session['is_downloading'] = False
                
                # Supprimer le fichier .torrent après le téléchargement
                if os.path.exists(torrent_file_path):
                    os.remove(torrent_file_path)
                    write_log(f"Fichier .torrent supprimé pour {username} : {torrent_file_path}")

        return Response(stream_with_context(generate()), mimetype='text/event-stream') """