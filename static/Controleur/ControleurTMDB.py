import tmdbsimple as tmdb

class ControllerTMDB:
    def __init__(self):
        tmdb.API_KEY = '2e1cdea4c5d37b09c615f5a708e2064b'
        tmdb.REQUESTS_TIMEOUT = (2, 5)  # seconds, for connect and read specifically
        
    def search_serie_name(self, title):
        search = tmdb.Search()
        search.tv(query=title)
        return search.results[0]['name']
    
    def search_movie_name(self, title):
        search = tmdb.Search()
        response =  search.movie(query=title)
        for s in search.results:
            print(s['title'])