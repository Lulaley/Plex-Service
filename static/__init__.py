import os
import sys
chemin_actuel = os.path.dirname(__file__)
chemin_static = os.path.join(chemin_actuel, '../static')
sys.path.append(chemin_static)

from Controleur.ControleurConf import ControleurConf
from Controleur.ControleurLog import write_log
from Controleur.ControleurLdap import ControleurLdap
from Controleur.ControleurTorrent import download_torrent
from Controleur.ControleurTorrent import send_download_info
