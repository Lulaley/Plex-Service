import logging
logging.basicConfig(level=logging.INFO)

from flask import Flask, request, jsonify
import libtorrent as lt
import threading
import time
import os

app = Flask(__name__)

# Session libtorrent unique
session = lt.session()

def _read_natpmpc_port(port_file='/run/natpmpc-port'):
    try:
        with open(port_file) as f:
            port = int(f.read().strip())
            if 1024 <= port <= 65535:
                return port
    except Exception:
        pass
    return 0  # 0 = libtorrent choisit automatiquement

_port = _read_natpmpc_port()
session.listen_on(_port, _port, '10.2.0.2')
logging.info("[libtorrent_service] Libtorrent ecoute sur le port: %s", session.listen_port())
seeds = {}  # id: handle
seeds_lock = threading.Lock()
downloads = {}  # id: {handle, started_at, save_path, torrent_path, ...}
downloads_lock = threading.Lock()

@app.route('/add_seed', methods=['POST'])
def add_seed():
    data = request.json
    torrent_path = data['torrent_path']
    data_path = data['data_path']
    seed_id = data['seed_id']
    # Offset pour préserver le total uploadé entre redémarrages
    uploaded_offset = data.get('uploaded_offset', 0)
    try:
        info = lt.torrent_info(torrent_path)
        atp = {
            'ti': info,
            'save_path': data_path,
            'flags': lt.torrent_flags.upload_mode | lt.torrent_flags.seed_mode
        }
        handle = session.add_torrent(atp)
        with seeds_lock:
            seeds[seed_id] = {'handle': handle, 'uploaded_offset': uploaded_offset}
        logging.info(f"[API] Seed ajouté: id={seed_id}, name={info.name()}, path={data_path}, offset={uploaded_offset}")
        return jsonify({'success': True})
    except Exception as e:
        logging.error(f"[API] Erreur lors de l'ajout du seed {seed_id}: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/remove_seed', methods=['POST'])
def remove_seed():
    data = request.json
    seed_id = data['seed_id']
    with seeds_lock:
        seed_entry = seeds.get(seed_id)
        if seed_entry:
            handle = seed_entry['handle']
            session.remove_torrent(handle)
            del seeds[seed_id]
            logging.info(f"[API] Seed supprimé: id={seed_id}")
            return jsonify({'success': True})
    logging.warning(f"[API] Suppression seed: id={seed_id} introuvable")
    return jsonify({'success': False, 'error': 'Seed not found'})

@app.route('/get_stats', methods=['GET'])
def get_stats():
    stats = {}
    invalid_ids = []
    with seeds_lock:
        for seed_id, seed_entry in seeds.items():
            try:
                handle = seed_entry['handle']
                uploaded_offset = seed_entry.get('uploaded_offset', 0)
                if not handle.is_valid():
                    logging.warning(f"[API] Handle invalide pour seed {seed_id}, ignoré")
                    invalid_ids.append(seed_id)
                    continue
                s = handle.status()
                stats[seed_id] = {
                    'name': handle.name(),
                    'uploaded': s.total_upload + uploaded_offset,  # Préserve le total entre redémarrages
                    'upload_rate': s.upload_rate,
                    'peers': s.num_peers,
                    'seeds': s.num_seeds,
                    'progress': s.progress * 100,
                    'state': str(s.state)
                }
                logging.debug(f"[API] Stats seed {seed_id}: {stats[seed_id]}")
            except Exception as e:
                logging.error(f"[API] Erreur stats seed {seed_id}: {e}")
                invalid_ids.append(seed_id)
        # Nettoyer les handles invalides
        for seed_id in invalid_ids:
            if seed_id in seeds:
                del seeds[seed_id]
                logging.info(f"[API] Handle invalide supprimé: {seed_id}")
    logging.debug(f"[API] Stats seeds: {stats}")
    return jsonify(stats)

# ========== ENDPOINTS POUR DOWNLOADS ==========

@app.route('/add_download', methods=['POST'])
def add_download():
    """Démarre un nouveau téléchargement via l'API"""
    data = request.json
    download_id = data['download_id']
    torrent_path = data['torrent_path']
    save_path = data['save_path']
    resume_data = data.get('resume_data')  # Resume data optionnel
    
    try:
        info = lt.torrent_info(torrent_path)
        atp = {
            'ti': info,
            'save_path': save_path
        }
        
        # Si des resume_data sont fournis, les utiliser
        if resume_data:
            atp['resume_data'] = bytes.fromhex(resume_data)
            logging.info(f"[API] Resume data chargé pour download {download_id}")
        
        handle = session.add_torrent(atp)
        
        with downloads_lock:
            downloads[download_id] = {
                'handle': handle,
                'started_at': time.time(),
                'save_path': save_path,
                'torrent_path': torrent_path,
                'name': info.name(),
                'is_active': True
            }
        
        logging.info(f"[API] Download ajouté: id={download_id}, name={info.name()}, save_path={save_path}")
        return jsonify({'success': True, 'name': info.name()})
        
    except Exception as e:
        logging.error(f"[API] Erreur lors de l'ajout du download {download_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/remove_download', methods=['POST'])
def remove_download():
    """Arrête et supprime un téléchargement"""
    data = request.json
    download_id = data['download_id']
    save_resume = data.get('save_resume', True)  # Par défaut, sauvegarder les resume data
    
    with downloads_lock:
        download_entry = downloads.get(download_id)
        if download_entry:
            handle = download_entry['handle']
            
            # Sauvegarder les resume data si demandé
            resume_data_hex = None
            if save_resume and handle.is_valid():
                try:
                    resume_data = handle.save_resume_data()
                    resume_data_hex = resume_data.hex()
                    logging.info(f"[API] Resume data sauvegardé pour download {download_id}")
                except Exception as e:
                    logging.error(f"[API] Erreur sauvegarde resume data pour {download_id}: {e}")
            
            session.remove_torrent(handle)
            downloads[download_id]['is_active'] = False
            del downloads[download_id]
            
            logging.info(f"[API] Download supprimé: id={download_id}")
            return jsonify({'success': True, 'resume_data': resume_data_hex})
    
    logging.warning(f"[API] Suppression download: id={download_id} introuvable")
    return jsonify({'success': False, 'error': 'Download not found'}), 404

@app.route('/get_download_stats', methods=['GET'])
def get_download_stats():
    """Récupère les statistiques d'un téléchargement spécifique"""
    download_id = request.args.get('download_id')
    
    if not download_id:
        return jsonify({'success': False, 'error': 'download_id required'}), 400
    
    with downloads_lock:
        download_entry = downloads.get(download_id)
        if not download_entry:
            return jsonify({'success': False, 'error': 'Download not found'}), 404
        
        try:
            handle = download_entry['handle']
            if not handle.is_valid():
                return jsonify({'success': False, 'error': 'Invalid handle'}), 500
            
            s = handle.status()
            stats = {
                'name': download_entry['name'],
                'progress': s.progress * 100,
                'download_rate': s.download_rate,
                'upload_rate': s.upload_rate,
                'peers': s.num_peers,
                'seeds': s.num_seeds,
                'downloaded': s.total_download,
                'uploaded': s.total_upload,
                'state': str(s.state),
                'is_seeding': handle.is_seed(),
                'save_path': download_entry['save_path'],
                'started_at': download_entry['started_at']
            }
            return jsonify({'success': True, 'stats': stats})
            
        except Exception as e:
            logging.error(f"[API] Erreur stats download {download_id}: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/get_all_downloads', methods=['GET'])
def get_all_downloads():
    """Récupère les statistiques de tous les téléchargements actifs"""
    all_stats = {}
    invalid_ids = []
    
    with downloads_lock:
        for download_id, download_entry in downloads.items():
            try:
                handle = download_entry['handle']
                if not handle.is_valid():
                    logging.warning(f"[API] Handle invalide pour download {download_id}, ignoré")
                    invalid_ids.append(download_id)
                    continue
                
                s = handle.status()
                all_stats[download_id] = {
                    'name': download_entry['name'],
                    'progress': s.progress * 100,
                    'download_rate': s.download_rate,
                    'upload_rate': s.upload_rate,
                    'peers': s.num_peers,
                    'seeds': s.num_seeds,
                    'downloaded': s.total_download,
                    'uploaded': s.total_upload,
                    'state': str(s.state),
                    'is_seeding': handle.is_seed(),
                    'save_path': download_entry['save_path'],
                    'started_at': download_entry['started_at']
                }
                
            except Exception as e:
                logging.error(f"[API] Erreur stats download {download_id}: {e}")
                invalid_ids.append(download_id)
        
        # Nettoyer les handles invalides
        for download_id in invalid_ids:
            if download_id in downloads:
                del downloads[download_id]
                logging.info(f"[API] Handle invalide supprimé: {download_id}")
    
    return jsonify({'success': True, 'downloads': all_stats})

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5005, debug=True)
