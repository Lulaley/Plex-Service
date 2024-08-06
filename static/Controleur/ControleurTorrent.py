from static.Controleur.ControleurLog import write_log
from static.Controleur.ControleurConf import ControleurConf
from flask import flash, get_flashed_messages
import libtorrent as lt
import time
import re

# Variable globale pour stocker l'état du téléchargement
download_status = {}

def is_movie_or_series(torrent_info):
    """
    Détermine si le contenu du torrent est un film ou une série.
    """
    files = torrent_info.files()
    num_files = files.num_files()
    movie_extensions = ['.mp4', '.mkv', '.avi']
    episode_pattern = re.compile(r'(E\d{2})|(Episode\s\d+)', re.IGNORECASE)
    series_pattern = re.compile(r'(S\d{2})|(Season\s\d+)', re.IGNORECASE)

    for i in range(num_files):
        file_path = files.file_path(i)
        if any(ext in file_path for ext in movie_extensions):
            if episode_pattern.search(file_path):
                return 'episode'
            elif series_pattern.search(file_path):
                return 'series'
            else:
                return 'movie'
    return 'unknown'

def download_torrent(torrent_file_path, save_path):

    ses = lt.session()
    write_log(f"Chargement du fichier .torrent pour {torrent_file_path}")
    info = lt.torrent_info(torrent_file_path)  # replace with your torrent file
    
    content_type = is_movie_or_series(info)
    write_log(f"Le contenu du torrent est identifié comme: {content_type}")
    info.print_files()
    
    #h = ses.add_torrent({'ti': info, 'save_path': save_path})  # download to current directory

    write_log(f"Téléchargement de {info.name()}")
    while not h.is_seed():
        s = h.status()
        log_message = '%.2f%% complete (down: %.1f kB/s up: %.1f kB/s peers: %d) %s' % (
            s.progress * 100, s.download_rate / 1000, s.upload_rate / 1000,
            s.num_peers, s.state)
        get_flashed_messages()
        write_log(log_message)
        flash(log_message)
        time.sleep(1)

    write_log(f"Téléchargement de {info.name()} Fini")
    ses.remove_torrent(h)
