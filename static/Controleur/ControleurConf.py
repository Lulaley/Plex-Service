import configparser

class ControleurConf:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')

    def get_config(self, section, key):
        try:
            value = self.config.get(section, key)
            return value
        except configparser.NoSectionError:
            print(f"La section '{section}' n'existe pas dans le fichier de configuration.")
        except configparser.NoOptionError:
            print(f"La clé '{key}' n'existe pas dans la section '{section}' du fichier de configuration.")