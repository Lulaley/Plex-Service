import requests

API_URL = 'http://127.0.0.1:5005'

def add_seed(seed_id, torrent_path, data_path):
    resp = requests.post(f'{API_URL}/add_seed', json={
        'seed_id': seed_id,
        'torrent_path': torrent_path,
        'data_path': data_path
    })
    return resp.json()

def remove_seed(seed_id):
    resp = requests.post(f'{API_URL}/remove_seed', json={
        'seed_id': seed_id
    })
    return resp.json()

def get_stats():
    resp = requests.get(f'{API_URL}/get_stats')
    return resp.json()
