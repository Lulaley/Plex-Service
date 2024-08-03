import requests
from .ControleurLog import write_log
from .ControleurConf import ControleurConf
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

class ControleurYGG:
    def __init__(self):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.binary_location = "/usr/bin/google-chrome"  # Spécifiez le chemin de l'exécutable Chrome
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--headless")  # Exécuter Chrome en mode headless
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--remote-debugging-port=9222")
        
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        self.conf = ControleurConf()
        self.torrent_link = None

    def login(self):
        try:
            login_url = self.conf.get_config('YGG', 'login_url')
            username = self.conf.get_config('YGG', 'username')
            password = self.conf.get_config('YGG', 'password')
            
            write_log("Tentative de connexion à YGG via Selenium...")
            self.driver.get(login_url)
            
            # Attendre que la page se charge et que les champs de connexion soient disponibles
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, 'id'))
            )
            
            write_log("Page de connexion chargée.")
            # Remplir les champs de connexion
            username_field = self.driver.find_element(By.NAME, 'id')
            password_field = self.driver.find_element(By.NAME, 'pass')
            username_field.send_keys(username)
            password_field.send_keys(password)
            
            write_log("Soumission du formulaire de connexion...")
            # Soumettre le formulaire
            password_field.submit()
            
            write_log("Attente de la page de connexion...")
            # Vérifier si la connexion a réussi
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
            if "tableau de bord" in self.driver.page_source.lower():
                write_log("Login successful")
                return True
            else:
                write_log("Login failed")
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