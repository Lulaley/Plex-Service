# Variable globale pour stocker l'état du téléchargement
download_session = {
    'is_downloading': False,
    'handle': None,
    'save_path': None,
    'torrent_file_path': None,
    'downloaded_files': []  # Liste des fichiers téléchargés
}