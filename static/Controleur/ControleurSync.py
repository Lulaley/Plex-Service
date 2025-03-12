import os
from pymediainfo import MediaInfo  # pip install pymediainfo
from .ControleurLog import write_log  # Assurez-vous que cette importation est correcte

class ControleurSync:
    def __init__(self, directory):
        self.directory = directory
        self.file_info_list = []
        write_log(f"Initialisation de ControleurSync avec le répertoire: {directory}")

    def scan_directory(self):
        """
        Parcourt le répertoire et récupère les informations de chaque fichier MKV et AVI.
        """
        write_log(f"Début de la numérisation du répertoire: {self.directory}")
        for root, _, files in os.walk(self.directory):
            for file in files:
                if file.lower().endswith(('.mkv', '.avi')):
                    file_path = os.path.join(root, file)
                    write_log(f"Fichier trouvé: {file_path}")
                    self.extract_and_store_info(file_path)
        write_log("Numérisation du répertoire terminée")

    def extract_and_store_info(self, file_path):
        """
        Extrait les informations du fichier MKV ou AVI et les stocke dans une liste.
        """
        write_log(f"Extraction des informations pour le fichier: {file_path}")
        media_info = MediaInfo.parse(file_path)
        general_info = media_info.general_tracks[0]
        video_info = next((track for track in media_info.video_tracks), None)
        audio_tracks = media_info.audio_tracks
        subtitle_tracks = media_info.text_tracks

        # Convertir la résolution en qualité
        if video_info:
            width = video_info.width
            if width >= 3840:
                quality = '4k'
            elif width >= 2560:
                quality = '2k'
            elif width >= 1920:
                quality = '1080p'
            elif width >= 1280:
                quality = '720p'
            else:
                quality = 'SD'
        else:
            quality = 'Unknown'

        # Récupérer les langues audio
        audio_languages = [track.language for track in audio_tracks if track.language]

        # Récupérer les langues des sous-titres
        subtitle_languages = [track.language for track in subtitle_tracks if track.language]

        info = {
            'file_name': general_info.file_name,
            'duration': general_info.duration,
            'quality': quality,
            'audio_languages': audio_languages,
            'subtitle_languages': subtitle_languages
        }

        self.file_info_list.append({
            'file_path': file_path,
            'info': info
        })

        write_log(f"Informations extraites pour le fichier: {file_path} - {info}")

    def get_file_info_list(self):
        """
        Retourne la liste des informations des fichiers MKV et AVI.
        """
        write_log("Récupération de la liste des informations des fichiers MKV et AVI")
        return self.file_info_list