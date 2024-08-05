from static.Controleur.ControleurLog import write_log
import libtorrent as lt
import time

# Variable globale pour stocker l'état du téléchargement
download_status = {}

def download_torrent(torrent_file_path, save_path):

    write_log(f"Ouverture de la session de téléchargement pour {torrent_file_path}")
    ses = lt.session()

    write_log(f"Chargement du fichier .torrent pour {torrent_file_path}")
    info = lt.torrent_info(torrent_file_path)  # replace with your torrent file
    write_log(f"Chargement du fichier .torrent pour {torrent_file_path} terminé")
    h = ses.add_torrent({'ti': info, 'save_path': save_path})  # download to current directory
    write_log(f"Téléchargement du fichier .torrent pour {torrent_file_path} démarré")

    write_log('downloading', info.name())
    while not h.is_seed():
        s = h.status()
        write_log('%.2f%% complete (down: %.1f kB/s up: %.1f kB/s peers: %d) %s' % (
            s.progress * 100, s.download_rate / 1000, s.upload_rate / 1000,
            s.num_peers, s.state))
        time.sleep(1)

    write_log(info.name(), 'complete')
    write_log(f"Téléchargement du fichier .torrent pour {torrent_file_path} terminé")
    ses.remove_torrent(h)
