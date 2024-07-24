# Plex-Service


## Mise en place du service pour le site web
### Création d'un service :

[Unit]
Description=Server Python Plex Service
After=network.target

[Service]
User=root

WorkingDirectory='chemin du projet git'
ExecStart=/usr/bin/python3 app.py

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target

Fichier à écrire dans '/etc/systemd/system/'

### Redémarrage des services daemon :
systemctl daemon-reload

### Démarrage et Arrêt du service web Plex :
systemctl start 'le nom du fichier'
systemctl stop 'le nom du fichier'