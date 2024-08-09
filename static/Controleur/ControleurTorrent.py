from .ControleurLog import write_log
from .ControleurConf import ControleurConf
from .ControleurTMDB import ControleurTMDB
from flask import flash, get_flashed_messages, render_template, Response, session
import libtorrent as lt
import time
import re
import os
import sys

# Variable globale pour stocker l'état du téléchargement
download_status = {}

def is_movie_or_series(torrent_info):
    """
    Détermine si le contenu du torrent est un film ou une série.
    """
    files = torrent_info.files()
    num_files = files.num_files()
    movie_extensions = ['.mp4', '.mkv', '.avi']
    episode_pattern = re.compile(r'(S\D{2}E\d{5})|(Episode\s\d+)', re.IGNORECASE)
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

def extract_title_prefix(filename):
    # Liste des motifs à rechercher
    patterns = [
        r'S\d{2}', r'S\d{2}E\d{5}', r'Integral', r'Complete', r'season', r'episode',
        r'S\.\d{2}', r'S\.\d{2}E\.\d{5}', r'S\.\d{2}\.E\.\d{5}'
    ]
    
    # Rechercher le premier motif correspondant
    for pattern in patterns:
        match = re.search(pattern, filename, re.IGNORECASE)
        if match:
            # Extraire la sous-chaîne jusqu'au motif trouvé
            return filename[:match.start()].strip()
    
    # Si aucun motif n'est trouvé, retourner la chaîne entière
    return filename

def ensure_directory_exists(base_path, series_name):
    # Créer le chemin complet du dossier
    directory_path = os.path.join(base_path, series_name)
    
    # Vérifier si le dossier existe, sinon le créer
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        write_log(f"Dossier créé: {directory_path}")
    else:
        write_log(f"Dossier déjà existant: {directory_path}")
    return directory_path

def download_torrent(torrent_file_path):
    write_log(f"Début de la fonction download_torrent avec le chemin : {torrent_file_path}")
    conf = ControleurConf()
    ses = lt.session()
    settings = {
        'download_rate_limit': -1,  # Pas de limite de vitesse de téléchargement
        'upload_rate_limit': -1,    # Pas de limite de vitesse d'upload
    }
    ses.apply_settings(settings)
    write_log(f"Chargement du fichier .torrent pour {torrent_file_path}")
    info = lt.torrent_info(torrent_file_path)
    write_log(f"info: {info}")
    content_type = is_movie_or_series(info)
    if content_type == 'series' or content_type == 'episode':
        save_path = conf.get_config('DLT', 'series')
        write_log(f"Le contenu du torrent est identifié comme une série")
        search = ControleurTMDB()
        write_log(f"Recherche de la série {info.name()} dans la base de données TMDB")
        search_name = extract_title_prefix(info.name())
        search_name = search_name.replace('.', ' ')
        write_log(f"Nom de la série extrait: {search_name}")
        name = search.search_serie_name(search_name)
        write_log(f"Nom de la série: {name}")
        name = name.replace(' ', '.')
        save_path = ensure_directory_exists(save_path, name)
        write_log(f"Chemin de sauvegarde: {save_path}")
    else:
        save_path = conf.get_config('DLT', 'movies')
        write_log(f"Le contenu du torrent est identifié comme un film")
    write_log(f"Le contenu du torrent est identifié comme: {content_type}")
    
    h = ses.add_torrent({'ti': info, 'save_path': save_path})

    write_log(f"Téléchargement de {info.name()}")
    while not h.is_seed():
        s = h.status()
        log_message = '%.2f%% complete (down: %.1f kB/s up: %.1f kB/s peers: %d) %s' % (
            s.progress * 100, s.download_rate / 1000, s.upload_rate / 1000,
            s.num_peers, s.state)
        write_log(log_message)
        session['data'] = f"data : {log_message}\n\n"
        yield f"data: {log_message}\n\n"
        sys.stdout.flush()  # Force l'envoi des données
        time.sleep(1)

    write_log(f"Téléchargement de {info.name()} Fini")
    ses.remove_torrent(h)
    yield "data: done\n\n"
    sys.stdout.flush()  # Force l'envoi des données
    
    if os.path.exists(torrent_file_path):
        os.remove(torrent_file_path)
        write_log(f"Fichier .torrent supprimé : {torrent_file_path}")
