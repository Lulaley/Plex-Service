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
    try:
        info = lt.torrent_info(torrent_path)
        atp = {
            'ti': info,
            'save_path': data_path,
            'flags': lt.torrent_flags.upload_mode | lt.torrent_flags.seed_mode
        }
        handle = session.add_torrent(atp)
        with seeds_lock:
            seeds[seed_id] = handle
        logging.info(f"[API] Seed ajouté: id={seed_id}, name={info.name()}, path={data_path}")
        return jsonify({'success': True})
    except Exception as e:
        logging.error(f"[API] Erreur lors de l'ajout du seed {seed_id}: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/remove_seed', methods=['POST'])
def remove_seed():
    data = request.json
    seed_id = data['seed_id']
    with seeds_lock:
        handle = seeds.get(seed_id)
        if handle:
            session.remove_torrent(handle)
            del seeds[seed_id]
            logging.info(f"[API] Seed supprimé: id={seed_id}")
            return jsonify({'success': True})
    logging.warning(f"[API] Suppression seed: id={seed_id} introuvable")
    return jsonify({'success': False, 'error': 'Seed not found'})

@app.route('/get_stats', methods=['GET'])
def get_stats():
    stats = {}
    with seeds_lock:
        for seed_id, handle in seeds.items():
            s = handle.status()
            stats[seed_id] = {
                'name': handle.name(),
                'uploaded': s.total_upload,
                'upload_rate': s.upload_rate,
                'peers': s.num_peers,
                'seeds': s.num_seeds,
                'progress': s.progress * 100,
                'state': str(s.state)
            }
            logging.debug(f"[API] Stats seed {seed_id}: {stats[seed_id]}")
    logging.debug(f"[API] Stats seeds: {stats}")
    return jsonify(stats)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5005, debug=True)
