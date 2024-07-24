import sys
sys.path.append('/chemin/absolu/vers/Plex-Service/static')

from ControleurConf import ControleurConf
from ControleurLdap import ControleurLdap
from ControleurLog import write_log
from ControleurTorrent import download_torrent