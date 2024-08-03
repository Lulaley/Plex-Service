import requests
from .ControleurLog import write_log
from .ControleurConf import ControleurConf
from selenium import webdriver #pip install selenium
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager #pip install webdriver_manager
import time

class ControleurYGG:
    def __init__(self):
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
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
            time.sleep(5)
            
            # Remplir les champs de connexion
            username_field = self.driver.find_element(By.NAME, 'id')
            password_field = self.driver.find_element(By.NAME, 'pass')
            username_field.send_keys(username)
            password_field.send_keys(password)
            
            # Soumettre le formulaire
            password_field.send_keys(Keys.RETURN)
            
            # Attendre que la connexion soit traitée
            time.sleep(5)
            
            # Vérifier si la connexion a réussi
            if "tableau de bord" in self.driver.page_source.lower():
                write_log("Login successful")
                return True
            else:
                write_log("Login failed")
                return False
        except Exception as e:
            write_log(f"Exception during login process: {e}")
            return False
        finally:
            self.driver.quit()
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