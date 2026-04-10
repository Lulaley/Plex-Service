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

# ========== FONCTIONS POUR DOWNLOADS ==========

def add_download(download_id, torrent_path, save_path, resume_data=None):
    """
    Démarre un nouveau téléchargement via l'API libtorrent
    
    Args:
        download_id: ID unique du téléchargement
        torrent_path: Chemin vers le fichier .torrent
        save_path: Chemin où sauvegarder les fichiers téléchargés
        resume_data: Resume data optionnel (hex string) pour reprendre un téléchargement
    
    Returns:
        dict: {'success': bool, 'name': str, 'error': str}
    """
    payload = {
        'download_id': download_id,
        'torrent_path': torrent_path,
        'save_path': save_path
    }
    
    if resume_data:
        payload['resume_data'] = resume_data
    
    try:
        resp = requests.post(f'{API_URL}/add_download', json=payload, timeout=30)
        return resp.json()
    except Exception as e:
        return {'success': False, 'error': str(e)}

def remove_download(download_id, save_resume=True):
    """
    Arrête et supprime un téléchargement
    
    Args:
        download_id: ID du téléchargement à supprimer
        save_resume: Si True, sauvegarde les resume data pour reprendre plus tard
    
    Returns:
        dict: {'success': bool, 'resume_data': str (hex), 'error': str}
    """
    try:
        resp = requests.post(f'{API_URL}/remove_download', json={
            'download_id': download_id,
            'save_resume': save_resume
        }, timeout=10)
        return resp.json()
    except Exception as e:
        return {'success': False, 'error': str(e)}

def get_download_stats(download_id):
    """
    Récupère les statistiques d'un téléchargement spécifique
    
    Args:
        download_id: ID du téléchargement
    
    Returns:
        dict: {'success': bool, 'stats': dict, 'error': str}
    """
    try:
        resp = requests.get(f'{API_URL}/get_download_stats', params={'download_id': download_id}, timeout=5)
        return resp.json()
    except Exception as e:
        return {'success': False, 'error': str(e)}

def get_all_downloads():
    """
    Récupère les statistiques de tous les téléchargements actifs
    
    Returns:
        dict: {'success': bool, 'downloads': dict, 'error': str}
    """
    try:
        resp = requests.get(f'{API_URL}/get_all_downloads', timeout=5)
        return resp.json()
    except Exception as e:
        return {'success': False, 'error': str(e)}
