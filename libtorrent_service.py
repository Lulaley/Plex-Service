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
logging.info("[libtorrent_service] Port d'écoute BitTorrent fixé à 52414 (TCP/UDP)")
print("Libtorrent ecoute sur le port:", session.listen_port())
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
        return jsonify({'success': True})
    except Exception as e:
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
            return jsonify({'success': True})
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
    return jsonify(stats)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5005, debug=True)
