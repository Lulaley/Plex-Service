import libtorrent as lt
import threading
from .ControleurLog import write_log

# Session globale unique pour libtorrent
_session = None
_session_lock = threading.Lock()

def get_libtorrent_session():
    """
    Retourne la session libtorrent globale unique.
    Thread-safe : crée la session une seule fois.
    """
    global _session
    
    if _session is None:
        with _session_lock:
            # Double-check locking pattern
            if _session is None:
                write_log("Création de la session libtorrent globale unique")
                _session = lt.session()
                
                # Configuration par défaut
                settings = {
                    'download_rate_limit': -1,  # Pas de limite de téléchargement
                    'upload_rate_limit': -1,    # Pas de limite d'upload
                    'alert_mask': lt.alert.category_t.all_categories,
                }
                _session.apply_settings(settings)
                write_log("Session libtorrent configurée avec succès")
    
    return _session

def configure_session_for_download():
    """Configure la session pour les téléchargements (upload et download)."""
    ses = get_libtorrent_session()
    settings = {
        'download_rate_limit': -1,  # Téléchargement illimité
        'upload_rate_limit': -1,    # Upload illimité
    }
    ses.apply_settings(settings)
    return ses

def configure_session_for_seed():
    """Configure la session pour le seeding uniquement (pas de download)."""
    ses = get_libtorrent_session()
    settings = {
        'download_rate_limit': 0,   # Pas de téléchargement
        'upload_rate_limit': -1,    # Upload illimité
    }
    ses.apply_settings(settings)
    return ses

def cleanup_session():
    """Nettoie proprement la session libtorrent au shutdown."""
    global _session
    if _session is not None:
        write_log("Fermeture de la session libtorrent")
        # Les torrents seront automatiquement pausés
        _session = None
