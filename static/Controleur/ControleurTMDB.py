import tmdbsimple as tmdb
import re
from .ControleurLog import write_log
from .ControleurConf import ControleurConf

class ControleurTMDB:
    def __init__(self):
        conf = ControleurConf()
        tmdb.API_KEY = conf.get_config('TMDB', 'api_key')
        tmdb.REQUESTS_TIMEOUT = (2, 5)  # seconds, for connect and read specifically

    def search_serie(self, title):
        search = tmdb.Search()
        write_log(f"Recherche de la série {title} dans la base de données TMDB")
        search.tv(query=title, language='fr-FR')
        
        if not search.results:
            write_log(f"Aucune série trouvée pour '{title}', tentative en anglais", "WARNING")
            search.tv(query=title, language='en-US')
        
        # Si toujours aucun résultat et qu'il y a une date entre parenthèses, réessayer sans la date
        if not search.results:
            title_without_date = re.sub(r'\s*\(\d{4}\)\s*', ' ', title).strip()
            if title_without_date != title:
                write_log(f"Aucune série trouvée, tentative sans la date: '{title_without_date}'", "WARNING")
                search.tv(query=title_without_date, language='fr-FR')
                
                if not search.results:
                    write_log(f"Tentative en anglais sans la date", "WARNING")
                    search.tv(query=title_without_date, language='en-US')
        
        if not search.results:
            write_log(f"Aucune série trouvée pour '{title}' sur TMDB", "ERROR")
            raise ValueError(f"Aucune série trouvée pour '{title}'")
        
        return search.results[0]

    def search_movie(self, title):
        search = tmdb.Search()
        write_log(f"Recherche du film {title} dans la base de données TMDB")
        search.movie(query=title, language='fr-FR')
        
        if not search.results:
            write_log(f"Aucun film trouvé pour '{title}', tentative en anglais", "WARNING")
            search.movie(query=title, language='en-US')
        
        # Si toujours aucun résultat et qu'il y a une date entre parenthèses, réessayer sans la date
        if not search.results:
            title_without_date = re.sub(r'\s*\(\d{4}\)\s*', ' ', title).strip()
            if title_without_date != title:
                write_log(f"Aucun film trouvé, tentative sans la date: '{title_without_date}'", "WARNING")
                search.movie(query=title_without_date, language='fr-FR')
                
                if not search.results:
                    write_log(f"Tentative en anglais sans la date", "WARNING")
                    search.movie(query=title_without_date, language='en-US')
        
        if not search.results:
            write_log(f"Aucun film trouvé pour '{title}' sur TMDB", "ERROR")
            raise ValueError(f"Aucun film trouvé pour '{title}'")
        
        return search.results[0]

    def search_all_series(self, title):
        search = tmdb.Search()
        write_log(f"Recherche de toutes les séries correspondant à {title} dans la base de données TMDB")
        response = search.tv(query=title, language='fr-FR')
        return response['results']

    def search_all_movies(self, title):
        search = tmdb.Search()
        write_log(f"Recherche de tous les films correspondant à {title} dans la base de données TMDB")
        response = search.movie(query=title, language='fr-FR')
        return response['results']