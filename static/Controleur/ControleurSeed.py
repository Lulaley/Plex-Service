from .ControleurLog import write_log
from .ControleurConf import ControleurConf
import libtorrent as lt
import time
import threading
import json
import os
import fcntl  # Pour le verrouillage de fichier

# Dictionnaire global pour stocker les seeds actifs
active_seeds = {}
seeds_lock = threading.Lock()

# Fichier de persistance
SEEDS_PERSISTENCE_FILE = "/var/www/public/Plex-Service/tmp/active_seeds.json"
# Fichier de lock pour éviter les restaurations multiples
SEEDS_RESTORE_LOCK_FILE = "/var/www/public/Plex-Service/tmp/seeds_restore.lock"

def load_persisted_seeds():
    """Charge les seeds persistés depuis le fichier JSON."""
    try:
        if os.path.exists(SEEDS_PERSISTENCE_FILE):
            with open(SEEDS_PERSISTENCE_FILE, 'r') as f:
                data = json.load(f)
                # Log retiré car appelé trop fréquemment (polling frontend)
                return data
    except Exception as e:
        write_log(f"Erreur lors du chargement des seeds persistés: {str(e)}", "ERROR")
    return {}

def save_persisted_seeds():
    """Sauvegarde les seeds actifs dans le fichier JSON."""
    try:
        # Créer une version sérialisable des seeds (sans les objets libtorrent)
        serializable_seeds = {}
        with seeds_lock:
            for seed_id, seed_data in active_seeds.items():
                serializable_seeds[seed_id] = {
                    'id': seed_data['id'],
                    'torrent_file_path': seed_data['torrent_file_path'],
                    'data_path': seed_data['data_path'],
                    'name': seed_data['name'],
                    'is_active': seed_data['is_active']
                }
        
        with open(SEEDS_PERSISTENCE_FILE, 'w') as f:
            json.dump(serializable_seeds, f, indent=4)
        write_log(f"Seeds sauvegardés: {len(serializable_seeds)} seeds")
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
    write_log(f"Démarrage du seed {seed_id} pour {torrent_file_path}")
    
    try:
        ses = lt.session()
        settings = {
            'download_rate_limit': 0,  # Pas de téléchargement
            'upload_rate_limit': -1,   # Upload illimité
        }
        ses.apply_settings(settings)
        
        info = lt.torrent_info(torrent_file_path)
        write_log(f"Torrent info chargé: {info.name()}")
        
        # Nettoyer le data_path (enlever les / finaux)
        data_path = data_path.rstrip('/')
        write_log(f"data_path nettoyé: {data_path}")
        
        # Déterminer le chemin de sauvegarde
        # Le save_path doit être le dossier PARENT du contenu du torrent
        torrent_name = info.name()
        
        if os.path.isfile(data_path):
            # Si data_path est un fichier, le save_path est son dossier parent
            save_path = os.path.dirname(data_path)
        elif os.path.isdir(data_path):
            # Si data_path est un dossier et que son nom correspond au torrent
            if os.path.basename(data_path) == torrent_name:
                # Le save_path est le dossier parent
                save_path = os.path.dirname(data_path)
                write_log(f"Le dossier correspond au nom du torrent, utilisation du parent")
            else:
                # Le save_path est data_path lui-même
                save_path = data_path
                write_log(f"Le dossier ne correspond pas au nom du torrent, utilisation de data_path")
        else:
            save_path = data_path
        
        write_log(f"Chemin de sauvegarde déterminé: {save_path}")
        write_log(f"Nom du torrent: {torrent_name}")
        write_log(f"Chemin complet attendu: {os.path.join(save_path, torrent_name)}")
        
        # Vérifier que les fichiers existent
        expected_path = os.path.join(save_path, torrent_name)
        if not os.path.exists(expected_path):
            write_log(f"ATTENTION: Le chemin {expected_path} n'existe pas!", "WARNING")
            write_log(f"data_path fourni: {data_path}", "WARNING")
        else:
            write_log(f"Le chemin {expected_path} existe bien!")
        
        h = ses.add_torrent({
            'ti': info,
            'save_path': save_path,
            'flags': lt.torrent_flags.upload_mode  # Mode upload uniquement (pas de download)
        })
        
        # Forcer la vérification des fichiers
        h.force_recheck()
        write_log(f"Force recheck lancé pour {seed_id}")
        
        write_log(f"Torrent ajouté à la session, état initial: {h.status().state}")
        
        with seeds_lock:
            active_seeds[seed_id] = {
                'id': seed_id,
                'handle': h,
                'session': ses,
                'torrent_file_path': torrent_file_path,
                'data_path': data_path,
                'name': info.name(),
                'is_active': True,
                'state': 'starting',
                'stats': {
                    'uploaded': 0,
                    'upload_rate': 0,
                    'peers': 0,
                    'seeds': 0,
                    'progress': 0
                }
            }
        
        save_persisted_seeds()
        write_log(f"Seed {seed_id} ajouté au dictionnaire et sauvegardé")
        
        # Lancer le thread de monitoring
        monitor_thread = threading.Thread(target=monitor_seed, args=(seed_id,), daemon=True)
        monitor_thread.start()
        write_log(f"Thread de monitoring démarré pour le seed {seed_id}")
        
        return True
    except Exception as e:
        write_log(f"Erreur lors du démarrage du seed {seed_id}: {str(e)}", "ERROR")
        # Nettoyer en cas d'erreur
        with seeds_lock:
            if seed_id in active_seeds:
                del active_seeds[seed_id]
        return False

def monitor_seed(seed_id):
    """Monitore un seed et met à jour ses statistiques."""
    write_log(f"Démarrage du monitoring pour le seed {seed_id}")
    
    while True:
        try:
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
                
                # Mettre à jour les statistiques
                seed_data['stats'] = {
                    'uploaded': s.total_upload,
                    'upload_rate': s.upload_rate / 1000,  # en kB/s
                    'peers': s.num_peers,
                    'seeds': s.num_seeds,
                    'progress': s.progress * 100,
                    'state': state_str
                }
            
            time.sleep(2)  # Mettre à jour toutes les 2 secondes
        except Exception as e:
            write_log(f"Erreur dans le monitoring du seed {seed_id}: {str(e)}", "ERROR")
            time.sleep(5)

def stop_seed(seed_id):
    """Arrête un seed."""
    write_log(f"Arrêt du seed {seed_id}")
    
    try:
        with seeds_lock:
            if seed_id not in active_seeds:
                write_log(f"Seed {seed_id} introuvable", "WARNING")
                return False
            
            seed_data = active_seeds[seed_id]
            seed_data['is_active'] = False
            
            # Arrêter la session libtorrent
            if 'session' in seed_data and seed_data['session']:
                seed_data['session'].remove_torrent(seed_data['handle'])
            
            # Supprimer du dictionnaire
            del active_seeds[seed_id]
        
        save_persisted_seeds()
        write_log(f"Seed {seed_id} arrêté avec succès")
        return True
    except Exception as e:
        write_log(f"Erreur lors de l'arrêt du seed {seed_id}: {str(e)}", "ERROR")
        return False

def get_seed_stats(seed_id):
    """Retourne les statistiques d'un seed."""
    with seeds_lock:
        if seed_id in active_seeds:
            return active_seeds[seed_id]['stats']
    return None

def get_all_seeds():
    """Retourne la liste de tous les seeds actifs depuis le fichier de persistance (partagé entre workers)."""
    # Charger depuis le fichier JSON qui est partagé entre tous les workers Gunicorn
    # Au lieu de se baser sur active_seeds qui est en mémoire locale du worker
    persisted_seeds = load_persisted_seeds()
    
    seeds_list = []
    for seed_id, seed_info in persisted_seeds.items():
        # Vérifier si ce seed est géré par CE worker spécifiquement pour les stats en temps réel
        stats = {'uploaded': 0, 'upload_rate': 0, 'peers': 0}
        state = 'seeding'
        is_active = True
        
        with seeds_lock:
            if seed_id in active_seeds:
                # Ce worker gère ce seed, on peut avoir les stats en temps réel
                stats = active_seeds[seed_id]['stats']
                state = active_seeds[seed_id].get('state', 'seeding')
                is_active = active_seeds[seed_id]['is_active']
        
        seeds_list.append({
            'id': seed_id,
            'name': seed_info.get('name', 'Unknown'),
            'data_path': seed_info.get('data_path', ''),
            'is_active': is_active,
            'state': state,
            'stats': stats
        })
    
    return seeds_list

def restore_seeds():
    """Restaure les seeds persistés au démarrage."""
    # Acquérir un verrou sur un fichier pour éviter les restaurations multiples
    # (important avec Gunicorn qui lance plusieurs workers)
    lock_file = None
    try:
        # Créer le répertoire tmp s'il n'existe pas
        os.makedirs(os.path.dirname(SEEDS_RESTORE_LOCK_FILE), exist_ok=True)
        
        # Ouvrir le fichier de lock
        lock_file = open(SEEDS_RESTORE_LOCK_FILE, 'w')
        
        # Tenter d'acquérir un verrou exclusif non-bloquant
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError:
            # Un autre worker a déjà le lock, ne pas restaurer les seeds
            write_log("Un autre worker Gunicorn est déjà en train de restaurer les seeds, skip")
            return
        
        write_log("Ce worker Gunicorn restaure les seeds (lock acquis)")
        write_log("Restauration des seeds persistés")
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
    
    except Exception as e:
        write_log(f"Erreur globale lors de la restauration des seeds: {str(e)}", "ERROR")
    
    finally:
        # Libérer le verrou et fermer le fichier
        if lock_file:
            try:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                lock_file.close()
            except:
                pass
