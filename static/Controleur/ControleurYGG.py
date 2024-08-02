import requests
from .ControleurLog import write_log
from .ControleurConf import ControleurConf
import cloudscraper

class ControleurYGG:
    def __init__(self):
        self.session = requests.Session()
        self.cfduid = None
        self.cf_clearance = None
        self.conf = ControleurConf()
        self.torrent_link = None

    def login(self):
        try:
            url = self.conf.get_config('YGG', 'login_url')
            username = self.conf.get_config('YGG', 'username')
            password = self.conf.get_config('YGG', 'password')

            if not url or not username or not password:
                write_log("URL, nom d'utilisateur ou mot de passe manquant dans la configuration.")
                return False

            write_log("Tentative de connexion à YGG...")

            # Utiliser cloudscraper pour gérer les protections Cloudflare
            scraper = cloudscraper.create_scraper()

            # Perform the initial request to get the Cloudflare cookies
            write_log("Récupération des cookies Cloudflare...")
            try:
                response = scraper.get(url)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                write_log(f"Erreur lors de la requête HTTPS: {e}")
                return False

            write_log(f"Code de statut de la récupération des cookies: {response.status_code}")
            write_log(f"Reponse de la récupération des cookies: {response.text}")

            # Extract the required cookies from the response
            cookies = response.cookies.get_dict()
            write_log(f"Cookies extraits: {cookies}")

            # Extract the '__cfduid' and 'cf_clearance' cookies
            self.cfduid = cookies.get('__cfduid')
            self.cf_clearance = cookies.get('cf_clearance')

            if not self.cfduid or not self.cf_clearance:
                write_log("Les cookies nécessaires n'ont pas été trouvés.")
                return False

            write_log(f"Debut de la connexion avec les cookies: __cfduid={self.cfduid}, cf_clearance={self.cf_clearance}")

            # Perform the login request with the required cookies and authentication data
            response = scraper.post(url, data={'id': username, 'pass': password}, cookies={'__cfduid': self.cfduid, 'cf_clearance': self.cf_clearance})
            write_log(f"Reponse de la connexion: {response.text}")

            # Check if the login was successful based on the response
            if response.status_code == 200 and 'Authentication failed' not in response.text:
                write_log("Connexion réussie.")
                return True
            else:
                write_log("Échec de la connexion.")
                return False

        except requests.exceptions.RequestException as e:
            write_log(f"Erreur lors de la requête: {e}")
            return False
        except Exception as e:
            write_log(f"Erreur inattendue: {e}")
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