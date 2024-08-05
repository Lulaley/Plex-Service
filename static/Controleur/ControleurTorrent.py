import time
import requests
from PyBitTorrent import TorrentClient
from PyBitTorrent.Exceptions import OutOfPeers
from static.Controleur.ControleurLog import write_log

# Variable globale pour stocker l'état du téléchargement
download_status = {}

def download_torrent(torrent_file_path, save_path):
    import libtorrent as lt
    import time

    ses = lt.session()

    info = lt.torrent_info(torrent_file_path)  # replace with your torrent file
    h = ses.add_torrent({'ti': info, 'save_path': save_path})  # download to current directory

    print('downloading', info.name())
    while not h.is_seed():
        s = h.status()
        print('%.2f%% complete (down: %.1f kB/s up: %.1f kB/s peers: %d) %s' % (
            s.progress * 100, s.download_rate / 1000, s.upload_rate / 1000,
            s.num_peers, s.state))
        time.sleep(1)

    print(info.name(), 'complete')
