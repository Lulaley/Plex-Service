import configparser
import os

class ControleurConf:
    def __init__(self):
        self.config = configparser.ConfigParser()
        # Construire le chemin relatif vers le fichier de configuration
        config_path = os.path.join(os.path.dirname(__file__), '..', 'Conf', 'config.ini')
        self.config.read(config_path)

    def get_config(self, section, key):
        try:
            value = self.config.get(section, key)
            return value
        except configparser.NoSectionError:
            print(f"La section '{section}' n'existe pas dans le fichier de configuration.")
        except configparser.NoOptionError:
            print(f"La clé '{key}' n'existe pas dans la section '{section}' du fichier de configuration.")