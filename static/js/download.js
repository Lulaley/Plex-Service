document.addEventListener('DOMContentLoaded', function () {
    const torrentForm = document.getElementById('torrent-form');
    const torrentFileInput = document.getElementById('torrent-file');
    const downloadButton = document.getElementById('download-button');
    const downloadIdInput = document.getElementById('download-id'); // Champ caché pour l'identifiant du téléchargement

    let isDownloading = false;
    let eventSource = null;

    // Au chargement de la page, vérifier s'il y a des téléchargements en cours
    checkActiveDownloads();

    function checkActiveDownloads() {
        fetch('/get_downloads')
            .then(response => response.json())
            .then(data => {
                if (data.success && data.downloads && data.downloads.length > 0) {
                    // Trouver le premier téléchargement actif
                    const activeDownload = data.downloads.find(dl => dl.is_active);
                    if (activeDownload) {
                        console.log('Téléchargement actif trouvé:', activeDownload);
                        // Se reconnecter au stream de ce téléchargement
                        reconnectToDownload(activeDownload);
                    }
                }
            })
            .catch(error => {
                console.error('Erreur lors de la vérification des téléchargements actifs:', error);
            });
    }

    function reconnectToDownload(downloadInfo) {
        isDownloading = true;
        torrentFileInput.disabled = true;
        downloadButton.textContent = 'Annuler le téléchargement';
        downloadIdInput.value = downloadInfo.download_id;

        // Afficher le nom du fichier
        var fileInfo = document.getElementById('file-info');
        fileInfo.textContent = 'Nom du fichier: ' + (downloadInfo.name || 'Téléchargement en cours');

        // Se connecter au stream du téléchargement existant
        const streamUrl = `/stream_download/${downloadInfo.download_id}`;
        console.log('Reconnexion au stream:', streamUrl);
        connectToStream(streamUrl);
    }

    torrentForm.addEventListener('submit', function (event) {
        event.preventDefault();
        if (isDownloading) {
            // Arrêter le téléchargement
            stopDownload();
        } else {
            // Démarrer le téléchargement
            startDownload();
        }
    });

    function startDownload() {
        isDownloading = true;
        torrentFileInput.disabled = true;
        downloadButton.textContent = 'Annuler le téléchargement';

        var formData = new FormData();
        var fileInput = document.getElementById('torrent-file');
        formData.append('torrent-file', fileInput.files[0]);

        fetch('/upload', {
            method: 'POST',
            body: formData
        }).then(response => {
            if (response.ok) {
                response.json().then(data => {
                    if (data.success) {
                        // Mettre à jour le champ caché avec l'identifiant du téléchargement
                        downloadIdInput.value = data.download_id;
                        
                        // Se connecter au stream
                        connectToStream(data.redirect_url);
                    } else {
                        console.error('Erreur lors du téléchargement');
                        isDownloading = false;
                        torrentFileInput.disabled = false;
                        downloadButton.textContent = 'Lancer le téléchargement';
                    }
                });
            }
        });
    }

    function connectToStream(streamUrl) {
        eventSource = new EventSource(streamUrl);
        var progressBar = document.getElementById('progress-bar');
        var speedInfo = document.getElementById('speed-info');
        var uploadSpeedInfo = document.getElementById('upload-speed-info');
        var elapsedTimeElem = document.getElementById('elapsed-time');
        var remainingTimeElem = document.getElementById('remaining-time');
        var startTime = Date.now();
        var lastProgress = 0;

        eventSource.onmessage = function (event) {
            var logMessage = event.data;

            if (logMessage === 'done' || logMessage === 'cancelled' || logMessage === 'not_found') {
                if (logMessage === 'done') {
                    progressBar.style.width = '100%';
                    progressBar.textContent = '100%';
                }
                speedInfo.textContent = 'Vitesse de téléchargement: 0 kB/s';
                uploadSpeedInfo.textContent = 'Vitesse d\'upload: 0 kB/s';
                remainingTimeElem.textContent = 'Temps restant: 0s';
                eventSource.close();
                isDownloading = false;
                downloadButton.textContent = 'Lancer le téléchargement';
                torrentFileInput.disabled = false;
                return;
            }

            var progressMatch = logMessage.match(/(\d+\.\d+)% complete/);
            var downloadSpeedMatch = logMessage.match(/down: (\d+\.\d+) kB\/s/);
            var uploadSpeedMatch = logMessage.match(/up: (\d+\.\d+) kB\/s/);

            if (progressMatch) {
                var progress = parseFloat(progressMatch[1]);
                progressBar.style.width = progress + '%';
                progressBar.textContent = progress.toFixed(2) + '%';

                var elapsedTime = (Date.now() - startTime) / 1000;
                elapsedTimeElem.textContent = 'Temps écoulé: ' + formatTime(elapsedTime);

                if (downloadSpeedMatch) {
                    var downloadSpeed = parseFloat(downloadSpeedMatch[1]);
                    speedInfo.textContent = 'Vitesse de téléchargement: ' + formatSpeed(downloadSpeed);
                }

                if (uploadSpeedMatch) {
                    var uploadSpeed = parseFloat(uploadSpeedMatch[1]);
                    uploadSpeedInfo.textContent = 'Vitesse d\'upload: ' + formatSpeed(uploadSpeed);
                }

                if (progress > lastProgress) {
                    var remainingTime = (elapsedTime / progress) * (100 - progress);
                    remainingTimeElem.textContent = 'Temps restant: ' + formatTime(remainingTime);
                    lastProgress = progress;
                }
            }
        };

        eventSource.onopen = function () {
            console.log('Connection opened');
        };

        eventSource.onerror = function () {
            console.log('Connection closed');
            eventSource.close();
            isDownloading = false;
            downloadButton.textContent = 'Lancer le téléchargement';
            torrentFileInput.disabled = false;
        };
    }

    function stopDownload() {
        isDownloading = false;
        torrentFileInput.disabled = false;
        downloadButton.textContent = 'Lancer le téléchargement';

        const downloadState = {
            download_id: downloadIdInput.value // Inclure l'identifiant du téléchargement
        };

        fetch('/stop_download', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(downloadState)
        })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                console.log('Téléchargement annulé avec succès');
                if (eventSource) {
                    eventSource.close();
                }
            } else {
                console.error('Erreur lors de l\'annulation du téléchargement');
            }
        })
        .catch(error => {
            console.error('Erreur réseau ou autre:', error);
        });
    }
});

document.getElementById('torrent-file').addEventListener('change', function (event) {
    var fileInfo = document.getElementById('file-info');
    var fileName = event.target.files[0] ? event.target.files[0].name : 'Aucun fichier sélectionné';
    fileInfo.textContent = 'Nom du fichier: ' + fileName;
});

function formatSpeed(speed) {
    if (speed < 1000) {
        return speed.toFixed(2) + ' kB/s';
    } else if (speed < 1000000) {
        return (speed / 1000).toFixed(2) + ' MB/s';
    } else {
        return (speed / 1000000).toFixed(2) + ' GB/s';
    }
}

function formatTime(seconds) {
    var hours = Math.floor(seconds / 3600);
    var minutes = Math.floor((seconds % 3600) / 60);
    var secs = Math.floor(seconds % 60);
    return (hours > 0 ? hours + 'h ' : '') + (minutes > 0 ? minutes + 'm ' : '') + secs + 's';
}

document.addEventListener('keydown', function (event) {
    if (event.key === 'Enter' && isDownloading) {
        event.preventDefault();
    }
});