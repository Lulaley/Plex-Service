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
session.listen_on(52415, 52415)
logging.info("[libtorrent_service] Libtorrent ecoute sur le port: %s", session.listen_port())
seeds = {}  # id: handle
seeds_lock = threading.Lock()

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

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5005, debug=True)
