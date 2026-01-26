import redis
import json
import time
from .ControleurLog import write_log

class ControleurCache:
    """Gestionnaire de cache Redis pour optimiser les requêtes LDAP"""
    
    def __init__(self):
        try:
            self.redis_client = redis.Redis(
                host='localhost',
                port=6379,
                db=0,
                decode_responses=True,
                socket_connect_timeout=5
            )
            self.redis_client.ping()
            self.enabled = True
            write_log("Cache Redis initialisé avec succès")
        except (redis.ConnectionError, redis.TimeoutError) as e:
            write_log(f"Redis non disponible, cache désactivé: {e}", "WARNING")
            self.enabled = False
            self.redis_client = None
    
    def get(self, key):
        """Récupère une valeur du cache"""
        if not self.enabled:
            return None
        try:
            value = self.redis_client.get(key)
            if value:
                write_log(f"Cache HIT: {key}", "DEBUG")
                return json.loads(value)
            write_log(f"Cache MISS: {key}", "DEBUG")
            return None
        except Exception as e:
            write_log(f"Erreur lecture cache: {e}", "ERROR")
            return None
    
    def set(self, key, value, ttl=300):
        """Stocke une valeur dans le cache (TTL par défaut: 5 minutes)"""
        if not self.enabled:
            return False
        
        try:
            self.redis_client.setex(
                key,
                ttl,
                json.dumps(value)
            )
            write_log(f"Cache SET: {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            write_log(f"Erreur écriture cache: {e}", "ERROR")
            return False
    
    def delete(self, key):
        """Supprime une clé du cache"""
        if not self.enabled:
            return False
        
        try:
            self.redis_client.delete(key)
            write_log(f"Cache DELETE: {key}")
            return True
        except Exception as e:
            write_log(f"Erreur suppression cache: {e}", "ERROR")
            return False
    
    def invalidate_pattern(self, pattern):
        """Supprime toutes les clés correspondant au pattern (ex: user:*)"""
        if not self.enabled:
            return False
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
                write_log(f"Cache INVALIDATE: {len(keys)} clés supprimées ({pattern})")
            return True
        except Exception as e:
            write_log(f"Erreur invalidation cache: {e}", "ERROR")
            return False
    
    def clear_all(self):
        """Vide tout le cache (utiliser avec précaution !)"""
        if not self.enabled:
            return False
        
        try:
            self.redis_client.flushdb()
            write_log("Cache FLUSH: Toutes les clés supprimées", "WARNING")
            return True
        except Exception as e:
            write_log(f"Erreur flush cache: {e}", "ERROR")
            return False

# Instance globale
cache = ControleurCache()
