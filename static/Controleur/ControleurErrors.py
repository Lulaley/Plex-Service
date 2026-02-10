"""
Module de gestion uniforme des erreurs.
Fournit un décorateur et des handlers Flask pour logger les erreurs de manière cohérente.
"""
from functools import wraps
from flask import jsonify
from static.Controleur.ControleurLog import write_log
import traceback


def handle_errors(default_message="Une erreur est survenue"):
    """
    Décorateur pour gérer les erreurs de manière uniforme dans les routes Flask.
    
    Args:
        default_message (str): Message d'erreur générique à retourner à l'utilisateur
    
    Usage:
        @app.route('/my_route')
        @handle_errors("Erreur lors du traitement")
        def my_route():
            # code susceptible de lever des exceptions
            pass
    
    Returns:
        Décorateur qui wrap la fonction et gère les exceptions
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Log complet avec stack trace pour debug serveur
                error_msg = f"Erreur dans {func.__name__}: {str(e)}\n{traceback.format_exc()}"
                write_log(error_msg, "ERROR")
                
                # Réponse utilisateur sans détails sensibles
                return jsonify({
                    'success': False,
                    'message': default_message
                }), 500
        return wrapper
    return decorator


def register_error_handlers(app):
    """
    Enregistre les handlers d'erreurs globaux pour l'application Flask.
    
    Args:
        app: Instance Flask
    
    Usage:
        from static.Controleur.ControleurErrors import register_error_handlers
        app = Flask(__name__)
        register_error_handlers(app)
    """
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        """Handler global pour toutes les exceptions non gérées."""
        # Log détaillé serveur
        error_msg = f"Exception non gérée: {str(e)}\n{traceback.format_exc()}"
        write_log(error_msg, "ERROR")
        
        # Réponse utilisateur
        if app.debug:
            # Mode dev : montrer l'erreur complète
            return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500
        else:
            # Mode prod : message générique sécurisé
            return jsonify({'error': 'Erreur serveur interne'}), 500
    
    @app.errorhandler(404)
    def handle_404(e):
        """Handler pour les erreurs 404."""
        write_log(f"Erreur 404: {e} - URL: {e.description if hasattr(e, 'description') else 'unknown'}", "WARNING")
        return jsonify({'error': 'Page non trouvée'}), 404
    
    @app.errorhandler(403)
    def handle_403(e):
        """Handler pour les erreurs 403 Forbidden."""
        write_log(f"Erreur 403: Accès refusé", "WARNING")
        return jsonify({'error': 'Accès refusé'}), 403
    
    @app.errorhandler(500)
    def handle_500(e):
        """Handler pour les erreurs 500."""
        error_msg = f"Erreur 500: {str(e)}"
        write_log(error_msg, "ERROR")
        return jsonify({'error': 'Erreur serveur interne'}), 500
    
    write_log("Handlers d'erreurs globaux enregistrés")
