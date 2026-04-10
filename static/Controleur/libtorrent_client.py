import requests

API_URL = 'http://127.0.0.1:5005'

def add_seed(seed_id, torrent_path, data_path, uploaded_offset=0):
    resp = requests.post(f'{API_URL}/add_seed', json={
        'seed_id': seed_id,
        'torrent_path': torrent_path,
        'data_path': data_path,
        'uploaded_offset': uploaded_offset
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

def add_download(download_id, torrent_path, save_path, resume_data=None):
    payload = {'download_id': download_id, 'torrent_path': torrent_path, 'save_path': save_path}
    if resume_data:
        payload['resume_data'] = resume_data
    try:
        resp = requests.post(f'{API_URL}/add_download', json=payload, timeout=30)
        return resp.json()
    except Exception as e:
        return {'success': False, 'error': str(e)}

def remove_download(download_id):
    try:
        resp = requests.post(f'{API_URL}/remove_download', json={'download_id': download_id}, timeout=10)
        return resp.json()
    except Exception as e:
        return {'success': False, 'error': str(e)}

def get_download_stats(download_id):
    try:
        resp = requests.get(f'{API_URL}/get_download_stats', params={'download_id': download_id}, timeout=5)
        return resp.json()
    except Exception as e:
        return {'success': False, 'error': str(e)}
