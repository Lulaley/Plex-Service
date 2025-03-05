import tmdbsimple as tmdb
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
        return search.results[0]

    def search_movie(self, title):
        search = tmdb.Search()
        write_log(f"Recherche du film {title} dans la base de données TMDB")
        search.movie(query=title, language='fr-FR')
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