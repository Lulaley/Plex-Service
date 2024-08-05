import libtorrent as lt
import time
import argparse

def main(torrent_file, save_path):

    ses = lt.session()

    print(f"Chargement du fichier .torrent pour {torrent_file}")
    info = lt.torrent_info(torrent_file)  # replace with your torrent file
    print(f"Chargement du fichier .torrent pour {torrent_file} terminé")
    h = ses.add_torrent({'ti': info, 'save_path': save_path})  # download to current directory
    print(f"Téléchargement du fichier .torrent pour {torrent_file} démarré")

    print('downloading', info.name())
    while not h.is_seed():
        s = h.status()
        print('%.2f%% complete (down: %.1f kB/s up: %.1f kB/s peers: %d) %s' % (
            s.progress * 100, s.download_rate / 1000, s.upload_rate / 1000,
            s.num_peers, s.state))
        time.sleep(1)

    print(info.name(), 'complete')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script de téléchargement")
    parser.add_argument('torrent_file', type=str, help='Le chemin vers le fichier torrent')
    parser.add_argument('save_path', type=str, help='Le chemin vers sabe_path')
    
    args = parser.parse_args()
    main(args.torrent_file, args.save_path)