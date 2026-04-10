import logging
logging.basicConfig(level=logging.INFO)

from flask import Flask, request, jsonify
import libtorrent as lt
import threading
import time
import os

app = Flask(__name__)

# =============================================================
# SESSION SEED : Liée au VPN (10.2.0.2) pour protéger l'identité lors du seeding
# =============================================================
session = lt.session()

def _read_natpmpc_port(port_file='/run/natpmpc-port'):
    try:
        with open(port_file) as f:
            port = int(f.read().strip())
            if 1024 <= port <= 65535:
                return port
    except Exception:
        pass
    return 0

_port = _read_natpmpc_port()
if _port == 0:
    logging.warning("[libtorrent_service] Port natpmpc non trouvé dans /run/natpmpc-port, libtorrent choisira un port aléatoire")
session.listen_on(_port, _port, '10.2.0.2')
logging.info("[libtorrent_service] Session écoute sur VPN port: %s (demandé: %s)", session.listen_port(), _port)

session.apply_settings({
    'download_rate_limit': 0,
    'upload_rate_limit': 0,
    'enable_dht': True,
    'enable_lsd': True,
    'enable_upnp': False,
    'enable_natpmp': False,
    'announce_to_all_trackers': True,
    'announce_to_all_tiers': True,
    'connections_limit': 1000,
    'connection_speed': 500,
    'unchoke_slots_limit': 20,
})
session.add_dht_router('router.bittorrent.com', 6881)
session.add_dht_router('router.utorrent.com', 6881)
session.add_dht_router('dht.transmissionbt.com', 6881)
session.add_dht_router('dht.libtorrent.org', 25401)

logging.info("[libtorrent_service] Session configurée (VPN, port %s)", session.listen_port())

seeds = {}  # id: handle
seeds_lock = threading.Lock()
downloads = {}  # id: {handle, started_at, save_path, torrent_path, name, is_active}
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

@app.route('/add_download', methods=['POST'])
def add_download():
    data = request.json
    download_id = data['download_id']
    torrent_path = data['torrent_path']
    save_path = data['save_path']
    resume_data = data.get('resume_data')

    try:
        info = lt.torrent_info(torrent_path)
        atp = lt.add_torrent_params()
        atp.ti = info
        atp.save_path = save_path
        if resume_data:
            atp.resume_data = bytes.fromhex(resume_data)
            logging.info(f"[API] Resume data chargé pour download {download_id}")

        handle = session.add_torrent(atp)
        handle.resume()

        with downloads_lock:
            downloads[download_id] = {
                'handle': handle,
                'started_at': time.time(),
                'save_path': save_path,
                'torrent_path': torrent_path,
                'name': info.name(),
                'is_active': True
            }
        logging.info(f"[API] Download ajouté: id={download_id}, name={info.name()}")
        return jsonify({'success': True, 'name': info.name()})
    except Exception as e:
        logging.error(f"[API] Erreur ajout download {download_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/remove_download', methods=['POST'])
def remove_download():
    data = request.json
    download_id = data['download_id']

    with downloads_lock:
        entry = downloads.get(download_id)
        if entry:
            handle = entry['handle']
            if handle.is_valid():
                session.remove_torrent(handle)
            downloads[download_id]['is_active'] = False
            del downloads[download_id]
            logging.info(f"[API] Download supprimé: id={download_id}")
            return jsonify({'success': True})

    return jsonify({'success': False, 'error': 'Download not found'}), 404

@app.route('/get_download_stats', methods=['GET'])
def get_download_stats():
    download_id = request.args.get('download_id')
    if not download_id:
        return jsonify({'success': False, 'error': 'download_id required'}), 400

    with downloads_lock:
        entry = downloads.get(download_id)
        if not entry:
            return jsonify({'success': False, 'error': 'Download not found'}), 404
        try:
            handle = entry['handle']
            if not handle.is_valid():
                return jsonify({'success': False, 'error': 'Invalid handle'}), 500
            s = handle.status()
            stats = {
                'name': entry['name'],
                'progress': s.progress * 100,
                'download_rate': s.download_rate,
                'upload_rate': s.upload_rate,
                'peers': s.num_peers,
                'seeds': s.num_seeds,
                'downloaded': s.total_download,
                'uploaded': s.total_upload,
                'state': str(s.state),
                'is_seeding': handle.is_seed(),
            }
            return jsonify({'success': True, 'stats': stats})
        except Exception as e:
            logging.error(f"[API] Erreur stats download {download_id}: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/get_all_downloads_stats', methods=['GET'])
def get_all_downloads_stats():
    result = {}
    with downloads_lock:
        for did, entry in downloads.items():
            try:
                handle = entry['handle']
                if not handle.is_valid():
                    continue
                s = handle.status()
                result[did] = {
                    'name': entry['name'],
                    'progress': round(s.progress * 100, 2),
                    'download_rate_kb': round(s.download_rate / 1024, 1),
                    'upload_rate_kb': round(s.upload_rate / 1024, 1),
                    'num_peers': s.num_peers,
                    'num_seeds': s.num_seeds,
                    'connect_candidates': s.connect_candidates,
                    'num_connections': s.num_connections,
                    'state': str(s.state),
                    'is_seeding': handle.is_seed(),
                    'seeders_in_swarm': s.num_complete,
                    'leechers_in_swarm': s.num_incomplete,
                }
            except Exception as e:
                result[did] = {'error': str(e)}
    return jsonify(result)

@app.route('/status', methods=['GET'])
def status():
    """Diagnostic de la session : port d'écoute, VPN, DHT, connexions"""
    try:
        s = session.status()
        port_file_content = None
        try:
            with open('/run/natpmpc-port') as f:
                port_file_content = f.read().strip()
        except Exception:
            port_file_content = 'FICHIER ABSENT'

        return jsonify({
            'listen_port': session.listen_port(),
            'natpmpc_port_file': port_file_content,
            'port_match': str(session.listen_port()) == port_file_content,
            'dht_nodes': s.dht_nodes,
            'has_incoming_connections': s.has_incoming_connections,
            'download_rate': s.download_rate,
            'upload_rate': s.upload_rate,
            'num_seeds_in_session': len(seeds),
            'num_downloads_in_session': len(downloads),
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5005, debug=True)