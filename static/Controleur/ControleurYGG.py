import requests
from .ControleurLog import write_log
from .ControleurConf import ControleurConf

class ControleurYGG:
    def __init__(self):
        self.session = requests.Session()
        self.cfduid = None
        self.cf_clearance = None
        self.conf = ControleurConf()
        self.torrent_link = None

    def login(self):
        url = self.conf.get_config('YGG', 'login_url')
        username = self.conf.get_config('YGG', 'username')
        password = self.conf.get_config('YGG', 'password')

        write_log("Tentative de connexion à YGG...")

        # Perform the initial request to get the Cloudflare cookies
        response = self.session.get(url)

        # Extract the required cookies from the response
        cookies = response.cookies.get_dict()

        # Extract the '__cfduid' and 'cf_clearance' cookies
        self.cfduid = cookies.get('__cfduid')
        self.cf_clearance = cookies.get('cf_clearance')

        write_log(f"Debut de la connexion avec les cookies: __cfduid={self.cfduid}, cf_clearance={self.cf_clearance}")
        # Perform the login request with the required cookies and authentication data
        response = self.session.post(url, data={'id': username, 'pass': password}, cookies={'__cfduid': self.cfduid, 'cf_clearance': self.cf_clearance})
        write_log(f"Reponse de la connexion: {response.text}")
        # Check if the login was successful based on the response
        if response.status_code == 200 and 'Authentication failed' not in response.text:
            write_log("Connexion réussie.")
            return True
        else:
            write_log("Échec de la connexion.")
            return False

    def search(self, titre, uploader=None, categorie=None, sous_categorie=None):
        search_url = self.conf.get_config('YGG', 'search_url')
        write_log(f"Recherche de '{titre}' sur YGG...")

        # Formuler les paramètres de la requête de recherche
        params = {'name': titre, 'description': '', 'file': '', 'do': 'search'}
        if uploader:
            params['uploader'] = uploader
        if categorie:
            params['category'] = categorie
        if sous_categorie:
            params['sub_category'] = sous_categorie

        # Effectuer la requête de recherche avec les paramètres
        response = self.session.get(search_url, params=params, cookies={'__cfduid': self.cfduid, 'cf_clearance': self.cf_clearance})
    
        if response.status_code == 200:
            write_log("Recherche réussie.")
            return response.text
        else:
            write_log("Échec de la recherche.")
            return None

    def load(self, torrent_link):
        self.torrent_link = torrent_link
        write_log(f"Lien du torrent chargé : {self.torrent_link}")

    def download(self):
        if self.torrent_link:
            write_log(f"Téléchargement du torrent depuis {self.torrent_link}...")
            response = self.session.get(self.torrent_link, cookies={'__cfduid': self.cfduid, 'cf_clearance': self.cf_clearance})
            if response.status_code == 200:
                with open('downloaded_torrent.torrent', 'wb') as f:
                    f.write(response.content)
                write_log("Torrent téléchargé avec succès.")
            else:
                write_log("Échec du téléchargement du torrent.")
        else:
            write_log("Aucun lien de torrent chargé.")