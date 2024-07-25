import time
import requests
from Controleur.ControleurLog import write_log
from pyBitTorrent import BTLT

def download_torrent(torrent_file_path, save_path):
    ses = BTLT.Session()
    h = ses.add_torrent(torrent_file_path, save_path)

    write_log('Téléchargement en cours : {}'.format(h.name()))
    while not h.is_seed():
        s = h.status()
        write_log('%.2f%% complet (téléchargement : %.1f kB/s, envoi : %.1f kB/s, pairs : %d) %s' % (
            s.progress * 100, s.download_rate / 1000, s.upload_rate / 1000,
            s.num_peers, s.state))
        send_download_info(h.name(), s.progress * 100, s.download_rate / 1000, s.upload_rate / 1000, s.num_peers, s.state)
        time.sleep(1)

    write_log('{} terminé'.format(h.name()))

    ses.remove_torrent(h)  # Stop seeding the torrent

# Exemple d'utilisation
torrent_file_path = '/chemin/vers/votre/fichier.torrent'
save_path = '/chemin/vers/votre/dossier/de/destination'
download_torrent(torrent_file_path, save_path)

# Fonction pour envoyer les informations de téléchargement à l'application Flask
def send_download_info(name, progress, download_rate, upload_rate, num_peers, state):
    url = 'http://localhost:5000/download_info'  # Remplacez par l'URL de votre application Flask
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
