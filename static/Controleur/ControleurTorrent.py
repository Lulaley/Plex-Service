from .ControleurLog import write_log
from .ControleurConf import ControleurConf
from .ControleurTMDB import ControleurTMDB
from .ControleurLibtorrent import configure_session_for_download
import libtorrent as lt
import time
import re
import os
import sys
import threading
import json
import fcntl

# Dictionnaire global pour stocker les informations des téléchargements en cours
downloads = {}
downloads_lock = threading.Lock()

# Fichier de persistance
DOWNLOADS_PERSISTENCE_FILE = "/var/www/public/Plex-Service/tmp/active_downloads.json"
DOWNLOADS_RESTORE_LOCK_FILE = "/var/www/public/Plex-Service/tmp/downloads_restore.lock"

def is_movie_or_series(torrent_info):
    """
    Détermine si le contenu du torrent est un film ou une série.
    """
    files = torrent_info.files()
    num_files = files.num_files()
    movie_extensions = ['.mp4', '.mkv', '.avi']
    episode_pattern = re.compile(r'(S\D{2}E\d{5})|(Episode\s\d+)', re.IGNORECASE)
    series_pattern = re.compile(r'(S\d{2})|(Season\s\d+)|(Integral)', re.IGNORECASE)

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
        r'S\d{2}', r'S\d{2}E\d{5}', r'Integral', r'Complete', r'season', r'episode', r'Saison',
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

def load_persisted_downloads():
    """Charge les downloads persistés depuis le fichier JSON avec verrouillage."""
    try:
        if os.path.exists(DOWNLOADS_PERSISTENCE_FILE):
            with open(DOWNLOADS_PERSISTENCE_FILE, 'r') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_SH)  # Verrou partagé (lecture)
                try:
                    return json.load(f)
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    except Exception as e:
        write_log(f"Erreur lors du chargement des downloads persistés: {str(e)}", "ERROR")
    return {}

def save_persisted_downloads():
    """Sauvegarde les downloads actifs dans le fichier JSON avec leurs stats et verrouillage."""
    try:
        serializable_downloads = {}
        with downloads_lock:
            for download_id, download_data in downloads.items():
                serializable_downloads[download_id] = {
                    'download_id': download_data.get('id', download_id),
                    'name': download_data.get('name', 'Unknown'),
                    'save_path': download_data.get('save_path', ''),
                    'torrent_path': download_data.get('torrent_file_path', ''),
                    'is_active': download_data.get('is_active', True),
                    'started_at': download_data.get('started_at', time.time()),
                    'stats': download_data.get('stats', {'progress': 0, 'download_rate': 0, 'upload_rate': 0, 'peers': 0, 'state': 'downloading'})
                }
        
        os.makedirs(os.path.dirname(DOWNLOADS_PERSISTENCE_FILE), exist_ok=True)
        with open(DOWNLOADS_PERSISTENCE_FILE, 'r+' if os.path.exists(DOWNLOADS_PERSISTENCE_FILE) else 'w') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)  # Verrou exclusif (écriture)
            try:
                f.seek(0)
                f.truncate()
                json.dump(serializable_downloads, f, indent=4)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    except Exception as e:
        write_log(f"Erreur lors de la sauvegarde des downloads: {str(e)}", "ERROR")

def remove_download_from_persistence(download_id):
    """Retire un download spécifique du fichier de persistance avec verrouillage."""
    try:
        os.makedirs(os.path.dirname(DOWNLOADS_PERSISTENCE_FILE), exist_ok=True)
        with open(DOWNLOADS_PERSISTENCE_FILE, 'r+' if os.path.exists(DOWNLOADS_PERSISTENCE_FILE) else 'w') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)  # Verrou exclusif
            try:
                if f.tell() == 0 and os.path.getsize(DOWNLOADS_PERSISTENCE_FILE) > 0:
                    persisted = json.load(f)
                else:
                    persisted = {}
                
                if download_id in persisted:
                    del persisted[download_id]
                    f.seek(0)
                    f.truncate()
                    json.dump(persisted, f, indent=4)
                    write_log(f"Download {download_id} retiré de la persistance")
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    except Exception as e:
        write_log(f"Erreur lors du retrait du download de la persistance: {str(e)}", "ERROR")

def get_all_downloads():
    """Retourne la liste de tous les downloads actifs depuis le fichier de persistance (partagé entre workers)."""
    persisted_downloads = load_persisted_downloads()
    
    downloads_list = []
    for download_id, download_info in persisted_downloads.items():
        # Par défaut, utiliser les stats depuis le fichier JSON (partagées entre workers)
        stats = download_info.get('stats', {'progress': 0, 'download_rate': 0, 'upload_rate': 0, 'peers': 0, 'state': 'downloading'})
        is_active = download_info.get('is_active', True)
        started_at = download_info.get('started_at', time.time())
        
        # Si ce worker gère ce download, utiliser les stats en mémoire (plus récentes)
        with downloads_lock:
            if download_id in downloads:
                stats = downloads[download_id].get('stats', stats)
                is_active = downloads[download_id].get('is_active', is_active)
                started_at = downloads[download_id].get('started_at', started_at)
        
        # Calculer le temps écoulé depuis le démarrage
        elapsed_seconds = int(time.time() - started_at)
        
        downloads_list.append({
            'download_id': download_id,
            'name': download_info.get('name', 'Unknown'),
            'save_path': download_info.get('save_path', ''),
            'is_active': is_active,
            'elapsed_seconds': elapsed_seconds,  # Ajouter le temps écoulé
            'progress': stats.get('progress', 0),
            'stats': stats
        })
    
    return downloads_list

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

def get_free_space_gb(directory):
    """Retourne l'espace libre en Go pour le répertoire donné."""
    statvfs = os.statvfs(directory)
    # Calculer l'espace libre en Go
    free_space_gb = (statvfs.f_frsize * statvfs.f_bavail) / (1024 ** 3)
    return free_space_gb

def get_total_space_gb(directory):
    """Retourne l'espace total en Go pour le répertoire donné."""
    statvfs = os.statvfs(directory)
    # Calculer l'espace total en Go
    total_space_gb = (statvfs.f_frsize * statvfs.f_blocks) / (1024 ** 3)
    return total_space_gb

def get_directory_size_gb(directory):
    """Retourne la taille totale en Go des fichiers dans le répertoire donné."""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(directory):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size / (1024 ** 3)

def save_download_resume_data(download_id, handle):
    """Sauvegarde les resume_data d'un téléchargement pour reprise sans re-checking."""
    # Version simplifiée - l'API write_resume_data_buf ne fonctionne pas correctement
    # On se contente de sauvegarder l'info hash qui sera utilisé pour reprendre
    try:
        resume_dir = '/var/www/public/Plex-Service/tmp/resume_data'
        os.makedirs(resume_dir, exist_ok=True)
        
        resume_file = os.path.join(resume_dir, f'{download_id}.resume')
        
        # Créer simplement un marqueur pour indiquer que ce download existait
        # Les resume_data de libtorrent seront gérés automatiquement via fastresume
        with open(resume_file, 'w') as f:
            f.write(f"{download_id}\n")
        
        write_log(f"Marqueur de reprise créé pour download {download_id}")
            
    except Exception as e:
        write_log(f"Erreur création marqueur resume pour {download_id}: {str(e)}", "WARNING")

def stop_download(handle):
    write_log("Appel de la fonction stop_download")
    write_log(f"handle: {handle}")
    if handle['is_downloading']:
        write_log("Téléchargement en cours détecté")
        if handle['handle']:
            handle['handle'].pause()
            handle['handle'].clear_error()
            handle['is_downloading'] = False
            handle['is_active'] = False
            write_log("Téléchargement annulé par l'utilisateur.")
            
            # Supprimer les fichiers téléchargés (commenté pour le test)
            for file_path in handle['downloaded_files']:
                if os.path.exists(file_path):
                    # os.remove(file_path)
                    write_log(f"[TEST] Fichier téléchargé qui aurait été supprimé : {file_path}")
            
            # Supprimer le fichier .torrent (commenté pour le test)
            if handle['torrent_file_path'] and os.path.exists(handle['torrent_file_path']):
                # os.remove(handle['torrent_file_path'])
                write_log(f"[TEST] Fichier .torrent qui aurait été supprimé : {handle['torrent_file_path']}")
            
            # Réinitialiser la liste des fichiers téléchargés
            handle['downloaded_files'] = []
            
            return True
    return False

def download_torrent(torrent_file_path, save_path, handle):
    write_log(f"Début de la fonction download_torrent avec le chemin : {torrent_file_path}")
    conf = ControleurConf()
    
    # Utiliser la session globale unique au lieu d'en créer une nouvelle
    ses = configure_session_for_download()
    
    write_log(f"Chargement du fichier .torrent pour {torrent_file_path}")
    info = lt.torrent_info(torrent_file_path)
    write_log(f"info: {info}")
    content_type = is_movie_or_series(info)
    
    # Vérifier l'espace disque disponible
    min_free_space_gb = 50
    if content_type == 'series' or content_type == 'episode':
        save_path = conf.get_config('DLT', 'series')
        write_log("Le contenu du torrent est identifié comme une série")
        search = ControleurTMDB()
        write_log(f"Recherche de la série {info.name()} dans la base de données TMDB")
        search_name = extract_title_prefix(info.name())
        search_name = search_name.replace('.', ' ')
        write_log(f"Nom de la série extrait: {search_name}")
        try:
            series_info = search.search_serie(search_name)
            name = series_info['name']
            write_log(f"Nom de la série: {name}")
            name = name.replace(' ', '.')
        except (ValueError, KeyError, IndexError) as e:
            write_log(f"Impossible de trouver la série sur TMDB: {str(e)}", "WARNING")
            write_log(f"Utilisation du nom du torrent comme nom de dossier", "WARNING")
            name = extract_title_prefix(info.name())
            name = name.replace(' ', '.')
    else:
        save_path = conf.get_config('DLT', 'movies')
        write_log("Le contenu du torrent est identifié comme un film")
    
    write_log(f"Le contenu du torrent est identifié comme: {content_type}")
    
    free_space_gb = get_free_space_gb(save_path)
    write_log(f"Espace libre sur le disque: {free_space_gb:.2f} Go")
    
    if free_space_gb < min_free_space_gb:
        write_log(f"Pas assez d'espace libre sur le disque. Espace requis: {min_free_space_gb} Go")
        write_log(f"Vérification de l'option de sauvegarde: {conf.get_config('SAVE', 'use_save')}")
        if conf.get_config('SAVE', 'use_save') == 'true':
            if content_type == 'series' or content_type == 'episode':
                save_path = conf.get_config('SAVE', 'series')
            else:
                save_path = conf.get_config('SAVE', 'movies')
            
            total_space_gb = get_total_space_gb(save_path)
            free_space_gb = get_free_space_gb(save_path)
            used_space_gb = get_directory_size_gb(save_path)
            write_log(f"Espace libre: {free_space_gb:.2f} Go")
            write_log(f"Espace utilisé par le dossier: {used_space_gb:.2f} Go")
            
            # Lire les pourcentages d'utilisation de l'espace disque depuis la configuration
            series_max_usage = int(conf.get_config('SAVE', 'series_max_usage'))
            movies_max_usage = int(conf.get_config('SAVE', 'movies_max_usage'))

            # Vérifier que le répertoire de sauvegarde ne dépasse pas le pourcentage d'utilisation de l'espace disque
            if content_type == 'series' or content_type == 'episode':
                max_usage_gb = total_space_gb * (series_max_usage / 100)
            else:
                max_usage_gb = total_space_gb * (movies_max_usage / 100)
                
            if used_space_gb > max_usage_gb:
                write_log(f"Le répertoire de sauvegarde dépasse le pourcentage d'utilisation de l'espace disque. Espace requis: {max_usage_gb} Go . Annulation du téléchargement.", "ERROR")
                yield "data: not enough space\n\n"
                return
            write_log(f"Redirection du téléchargement vers: {save_path}")

        else:
            write_log("Pas assez d'espace libre et l'option de sauvegarde est désactivée. Annulation du téléchargement.", "ERROR")
            yield "data: not enough space\n\n"
            return
    
    if content_type == 'series' or content_type == 'episode':
        save_path = ensure_directory_exists(save_path, name)
        write_log(f"Chemin de sauvegarde: {save_path}")
    
    # Préparer les paramètres du torrent
    atp = {
        'ti': info,
        'save_path': save_path
    }
    
    # Charger les resume_data si disponibles pour reprendre sans re-checking
    resume_file = os.path.join('/var/www/public/Plex-Service/tmp/resume_data', f'{handle["id"]}.resume')
    if os.path.exists(resume_file):
        try:
            with open(resume_file, 'rb') as f:
                atp['resume_data'] = f.read()
            write_log(f"Resume data chargé pour {handle['id']}, reprise sans re-checking")
        except Exception as e:
            write_log(f"Erreur lors du chargement des resume_data: {str(e)}", "WARNING")
    
    h = ses.add_torrent(atp)
    handle['is_downloading'] = True
    handle['handle'] = h
    handle['save_path'] = save_path
    handle['torrent_file_path'] = torrent_file_path
    handle['downloaded_files'] = []
    handle['started_at'] = time.time()  # Enregistrer le temps de démarrage

    with downloads_lock:
        downloads[handle['id']] = handle
    
    # Sauvegarder dans le fichier de persistance
    save_persisted_downloads()

    write_log(f"Téléchargement de {info.name()}")
    iteration = 0  # Compteur pour sauvegarder les resume_data périodiquement
    while not h.is_seed():
        # Vérifier si le téléchargement a été annulé localement
        if not handle['is_downloading']:
            write_log("Téléchargement annulé localement.")
            # Sauvegarder resume_data pour reprendre plus tard
            try:
                save_download_resume_data(handle['id'], h)
            except Exception as e:
                write_log(f"Erreur sauvegarde resume_data: {str(e)}", "WARNING")
            ses.remove_torrent(h)
            with downloads_lock:
                if handle['id'] in downloads:
                    del downloads[handle['id']]
            remove_download_from_persistence(handle['id'])
            yield "data: cancelled\n\n"
            return
        
        # Vérifier si le téléchargement a été annulé via le fichier de persistance (depuis un autre worker)
        persisted = load_persisted_downloads()
        if handle['id'] in persisted and not persisted[handle['id']].get('is_active', True):
            write_log("Téléchargement annulé via le fichier de persistance (autre worker).")
            handle['is_downloading'] = False
            handle['is_active'] = False
            # Sauvegarder resume_data pour reprendre plus tard
            try:
                save_download_resume_data(handle['id'], h)
            except Exception as e:
                write_log(f"Erreur sauvegarde resume_data: {str(e)}", "WARNING")
            ses.remove_torrent(h)
            with downloads_lock:
                if handle['id'] in downloads:
                    del downloads[handle['id']]
            remove_download_from_persistence(handle['id'])
            yield "data: cancelled\n\n"
            return

        s = h.status()
        log_message = '%.2f%% complete (down: %.1f kB/s up: %.1f kB/s peers: %d) %s' % (
            s.progress * 100, s.download_rate / 1000, s.upload_rate / 1000,
            s.num_peers, s.state)
        write_log(log_message)
        
        # Mettre à jour les stats
        handle['stats'] = {
            'progress': s.progress * 100,
            'download_rate': s.download_rate / 1000,
            'upload_rate': s.upload_rate / 1000,
            'peers': s.num_peers,
            'state': str(s.state)
        }
        handle['name'] = info.name()
        
        # Sauvegarder les stats dans le fichier
        save_persisted_downloads()
        
        # Sauvegarder les resume_data toutes les 10 itérations (10 secondes)
        # TEMPORAIREMENT DÉSACTIVÉ - API libtorrent incompatible
        # iteration += 1
        # if iteration % 10 == 0:
        #     try:
        #         save_download_resume_data(handle['id'], h)
        #     except Exception as e:
        #         write_log(f"Erreur sauvegarde périodique resume_data: {str(e)}", "WARNING")
        
        # Ajouter les fichiers téléchargés à la liste
        for file in h.get_torrent_info().files():
            file_path = os.path.join(save_path, file.path)
            if file_path not in handle['downloaded_files']:
                handle['downloaded_files'].append(file_path)
        
        yield f"data: {log_message}\n\n"
        sys.stdout.flush()  # Force l'envoi des données
        time.sleep(1)

    write_log(f"Téléchargement de {info.name()} Fini")
    ses.remove_torrent(h)
    with downloads_lock:
        del downloads[handle['id']]
    
    # Retirer de la persistance une fois terminé
    remove_download_from_persistence(handle['id'])
    
    # Supprimer les resume_data (plus nécessaires)
    resume_file = os.path.join('/var/www/public/Plex-Service/tmp/resume_data', f'{handle["id"]}.resume')
    if os.path.exists(resume_file):
        try:
            os.remove(resume_file)
            write_log(f"Resume data supprimé pour {handle['id']}")
        except Exception as e:
            write_log(f"Erreur suppression resume_data: {str(e)}", "WARNING")
    
    yield "data: done\n\n"
    sys.stdout.flush()  # Force l'envoi des données
    
    if os.path.exists(torrent_file_path):
        os.remove(torrent_file_path)
        write_log(f"Fichier .torrent supprimé : {torrent_file_path}")
    
    handle['is_downloading'] = False
    handle['handle'] = None
    handle['save_path'] = None
    handle['torrent_file_path'] = None
    handle['downloaded_files'] = []
