import requests
from .ControleurLog import write_log
from .ControleurConf import ControleurConf
import cloudscraper

class ControleurYGG:
    def __init__(self):
        self.scraper = cloudscraper.create_scraper()  # Utiliser cloudscraper pour contourner les protections Cloudflare
        self.cfduid = None
        self.cf_clearance = None
        self.conf = ControleurConf()
        self.torrent_link = None

    def login(self):
        login_url = self.conf.get_config('YGG', 'login_url')
        username = self.conf.get_config('YGG', 'username')
        password = self.conf.get_config('YGG', 'password')
        
        # Initial GET request to obtain cookies and headers
        response = self.scraper.get(login_url)
        
        # Check if the response contains the expected content
        if "Just a moment..." in response.text:
            write_log("Encountered bot protection. Additional steps may be required.")
            return False
        
        # Prepare login data
        login_data = {
            'id': username,
            'pass': password
        }
        
        # POST request to login
        login_response = self.scraper.post(login_url, data=login_data)
        
        if login_response.status_code == 200:
            write_log("Login successful")
            return True
        else:
            write_log("Login failed")
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