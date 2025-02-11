import tmdbsimple as tmdb
from .ControleurLog import write_log
from .ControleurConf import ControleurConf

class ControleurTMDB:
    def __init__(self):
        conf = ControleurConf()
        tmdb.API_KEY = conf.get_config('TMDB', 'api_key')
        tmdb.REQUESTS_TIMEOUT = (2, 5)  # seconds, for connect and read specifically
        
    def search_serie_name(self, title):
        search = tmdb.Search()
        write_log(f"Recherche de la série {title} dans la base de données TMDB")
        search.tv(query=title)
        return search.results[0]['name']
    
    def search_movie_name(self, title):
        search = tmdb.Search()
        search.movie(query=title)
        for s in search.results:
            print(s['title'])