import os
import re

def sanitize_filename(filename):
    """
    Nettoie un nom de fichier pour éviter les injections et caractères dangereux.
    """
    # Supprimer les caractères spéciaux dangereux
    filename = re.sub(r'[<>:"|?*\x00-\x1f]', '', filename)
    
    # Supprimer les séquences de traversée de répertoire
    filename = filename.replace('..', '')
    filename = filename.replace('/', '_')
    filename = filename.replace('\\', '_')
    
    # Limiter la longueur
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255-len(ext)] + ext
    
    return filename.strip()

def validate_path(path, allowed_base_paths):
    """
    Vérifie qu'un chemin est dans les répertoires autorisés.
    
    Args:
        path: Le chemin à valider
        allowed_base_paths: Liste des chemins de base autorisés
    
    Returns:
        True si le chemin est valide, False sinon
    """
    try:
        # Résoudre le chemin absolu
        abs_path = os.path.abspath(path)
        
        # Vérifier qu'il est dans un des répertoires autorisés
        for base_path in allowed_base_paths:
            abs_base = os.path.abspath(base_path)
            if abs_path.startswith(abs_base):
                return True
        
        return False
    except Exception:
        return False

def secure_join(base_path, *paths):
    """
    Joint des chemins de manière sécurisée en empêchant la traversée de répertoire.
    
    Args:
        base_path: Le répertoire de base
        *paths: Les sous-chemins à joindre
    
    Returns:
        Le chemin joint sécurisé ou None si invalide
    """
    try:
        # Nettoyer chaque composant
        clean_paths = [sanitize_filename(p) for p in paths]
        
        # Construire le chemin
        full_path = os.path.join(base_path, *clean_paths)
        
        # Vérifier qu'on reste dans le répertoire de base
        abs_full = os.path.abspath(full_path)
        abs_base = os.path.abspath(base_path)
        
        if abs_full.startswith(abs_base):
            return abs_full
        
        return None
    except Exception:
        return None
