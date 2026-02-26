# Thread périodique pour mettre à jour les stats des seeds dans la BDD
import threading
def periodic_stats_update(interval=10):
    while True:
        try:
            get_all_seeds()  # Met à jour la BDD avec les stats de l'API
        except Exception as e:
            write_log(f"[PERIODIC] Erreur update stats seeds: {e}", "WARNING")
        time.sleep(interval)

threading.Thread(target=periodic_stats_update, args=(10,), daemon=True).start()
def sync_seeds_with_api():
    """Synchronise les seeds entre la BDD et l'API libtorrent_service : relance les seeds manquants côté API."""
    from static.Controleur.libtorrent_client import get_stats, add_seed
    from static.Controleur.ControleurDatabase import get_all_seeds_from_sql
    stats_api = get_stats()
    seeds_in_api = set(stats_api.keys())
    seeds_in_db = get_all_seeds_from_sql()
    for seed in seeds_in_db:
        if seed['id'] not in seeds_in_api:
            # Relance le seed via add_seed
            try:
                # Il faut le chemin du .torrent et du data_path
                add_seed(seed['id'], seed.get('torrent_file_path', ''), seed.get('data_path', ''))
                write_log(f"[SYNC] Relancé seed absent de l'API : {seed['id']}")
            except Exception as e:
                write_log(f"[SYNC] Erreur relance seed {seed['id']} : {e}", "WARNING")
import signal

# Handler de shutdown pour arrêter tous les seeds actifs proprement
def shutdown_handler(signum, frame):
    write_log(f"Signal {signum} reçu, arrêt propre de tous les seeds...")
    with seeds_lock:
        seeds_to_stop = list(active_seeds.keys())
    for seed_id in seeds_to_stop:
        try:
            stop_seed(seed_id)
        except Exception as e:
            write_log(f"Erreur lors de l'arrêt du seed {seed_id} pendant shutdown: {e}", "ERROR")
    write_log("Tous les seeds actifs ont été arrêtés proprement.")

# Enregistrement du handler pour SIGTERM et SIGINT
signal.signal(signal.SIGTERM, shutdown_handler)
signal.signal(signal.SIGINT, shutdown_handler)
from .ControleurLog import write_log
from .ControleurConf import ControleurConf
from .ControleurLibtorrent import configure_session_for_seed
from static.Controleur.libtorrent_client import add_seed, remove_seed
import time
import threading
import json
import os
import fcntl  # Pour le verrouillage de fichier

# Dictionnaire global pour stocker les seeds actifs
active_seeds = {}
seeds_lock = threading.Lock()

# Synchronisation automatique au démarrage du site
try:
    sync_seeds_with_api()
except Exception as e:
    write_log(f"[SYNC] Erreur lors de la synchronisation initiale avec l'API : {e}", "WARNING")

# Fichier de persistance
SEEDS_PERSISTENCE_FILE = "/var/www/public/Plex-Service/tmp/active_seeds.json"
# Fichier de lock pour éviter les restaurations multiples
SEEDS_RESTORE_LOCK_FILE = "/var/www/public/Plex-Service/tmp/seeds_restore.lock"

def load_persisted_seeds():
    """Charge les seeds persistés depuis le fichier JSON avec verrouillage."""
    try:
        if os.path.exists(SEEDS_PERSISTENCE_FILE):
            with open(SEEDS_PERSISTENCE_FILE, 'r') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_SH)  # Verrou partagé (lecture)
                try:
                    data = json.load(f)
                    return data
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    except Exception as e:
        write_log(f"Erreur lors du chargement des seeds persistés: {str(e)}", "ERROR")
    return {}

def save_persisted_seeds():
    """Sauvegarde les seeds actifs dans le fichier JSON avec leurs stats et verrouillage."""
    try:
        os.makedirs(os.path.dirname(SEEDS_PERSISTENCE_FILE), exist_ok=True)
        
        with open(SEEDS_PERSISTENCE_FILE, 'r+' if os.path.exists(SEEDS_PERSISTENCE_FILE) else 'w') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)  # Verrou exclusif (écriture)
            try:
                # Charger les seeds existants depuis le fichier
                if f.tell() == 0 and os.path.exists(SEEDS_PERSISTENCE_FILE) and os.path.getsize(SEEDS_PERSISTENCE_FILE) > 0:
                    existing_seeds = json.load(f)
                else:
                    existing_seeds = {}
                
                # Mettre à jour uniquement les seeds de ce worker
                with seeds_lock:
                    for seed_id, seed_data in active_seeds.items():
                        # Ne pas ré-ajouter un seed qui a été supprimé par un autre worker
                        if seed_id in existing_seeds and not existing_seeds[seed_id].get('is_active', True):
                            continue
                        
                        existing_seeds[seed_id] = {
                            'id': seed_data['id'],
                            'torrent_file_path': seed_data['torrent_file_path'],
                            'data_path': seed_data['data_path'],
                            'name': seed_data['name'],
                            'is_active': seed_data['is_active'],
                            'stats': seed_data.get('stats', {'uploaded': 0, 'upload_rate': 0, 'peers': 0, 'seeds': 0, 'progress': 0, 'state': 'unknown'}),
                            'state': seed_data.get('state', 'unknown')
                        }
                
                # Sauvegarder tous les seeds
                f.seek(0)
                f.truncate()
                json.dump(existing_seeds, f, indent=4)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    except Exception as e:
        write_log(f"Erreur lors de la sauvegarde des seeds: {str(e)}", "ERROR")

def find_torrent_file(data_path):
    """Recherche un fichier .torrent dans le répertoire ou crée-en un."""
    write_log(f"Recherche d'un fichier .torrent pour: {data_path}")
    
    # Vérifier si le chemin existe
    if not os.path.exists(data_path):
        write_log(f"Le chemin {data_path} n'existe pas", "ERROR")
        return None
    
    # Si c'est un répertoire, chercher un fichier .torrent dedans
    if os.path.isdir(data_path):
        for file in os.listdir(data_path):
            if file.endswith('.torrent'):
                torrent_path = os.path.join(data_path, file)
                write_log(f"Fichier .torrent trouvé: {torrent_path}")
                return torrent_path
    
    # Si c'est un fichier, chercher un .torrent avec le même nom
    if os.path.isfile(data_path):
        base_name = os.path.splitext(os.path.basename(data_path))[0]
        dir_path = os.path.dirname(data_path)
        torrent_path = os.path.join(dir_path, f"{base_name}.torrent")
        if os.path.exists(torrent_path):
            write_log(f"Fichier .torrent trouvé: {torrent_path}")
            return torrent_path
    
    write_log(f"Aucun fichier .torrent trouvé pour {data_path}", "WARNING")
    return None

def get_all_media_paths():
    """Retourne la liste de tous les fichiers/dossiers disponibles pour le seed."""
    conf = ControleurConf()
    media_paths = []
    
    try:
        # Récupérer les chemins des films et séries
        movies_path = conf.get_config('DLT', 'movies')
        series_path = conf.get_config('DLT', 'series')
        
        # Ajouter les films
        if os.path.exists(movies_path):
            for item in os.listdir(movies_path):
                item_path = os.path.join(movies_path, item)
                if os.path.isfile(item_path) and item.endswith(('.mp4', '.mkv', '.avi')):
                    media_paths.append({
                        'path': item_path,
                        'name': item,
                        'type': 'movie'
                    })
        
        # Ajouter les séries
        if os.path.exists(series_path):
            for series_folder in os.listdir(series_path):
                series_folder_path = os.path.join(series_path, series_folder)
                if os.path.isdir(series_folder_path):
                    media_paths.append({
                        'path': series_folder_path,
                        'name': series_folder,
                        'type': 'series'
                    })
        
        write_log(f"Chemins médias trouvés: {len(media_paths)}")
    except Exception as e:
        write_log(f"Erreur lors de la récupération des chemins médias: {str(e)}", "ERROR")
    
    return media_paths

def start_seed(seed_id, torrent_file_path, data_path):
    """Démarre un seed pour un fichier torrent donné."""
    write_log(f"[API] Démarrage du seed {seed_id} pour {torrent_file_path}")
    try:
        result = add_seed(seed_id, torrent_file_path, data_path)
        if result.get('success'):
            write_log(f"[API] Seed {seed_id} ajouté via API")
            # Ici, tu peux garder la logique BDD/JSON si besoin
            return True
        else:
            write_log(f"[API] Erreur API add_seed: {result.get('error')}", "ERROR")
            return False
    except Exception as e:
        write_log(f"[API] Exception lors du démarrage du seed {seed_id}: {str(e)}", "ERROR")
        return False

def monitor_seed(seed_id):
    """Monitore un seed et met à jour ses statistiques."""
    write_log(f"Démarrage du monitoring pour le seed {seed_id}")
    
    check_counter = 0  # Compteur pour vérifier l'arrêt moins souvent
    
    while True:
        try:
            check_counter += 1
            
            # Vérifier si le seed a été arrêté par un autre worker (toutes les 10s au lieu de 2s)
            if check_counter % 5 == 0:  # 5 * 2s = 10s
                persisted = load_persisted_seeds()
                if seed_id not in persisted or not persisted[seed_id].get('is_active', True):
                    write_log(f"Seed {seed_id} arrêté par un autre worker, arrêt du monitoring")
                    with seeds_lock:
                        if seed_id in active_seeds:
                            # Arrêter proprement le seed dans ce worker
                            seed_data = active_seeds[seed_id]
                            if 'session' in seed_data and seed_data['session']:
                                try:
                                    seed_data['session'].remove_torrent(seed_data['handle'])
                                except:
                                    pass
                            del active_seeds[seed_id]
                    break
            
            with seeds_lock:
                if seed_id not in active_seeds:
                    write_log(f"Seed {seed_id} n'existe plus, arrêt du monitoring")
                    break
                
                seed_data = active_seeds[seed_id]
                if not seed_data['is_active']:
                    write_log(f"Seed {seed_id} n'est plus actif, arrêt du monitoring")
                    break
                
                h = seed_data['handle']
                s = h.status()
                
                # Log de l'état actuel
                state_str = str(s.state)
                if seed_data.get('state') != state_str:
                    write_log(f"Seed {seed_id} - Changement d'état: {state_str}")
                    seed_data['state'] = state_str
                
                # Calculer la progression (progress_ppm fonctionne aussi pendant checking_files)
                progress = s.progress_ppm / 10000.0  # Convertir parts-per-million en pourcentage
                
                # Mettre à jour les statistiques
                seed_data['stats'] = {
                    'uploaded': s.total_upload,
                    'upload_rate': s.upload_rate / 1000,  # en kB/s
                    'peers': s.num_peers,
                    'seeds': s.num_seeds,
                    'progress': progress,
                    'state': state_str
                }
            
            # Sauvegarder les stats dans le fichier JSON pour que les autres workers les voient
            save_persisted_seeds()
            
            time.sleep(2)  # Mettre à jour toutes les 2 secondes
        except Exception as e:
            write_log(f"Erreur dans le monitoring du seed {seed_id}: {str(e)}", "ERROR")
            time.sleep(5)

def stop_seed(seed_id):
    """Arrête un seed."""
    write_log(f"[API] Arrêt du seed {seed_id}")
    try:
        result = remove_seed(seed_id)
        if result.get('success'):
            write_log(f"[API] Seed {seed_id} supprimé via API")
            # Ici, tu peux garder la logique BDD/JSON si besoin
            return True
        else:
            write_log(f"[API] Erreur API remove_seed: {result.get('error')}", "ERROR")
            return False
    except Exception as e:
        write_log(f"[API] Exception lors de l'arrêt du seed {seed_id}: {str(e)}", "ERROR")
        return False

def save_resume_data(identifier, handle):
    """Sauvegarde les resume_data d'un torrent."""
    try:
        resume_dir = '/var/www/public/Plex-Service/tmp/resume_data'
        os.makedirs(resume_dir, exist_ok=True)
        
        resume_file = os.path.join(resume_dir, f'{identifier}.resume')
        
        # Utiliser write_resume_data pour récupérer l'add_torrent_params
        try:
            atp = handle.write_resume_data()
            resume_data = lt.write_resume_data_buf(atp)
            
            with open(resume_file, 'wb') as f:
                f.write(resume_data)
            
            write_log(f"Resume data sauvegardé pour {identifier}")
        except Exception as e:
            write_log(f"Erreur lors de la sauvegarde des resume_data pour {identifier}: {str(e)}", "WARNING")
    except Exception as e:
        write_log(f"Erreur lors de la sauvegarde des resume_data pour {identifier}: {str(e)}", "WARNING")

def get_seed_stats(seed_id):
    """Retourne les statistiques d'un seed."""
    with seeds_lock:
        if seed_id in active_seeds:
            return active_seeds[seed_id]['stats']
    return None

def get_all_seeds():
    """Retourne la liste de tous les seeds actifs depuis l'API libtorrent_service (source de vérité)."""
    from static.Controleur.libtorrent_client import get_stats
    from static.Controleur.ControleurDatabase import update_seed_stats_in_db
    stats_api = get_stats()
    seeds_list = []
    for seed_id, info in stats_api.items():
        # Met à jour la BDD avec les stats reçues
        try:
            update_seed_stats_in_db(seed_id, info)
        except Exception as e:
            write_log(f"Erreur update_seed_stats_in_db pour {seed_id}: {e}", "WARNING")
        seeds_list.append({
            'id': seed_id,
            'name': info.get('name', 'Unknown'),
            'data_path': '',  # Peut être complété depuis la BDD si besoin
            'is_active': True,
            'state': info.get('state', 'seeding'),
            'stats': info
        })
    return seeds_list

def restore_seeds():
    """Restaure les seeds persistés au démarrage (depuis SQL ou JSON selon le mode)."""
    from static.Controleur.ControleurDatabase import use_sql_mode, load_seeds_from_db
    lock_file = None
    try:
        os.makedirs(os.path.dirname(SEEDS_RESTORE_LOCK_FILE), exist_ok=True)
        lock_file = open(SEEDS_RESTORE_LOCK_FILE, 'w')
        try:
            # Seul le worker qui obtient le lock exclusif restaure les seeds
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            write_log("Ce worker Gunicorn restaure les seeds (lock acquis)")
            if use_sql_mode():
                write_log("Restauration des seeds depuis SQLite (mode SQL)")
                seeds_db = load_seeds_from_db()
                for seed_id, seed_info in seeds_db.items():
                    try:
                        write_log(f"Restauration du seed SQL {seed_id}")
                        start_seed(
                            seed_id,
                            seed_info.get('torrent_path', ''),
                            seed_info.get('data_path', '')
                        )
                    except Exception as e:
                        write_log(f"Erreur lors de la restauration du seed SQL {seed_id}: {str(e)}", "ERROR")
            else:
                write_log("Restauration des seeds persistés (mode JSON)")
                persisted_seeds = load_persisted_seeds()
                for seed_id, seed_info in persisted_seeds.items():
                    try:
                        write_log(f"Restauration du seed {seed_id}")
                        start_seed(
                            seed_id,
                            seed_info['torrent_file_path'],
                            seed_info['data_path']
                        )
                    except Exception as e:
                        write_log(f"Erreur lors de la restauration du seed {seed_id}: {str(e)}", "ERROR")
        except IOError:
            # Les autres workers ne restaurent pas les seeds
            write_log("Un autre worker Gunicorn est déjà en train de restaurer les seeds, skip")
            return
    except Exception as e:
        write_log(f"Erreur globale lors de la restauration des seeds: {str(e)}", "ERROR")
    finally:
        if lock_file:
            try:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                lock_file.close()
            except OSError as e:
                write_log(f"Erreur lors de la fermeture du fichier de verrouillage: {e}", "WARNING")
