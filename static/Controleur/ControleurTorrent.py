import time
import requests
from PyBitTorrent import TorrentClient
from PyBitTorrent.Exceptions import OutOfPeers
from static.Controleur.ControleurLog import write_log

# Variable globale pour stocker l'état du téléchargement
download_status = {}

def download_torrent(torrent_file_path, save_path):
    global download_status
    # Création d'une instance de TorrentClient avec l'argument requis
    torrent = TorrentClient(torrent_file_path, output_dir=save_path)

    try:
        status = torrent.start()
        write_log(f'Téléchargement du torrent {status} démarré')
        

        #write_log('{} terminé'.format(torrent.name))

        # Suppression du torrent de la session pour arrêter le partage
        torrent.remove()

    except OutOfPeers:
        write_log('Erreur : Plus de pairs disponibles pour le téléchargement du torrent.')
        download_status = {
            'name': torrent_file_path,
            'progress': 0,
            'download_rate': 0,
            'upload_rate': 0,
            'num_peers': 0,
            'state': 'Erreur : Plus de pairs disponibles'
        }

    # Réinitialisation de l'état du téléchargement
    download_status = {}

def send_download_info(name, progress, download_rate, upload_rate, num_peers, state):
    url = 'http://localhost:5001/download_info'
    data = {
        'name': name,
        'progress': progress,
        'download_rate': download_rate,
        'upload_rate': upload_rate,
        'num_peers': num_peers,
        'state': state
    }
    requests.post(url, json=data)

def get_download_status():
    global download_status
    return download_status