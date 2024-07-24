import sys
sys.path.append('/chemin/absolu/vers/Plex-Service/static')

from Controleur.ControleurConf import ControleurConf
from Controleur.ControleurLog import write_log
from Controleur.ControleurLdap import ControleurLdap
from Controleur.ControleurTorrent import download_torrent
from Controleur.ControleurTorrent import send_download_info
