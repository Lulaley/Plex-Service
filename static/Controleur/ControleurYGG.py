import requests
from .ControleurLog import write_log
from .ControleurConf import ControleurConf
import cloudscraper
import time

class ControleurYGG:
    def __init__(self):
        self.scraper = cloudscraper.create_scraper()  # Utiliser cloudscraper pour contourner les protections Cloudflare
        self.cfduid = None
        self.cf_clearance = None
        self.conf = ControleurConf()
        self.torrent_link = None

    def login(self):
        try:
            login_url = self.conf.get_config('YGG', 'login_url')
            username = self.conf.get_config('YGG', 'username')
            password = self.conf.get_config('YGG', 'password')
            
            # Initial GET request to obtain cookies and headers
            write_log("Tentative de connexion à YGG...")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Referer': login_url,
                'Origin': login_url
            }
            response = self.scraper.get(login_url, headers=headers)
            
            write_log("Cookies et headers obtenus.")
            # Check if the response contains the expected content
            if "Just a moment..." in response.text:
                write_log("Encountered bot protection. Additional steps may be required.")
                # Extract cookies and headers from the response
                write_log("Extracting cookies and headers...")
                self.cfduid = response.cookies.get('__cfduid')
                self.cf_clearance = response.cookies.get('cf_clearance')
                headers.update(response.headers)
                
                # Wait for a few seconds before retrying
                write_log("Waiting for 5 seconds before retrying...")
                time.sleep(5)
                
                # Retry the GET request with the extracted cookies and headers
                write_log("Retrying GET request with extracted cookies and headers...")
                try:
                    response = self.scraper.get(login_url, cookies=response.cookies, headers=headers)
                except Exception as e:
                    write_log(f"Exception during retry GET request: {e}")
                    return False
                
                if "Just a moment..." in response.text:
                    write_log("Bot protection still encountered. Login failed.")
                    return False
            
            write_log("Connexion en cours...")
            # Prepare login data
            login_data = {
                'id': username,
                'pass': password
            }
            
            write_log("Envoi de la requête de connexion...")
            # POST request to login
            login_response = self.scraper.post(login_url, data=login_data, headers=headers, cookies=response.cookies)
            
            write_log(f"Login response status code: {login_response.status_code}")
            if login_response.status_code == 200:
                write_log("Login successful")
                return True
            else:
                write_log(f"Login failed with status code: {login_response.status_code}")
                try:
                    write_log(f"Decoding response text...")
                    response_text = login_response.text.encode('utf-8').decode('utf-8')
                except UnicodeDecodeError:
                    write_log("Response contains non-text content")
                    response_text = "Response contains non-text content"
                #write_log(f"Response text: {response_text}")
                return False
        except Exception as e:
            write_log(f"Exception during login process: {e}")
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
            params['subcategory'] = sous_categorie

        # Envoyer la requête de recherche
        try:
            response = self.scraper.get(search_url, params=params, headers=headers, cookies=response.cookies)
            if response.status_code == 200:
                write_log("Recherche réussie")
                return response.json()
            else:
                write_log(f"Recherche échouée avec le code de statut: {response.status_code}")
                return None
        except Exception as e:
            write_log(f"Exception pendant la recherche: {e}")
            return None

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