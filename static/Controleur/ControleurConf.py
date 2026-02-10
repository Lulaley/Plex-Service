import configparser
import os

class ControleurConf:
    _instance = None
    _config = None
    
    def __new__(cls):
        """Impl\u00e9mentation Singleton - une seule instance partag\u00e9e."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._config = configparser.ConfigParser()
            # Construire le chemin relatif vers le fichier de configuration
            config_path = os.path.join(os.path.dirname(__file__), '..', 'Conf', 'config.ini')
            cls._config.read(config_path)
        return cls._instance

    def get_config(self, section, key):
        try:
            value = self._config.get(section, key)
            return value
        except configparser.NoSectionError:
            print(f"La section '{section}' n'existe pas dans le fichier de configuration.")
        except configparser.NoOptionError:
            print(f"La clé '{key}' n'existe pas dans la section '{section}' du fichier de configuration.")