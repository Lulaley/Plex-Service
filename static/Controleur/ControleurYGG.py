import requests
from .ControleurLog import write_log
from .ControleurConf import ControleurConf
import cfscrape
import pickle
import os

class ControleurYGG:
    def __init__(self):
        write_log("Initialisation de ControleurYGG")
        self.scraper = cfscrape.create_scraper()
        write_log("Scraper cfscrape créé")
        self.conf = ControleurConf()
        write_log("Configuration chargée")
        self.torrent_link = None

    def load_cookies(self, cookies_file):
        write_log(f"Chargement des cookies depuis le fichier: {cookies_file}")
        if not os.path.exists(cookies_file):
            write_log(f"Le fichier {cookies_file} n'existe pas. Création d'un nouveau fichier de cookies.")
            self.save_cookies(cookies_file)
        try:
            with open(cookies_file, 'rb') as f:
                cookies = pickle.load(f)
                for cookie in cookies:
                    self.scraper.cookies.set(cookie['name'], cookie['value'], domain=cookie['domain'])
            write_log("Cookies chargés avec succès")
        except Exception as e:
            write_log(f"Erreur lors du chargement des cookies: {e}")
            raise

    def save_cookies(self, cookies_file):
        write_log(f"Sauvegarde des cookies dans le fichier: {cookies_file}")
        try:
            cookies = self.scraper.cookies
            with open(cookies_file, 'wb') as f:
                pickle.dump(cookies, f)
            write_log("Cookies sauvegardés avec succès")
        except Exception as e:
            write_log(f"Erreur lors de la sauvegarde des cookies: {e}")
            raise

    def login(self):
        try:
            login_url = self.conf.get_config('YGG', 'login_url')
            username = self.conf.get_config('YGG', 'username')
            password = self.conf.get_config('YGG', 'password')
            
            write_log("Début de la tentative de connexion")
            write_log(f"URL de connexion: {login_url}")
            write_log(f"Nom d'utilisateur: {username}")
            
            # Charger les cookies de session
            self.load_cookies('cookies.pkl')
            
            # Effectuer la requête de connexion
            login_data = {
                'id': username,
                'pass': password
            }
            response = self.scraper.post(login_url, data=login_data)
            
            if response.status_code == 200 and "tableau de bord" in response.text.lower():
                write_log("Connexion réussie.")
                self.save_cookies('cookies.pkl')
                return True
            else:
                write_log(f"Échec de la connexion. Statut: {response.status_code}, Réponse: {response.text}")
                return False
        except Exception as e:
            write_log(f"Erreur lors de la connexion : {e}")
            raise

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