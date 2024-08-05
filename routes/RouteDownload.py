from flask import render_template, request, session, redirect, url_for, flash
from static.Controleur.ControleurLog import write_log
from static.Controleur.ControleurTorrent import download_torrent, get_download_status
import os

def download(app):
    @app.route('/download')
    def inner_download():
        username = session.get('username')
        write_log(f"Affichage de la page de téléchargement pour l'utilisateur: {username}")
        download_status = get_download_status()
        return render_template('download.html', username=username, download_status=download_status)

def upload(app):
    @app.route('/upload', methods=['POST'])
    def inner_upload():
        username = session.get('username')
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
            file_path = os.path.join("/home/chimea/Plex-Stock", filename)
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
            torrent_file_path = session.get('torrent_file_path')  # Remplacez par le chemin réel du fichier .torrent
            save_path = "/home/chimea/Plex-Stock"  # Remplacez par le chemin réel où vous souhaitez enregistrer les téléchargements
        except:
            write_log(f"Erreur lors de la récupération du chemin du fichier .torrent pour {username}")
            flash('Erreur lors de la récupération du chemin du fichier .torrent')
            return redirect(url_for('inner_download'))
        try:
            download_torrent(torrent_file_path, save_path)
        except:
            write_log(f"Erreur lors du téléchargement du fichier .torrent pour {username}")
            flash('Erreur lors du téléchargement du fichier .torrent')
            return redirect(url_for('inner_download'))  
        flash('Téléchargement démarré')
        return redirect(url_for('inner_download'))