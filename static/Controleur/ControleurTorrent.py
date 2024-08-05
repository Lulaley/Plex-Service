import time
import requests
from PyBitTorrent import TorrentClient , 
from static.Controleur.ControleurLog import write_log

# Variable globale pour stocker l'état du téléchargement
download_status = {}

def download_torrent(torrent_file_path, save_path):
    global download_status
    # Création d'une instance de TorrentClient avec l'argument requis
    torrent = TorrentClient(torrent_file_path, output_dir=save_path)

    torrent.start()
    # Ajout du torrent et définition du chemin de sauvegarde
    #torrent = client.add_torrent(torrent_file_path, save_path)
    
    write_log('Téléchargement en cours : {}'.format(torrent.name))
    while not torrent.is_done():
        status = torrent.status()
        write_log('%.2f%% complet (téléchargement : %.1f kB/s, envoi : %.1f kB/s, pairs : %d)' % (
            status.progress * 100, status.download_rate / 1000, status.upload_rate / 1000,
            status.num_peers))
        send_download_info(torrent.name, status.progress * 100, status.download_rate / 1000, status.upload_rate / 1000, status.num_peers, status.state)
        
        # Mise à jour de l'état du téléchargement
        download_status = {
            'name': torrent.name,
            'progress': status.progress * 100,
            'download_rate': status.download_rate / 1000,
            'upload_rate': status.upload_rate / 1000,
            'num_peers': status.num_peers,
            'state': status.state
        }
        
        time.sleep(1)

    write_log('{} terminé'.format(torrent.name))

    # Suppression du torrent de la session pour arrêter le partage
    torrent.remove()

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