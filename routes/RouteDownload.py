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
            flash('Aucun fichier sélectionné')
            return redirect(url_for('inner_download'))
        
        file = request.files['torrent-file']
        if file.filename == '':
            flash('Aucun fichier sélectionné')
            return redirect(url_for('inner_download'))
        
        if file and file.filename.endswith('.torrent'):
            file_path = os.path.join("/path/to/save", file.filename)
            file.save(file_path)
            write_log(f"Fichier .torrent téléchargé par {username} : {file.filename}")
            flash('Fichier .torrent téléchargé avec succès')
            return redirect(url_for('inner_download'))
        else:
            flash('Format de fichier non supporté')
            return redirect(url_for('inner_download'))

def start_download(app):
    @app.route('/start_download', methods=['POST'])
    def inner_start_download():
        username = session.get('username')
        write_log(f"Envoi d'une requête de téléchargement pour l'utilisateur: {username}")
        torrent_file_path = "/path/to/save/your_torrent_file.torrent"  # Remplacez par le chemin réel du fichier .torrent
        save_path = "/path/to/save/downloads"  # Remplacez par le chemin réel où vous souhaitez enregistrer les téléchargements
        download_torrent(torrent_file_path, save_path)
        flash('Téléchargement démarré')
        return redirect(url_for('inner_download'))