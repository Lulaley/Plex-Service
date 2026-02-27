def update_seed_stats_in_db(seed_id, info):
    """Met à jour les stats d'un seed dans SQLite à partir des infos API."""
    try:
        with get_db() as db:
            db.execute("""
                UPDATE seeds SET
                    uploaded_size = ?,
                    upload_rate = ?,
                    peers = ?,
                    status = ?,
                    updated_at = ?
                WHERE id = ?
            """, (
                info.get('uploaded', 0),
                info.get('upload_rate', 0),
                info.get('peers', 0),
                info.get('state', 'seeding'),
                datetime.now().isoformat(),
                seed_id
            ))
        return True
    except Exception as e:
        write_log(f"Erreur update_seed_stats_in_db pour {seed_id}: {e}", "ERROR")
        return False
def delete_seed_from_db(seed_id):
    """Supprime un seed de la table seeds dans SQLite."""
    try:
        with get_db() as db:
            db.execute("DELETE FROM seeds WHERE id = ?", (seed_id,))
        write_log(f"Seed {seed_id} supprimé de la BDD")
        return True
    except Exception as e:
        write_log(f"Erreur suppression seed SQL: {e}", "ERROR")
        return False
def deduplicate_seeds_in_db():
    """Supprime les doublons dans la table seeds (garde le plus récent par data_path)."""
    try:
        with get_db() as db:
            # Supprime tous les seeds qui ne sont pas le plus récent pour chaque data_path
            db.execute("""
                DELETE FROM seeds
                WHERE id NOT IN (
                    SELECT id FROM (
                        SELECT id, data_path, MAX(updated_at) OVER (PARTITION BY data_path) as max_updated
                        FROM seeds
                    )
                    WHERE updated_at = max_updated
                )
            """)
        write_log("Déduplication des seeds terminée (un seul par data_path, le plus récent gardé)")
        return True
    except Exception as e:
        write_log(f"Erreur déduplication seeds: {e}", "ERROR")
        return False
def get_all_seeds_from_sql():
    """Retourne la liste de tous les seeds (actifs ou non) depuis SQLite, formatée pour l'interface."""
    try:
        seeds_list = []
        with get_db() as db:
            cursor = db.execute("SELECT * FROM seeds")
            seen_names = set()
            for row in cursor.fetchall():
                name = row['torrent_name']
                if name in seen_names:
                    continue  # Ignore les doublons de nom
                seen_names.add(name)
                stats = {
                    'uploaded': row['uploaded_size'],
                    'upload_rate': row['upload_rate'],
                    'peers': row['peers'],
                    'state': row['status'],
                    'progress': 100
                }
                seeds_list.append({
                    'id': row['id'],
                    'name': name,
                    'data_path': row['data_path'],
                    'is_active': row['status'] == 'seeding',
                    'state': row['status'],
                    'stats': stats
                })
        return seeds_list
    except Exception as e:
        write_log(f"Erreur get_all_seeds_from_sql: {e}", "ERROR")
        return []
"""
ControleurDatabase - Gestion de la base de données SQLite pour downloads/seeds
Supporte la migration bidirectionnelle JSON ↔ SQLite
"""

import sqlite3
import json
import os
from contextlib import contextmanager
from datetime import datetime
from static.Controleur.ControleurConf import ControleurConf
from static.Controleur.ControleurLog import write_log

conf = ControleurConf()

# Chemin de la base de données
DB_PATH = conf.get_config('BDD', 'db_path')
DOWNLOADS_JSON_PATH = "/var/www/public/Plex-Service/tmp/active_downloads.json"
SEEDS_JSON_PATH = "/var/www/public/Plex-Service/tmp/active_seeds.json"


@contextmanager
def get_db():
    """Context manager pour connexions SQLite thread-safe"""
    # Créer le dossier si nécessaire
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=10.0)
    conn.row_factory = sqlite3.Row  # Accès par nom de colonne
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        write_log(f"Erreur transaction SQLite: {e}", "ERROR")
        raise
    finally:
        conn.close()


def init_database():
    """Initialise les tables de la base de données"""
    with get_db() as db:
        # Table des downloads
        db.execute("""
            CREATE TABLE IF NOT EXISTS downloads (
                id TEXT PRIMARY KEY,
                torrent_name TEXT NOT NULL,
                torrent_path TEXT NOT NULL,
                save_path TEXT NOT NULL,
                username TEXT NOT NULL,
                status TEXT NOT NULL,
                progress REAL DEFAULT 0,
                total_size INTEGER DEFAULT 0,
                downloaded_size INTEGER DEFAULT 0,
                upload_rate REAL DEFAULT 0,
                download_rate REAL DEFAULT 0,
                peers INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                started_at TIMESTAMP,
                finished_at TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table des seeds
        db.execute("""
            CREATE TABLE IF NOT EXISTS seeds (
                id TEXT PRIMARY KEY,
                torrent_name TEXT NOT NULL,
                torrent_path TEXT NOT NULL,
                data_path TEXT NOT NULL,
                username TEXT NOT NULL,
                status TEXT NOT NULL,
                uploaded_size INTEGER DEFAULT 0,
                upload_rate REAL DEFAULT 0,
                peers INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                stopped_at TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Index pour requêtes rapides
        db.execute("CREATE INDEX IF NOT EXISTS idx_downloads_status ON downloads(status)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_downloads_user ON downloads(username)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_seeds_status ON seeds(status)")
        
        write_log("Tables SQLite initialisées avec succès")


def use_sql_mode():
    """Vérifie si le mode SQL est activé dans la config"""
    try:
        return conf.get_config('BDD', 'sql').lower() == 'true'
    except Exception:
        return False


def get_json_last_modified(json_path):
    """Retourne le timestamp de dernière modification du fichier JSON"""
    try:
        if os.path.exists(json_path):
            return os.path.getmtime(json_path)
        return 0
    except Exception:
        return 0


def get_sql_last_modified(table_name):
    """Retourne le timestamp de dernière modification dans SQLite"""
    try:
        with get_db() as db:
            cursor = db.execute(f"""
                SELECT MAX(updated_at) as last_update 
                FROM {table_name}
            """)
            row = cursor.fetchone()
            if row and row['last_update']:
                dt = datetime.fromisoformat(row['last_update'])
                return dt.timestamp()
        return 0
    except Exception:
        return 0


def migrate_json_to_sql_downloads():
    """Migre les downloads depuis JSON vers SQLite"""
    try:
        if not os.path.exists(DOWNLOADS_JSON_PATH):
            write_log("Aucun fichier JSON downloads à migrer")
            return True
        
        with open(DOWNLOADS_JSON_PATH, 'r') as f:
            downloads_data = json.load(f)
        
        if not downloads_data:
            write_log("Fichier JSON downloads vide, rien à migrer")
            return True
        
        migrated_count = 0
        with get_db() as db:
            for download_id, data in downloads_data.items():
                stats = data.get('stats', {})
                
                db.execute("""
                    INSERT OR REPLACE INTO downloads 
                    (id, torrent_name, torrent_path, save_path, username, status,
                     progress, total_size, downloaded_size, upload_rate, download_rate,
                     peers, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    download_id,
                    data.get('name', 'Unknown'),
                    data.get('torrent_path', ''),
                    data.get('save_path', ''),
                    data.get('username', 'unknown'),
                    'downloading' if data.get('is_active', True) else 'stopped',
                    stats.get('progress', 0),
                    stats.get('total_size', 0),
                    stats.get('downloaded_size', 0),
                    stats.get('upload_rate', 0),
                    stats.get('download_rate', 0),
                    stats.get('peers', 0),
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
                migrated_count += 1
        
        write_log(f"Migration JSON→SQL: {migrated_count} downloads migrés")
        return True
        
    except Exception as e:
        write_log(f"Erreur migration JSON→SQL downloads: {e}", "ERROR")
        return False


def migrate_sql_to_json_downloads():
    """Migre les downloads depuis SQLite vers JSON"""
    try:
        downloads_data = {}
        
        with get_db() as db:
            cursor = db.execute("""
                SELECT * FROM downloads 
                WHERE status IN ('downloading', 'seeding')
            """)
            
            for row in cursor.fetchall():
                downloads_data[row['id']] = {
                    'id': row['id'],
                    'name': row['torrent_name'],
                    'torrent_path': row['torrent_path'],
                    'save_path': row['save_path'],
                    'username': row['username'],
                    'is_active': row['status'] in ('downloading', 'seeding'),
                    'stats': {
                        'progress': row['progress'],
                        'total_size': row['total_size'],
                        'downloaded_size': row['downloaded_size'],
                        'upload_rate': row['upload_rate'],
                        'download_rate': row['download_rate'],
                        'peers': row['peers'],
                        'state': row['status']
                    }
                }
        
        os.makedirs(os.path.dirname(DOWNLOADS_JSON_PATH), exist_ok=True)
        with open(DOWNLOADS_JSON_PATH, 'w') as f:
            json.dump(downloads_data, f, indent=4)
        
        write_log(f"Migration SQL→JSON: {len(downloads_data)} downloads exportés")
        return True
        
    except Exception as e:
        write_log(f"Erreur migration SQL→JSON downloads: {e}", "ERROR")
        return False


def migrate_json_to_sql_seeds():
    """Migre les seeds depuis JSON vers SQLite"""
    try:
        if not os.path.exists(SEEDS_JSON_PATH):
            write_log("Aucun fichier JSON seeds à migrer")
            return True
        
        with open(SEEDS_JSON_PATH, 'r') as f:
            seeds_data = json.load(f)
        
        if not seeds_data:
            write_log("Fichier JSON seeds vide, rien à migrer")
            return True
        
        migrated_count = 0
        with get_db() as db:
            for seed_id, data in seeds_data.items():
                # Correction : toujours transmettre le chemin du .torrent depuis 'torrent_file_path' si présent, sinon 'torrent_path'
                torrent_path = data.get('torrent_file_path') or data.get('torrent_path', '')
                db.execute("""
                    INSERT OR REPLACE INTO seeds 
                    (id, torrent_name, torrent_path, data_path, username, status,
                     uploaded_size, upload_rate, peers, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    seed_id,
                    data.get('name', 'Unknown'),
                    torrent_path,
                    data.get('data_path', ''),
                    data.get('username', 'unknown'),
                    'seeding' if data.get('is_active', True) else 'stopped',
                    data.get('uploaded_size', 0),
                    data.get('upload_rate', 0),
                    data.get('peers', 0),
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
                migrated_count += 1
        
        write_log(f"Migration JSON→SQL: {migrated_count} seeds migrés")
        return True
        
    except Exception as e:
        write_log(f"Erreur migration JSON→SQL seeds: {e}", "ERROR")
        return False


def migrate_sql_to_json_seeds():
    """Migre les seeds depuis SQLite vers JSON"""
    try:
        seeds_data = {}
        
        with get_db() as db:
            cursor = db.execute("""
                SELECT * FROM seeds 
                WHERE status = 'seeding'
            """)
            
            for row in cursor.fetchall():
                seeds_data[row['id']] = {
                    'id': row['id'],
                    'name': row['torrent_name'],
                    'torrent_path': row['torrent_path'],
                    'data_path': row['data_path'],
                    'username': row['username'],
                    'is_active': row['status'] == 'seeding',
                    'uploaded_size': row['uploaded_size'],
                    'upload_rate': row['upload_rate'],
                    'peers': row['peers']
                }
        
        os.makedirs(os.path.dirname(SEEDS_JSON_PATH), exist_ok=True)
        with open(SEEDS_JSON_PATH, 'w') as f:
            json.dump(seeds_data, f, indent=4)
        
        write_log(f"Migration SQL→JSON: {len(seeds_data)} seeds exportés")
        return True
        
    except Exception as e:
        write_log(f"Erreur migration SQL→JSON seeds: {e}", "ERROR")
        return False


def sync_on_mode_change():
    """
    Synchronise automatiquement les données lors du changement de mode.
    Détecte quelle version est la plus récente et migre vers le nouveau mode.
    """
    sql_mode = use_sql_mode()
    
    # Initialiser la BDD si mode SQL
    if sql_mode:
        init_database()
    
    # Vérifier les timestamps pour downloads
    json_time = get_json_last_modified(DOWNLOADS_JSON_PATH)
    sql_time = get_sql_last_modified('downloads')
    
    write_log(f"Sync downloads: JSON={json_time}, SQL={sql_time}, Mode={'SQL' if sql_mode else 'JSON'}")
    
    if sql_mode and json_time > sql_time and json_time > 0:
        # Mode SQL activé, mais JSON plus récent → migrer JSON vers SQL
        write_log("JSON downloads plus récent, migration JSON→SQL")
        migrate_json_to_sql_downloads()
    elif not sql_mode and sql_time > json_time and sql_time > 0:
        # Mode JSON activé, mais SQL plus récent → migrer SQL vers JSON
        write_log("SQL downloads plus récent, migration SQL→JSON")
        migrate_sql_to_json_downloads()
    
    # Vérifier les timestamps pour seeds
    json_time = get_json_last_modified(SEEDS_JSON_PATH)
    sql_time = get_sql_last_modified('seeds')
    
    write_log(f"Sync seeds: JSON={json_time}, SQL={sql_time}, Mode={'SQL' if sql_mode else 'JSON'}")
    
    if sql_mode and json_time > sql_time and json_time > 0:
        # Mode SQL activé, mais JSON plus récent → migrer JSON vers SQL
        write_log("JSON seeds plus récent, migration JSON→SQL")
        migrate_json_to_sql_seeds()
    elif not sql_mode and sql_time > json_time and sql_time > 0:
        # Mode JSON activé, mais SQL plus récent → migrer SQL vers JSON
        write_log("SQL seeds plus récent, migration SQL→JSON")
        migrate_sql_to_json_seeds()


# ========== FONCTIONS D'ACCÈS SQL ==========

def save_download_to_db(download_id, handle):
    def delete_download_from_db(download_id):
        """Supprime un téléchargement de la BDD SQLite."""
        try:
            with get_db() as db:
                db.execute("DELETE FROM downloads WHERE id = ?", (download_id,))
            return True
        except Exception as e:
            write_log(f"Erreur suppression download SQL: {e}", "ERROR")
            return False
    """Sauvegarde un download dans SQLite"""
    try:
        with get_db() as db:
            stats = handle.get('stats', {})
            
            # Statut robuste : 'downloading' tant que progress < 100, 'completed' sinon
            progress = stats.get('progress', 0)
            is_downloading = stats.get('is_downloading', False)
            if progress >= 100 and not is_downloading:
                status = 'completed'
            else:
                status = 'downloading'
            db.execute("""
                INSERT OR REPLACE INTO downloads 
                (id, torrent_name, torrent_path, save_path, username, status,
                 progress, total_size, downloaded_size, upload_rate, download_rate,
                 peers, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                download_id,
                handle.get('name', 'Unknown'),
                handle.get('torrent_file_path', ''),
                handle.get('save_path', ''),
                handle.get('username', 'unknown'),
                status,
                progress,
                stats.get('total_size', 0),
                stats.get('downloaded_size', 0),
                stats.get('upload_rate', 0),
                stats.get('download_rate', 0),
                stats.get('peers', 0),
                datetime.now().isoformat()
            ))
        return True
    except Exception as e:
        write_log(f"Erreur sauvegarde download SQL: {e}", "ERROR")
        return False


def load_downloads_from_db():
    """Charge tous les downloads actifs depuis SQLite"""
    try:
        downloads = {}
        with get_db() as db:
            cursor = db.execute("""
                SELECT * FROM downloads 
                WHERE status IN ('downloading', 'seeding')
            """)
            
            for row in cursor.fetchall():
                downloads[row['id']] = {
                    'id': row['id'],
                    'name': row['torrent_name'],
                    'torrent_path': row['torrent_path'],
                    'save_path': row['save_path'],
                    'username': row['username'],
                    'is_active': True,
                    'stats': {
                        'progress': row['progress'],
                        'total_size': row['total_size'],
                        'downloaded_size': row['downloaded_size'],
                        'upload_rate': row['upload_rate'],
                        'download_rate': row['download_rate'],
                        'peers': row['peers'],
                        'state': row['status']
                    }
                }
        return downloads
    except Exception as e:
        write_log(f"Erreur chargement downloads SQL: {e}", "ERROR")
        return {}


def save_seed_to_db(seed_id, data):
    """Sauvegarde un seed dans SQLite"""
    try:
        with get_db() as db:
            # Correction : toujours renseigner le chemin du .torrent
            torrent_path = data.get('torrent_file_path') or data.get('torrent_path', '')
            db.execute("""
                INSERT OR REPLACE INTO seeds 
                (id, torrent_name, torrent_path, data_path, username, status,
                 uploaded_size, upload_rate, peers, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                seed_id,
                data.get('name', 'Unknown'),
                torrent_path,
                data.get('data_path', ''),
                data.get('username', 'unknown'),
                'seeding' if data.get('is_active', True) else 'stopped',
                data.get('uploaded_size', 0),
                data.get('upload_rate', 0),
                data.get('peers', 0),
                datetime.now().isoformat()
            ))
        return True
    except Exception as e:
        write_log(f"Erreur sauvegarde seed SQL: {e}", "ERROR")
        return False


def load_seeds_from_db():
    """Charge tous les seeds actifs depuis SQLite"""
    try:
        seeds = {}
        with get_db() as db:
            cursor = db.execute("""
                SELECT * FROM seeds 
                WHERE status = 'seeding'
            """)
            
            for row in cursor.fetchall():
                seeds[row['id']] = {
                    'id': row['id'],
                    'name': row['torrent_name'],
                    'torrent_path': row['torrent_path'],
                    'data_path': row['data_path'],
                    'username': row['username'],
                    'is_active': True,
                    'uploaded_size': row['uploaded_size'],
                    'upload_rate': row['upload_rate'],
                    'peers': row['peers']
                }
        return seeds
    except Exception as e:
        write_log(f"Erreur chargement seeds SQL: {e}", "ERROR")
        return {}
