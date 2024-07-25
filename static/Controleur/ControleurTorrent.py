import time
import requests
from PyBitTorrent import TorrentClient
from static.Controleur.ControleurLog import write_log

def download_torrent(torrent_file_path, save_path):
    # Création d'une instance de TorrentClient
    client = TorrentClient()

    # Ajout du torrent et définition du chemin de sauvegarde
    torrent = client.add_torrent(torrent_file_path, save_path)

    write_log('Téléchargement en cours : {}'.format(torrent.name))
    while not torrent.is_finished:
        status = torrent.status()
        write_log('%.2f%% complet (téléchargement : %.1f kB/s, envoi : %.1f kB/s, pairs : %d)' % (
            status.progress * 100, status.download_rate / 1000, status.upload_rate / 1000,
            status.num_peers))
        send_download_info(torrent.name, status.progress * 100, status.download_rate / 1000, status.upload_rate / 1000, status.num_peers, status.state)
        time.sleep(1)

    write_log('{} terminé'.format(torrent.name))

    # Suppression du torrent de la session pour arrêter le partage
    client.remove_torrent(torrent)

def send_download_info(name, progress, download_rate, upload_rate, num_peers, state):
    url = 'http://localhost:5000/download_info'
    data = {
        'name': name,
        'progress': progress,
        'download_rate': download_rate,
        'upload_rate': upload_rate,
        'num_peers': num_peers,
        'state': state
    }
    response = requests.post(url, json=data)
    if response.status_code == 200:
        write_log('Informations de téléchargement envoyées avec succès')
    else:
        write_log('Erreur lors de l\'envoi des informations de téléchargement')