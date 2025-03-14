document.addEventListener('DOMContentLoaded', function () {
    const torrentForm = document.getElementById('torrent-form');
    const torrentFileInput = document.getElementById('torrent-file');
    const downloadButton = document.getElementById('download-button');

    let isDownloading = false;

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
        // Ajoutez ici le code pour démarrer le téléchargement
    }

    function stopDownload() {
        isDownloading = false;
        torrentFileInput.disabled = false;
        downloadButton.textContent = 'Lancer le téléchargement';
        fetch('/stop_download', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    console.log('Téléchargement annulé avec succès');
                } else {
                    console.error('Erreur lors de l\'annulation du téléchargement');
                }
            });
    }
});

document.getElementById('torrent-file').addEventListener('change', function (event) {
    var fileInfo = document.getElementById('file-info');
    var fileName = event.target.files[0] ? event.target.files[0].name : 'Aucun fichier sélectionné';
    fileInfo.textContent = 'Nom du fichier: ' + fileName;
});

document.getElementById('torrent-form').addEventListener('submit', function (event) {
    event.preventDefault();

    if (isDownloading) {
        return;
    }

    isDownloading = true;
    document.getElementById('download-button').disabled = true;
    document.getElementById('download-button').style.backgroundColor = "#ffb74a";
    document.getElementById('download-button').style.cursor = "not-allowed";

    var formData = new FormData();
    var fileInput = document.getElementById('torrent-file');
    formData.append('torrent-file', fileInput.files[0]);

    fetch('/upload', {
        method: 'POST',
        body: formData
    }).then(response => {
        if (response.ok) {
            var eventSource = new EventSource('/start_download');
            var progressBar = document.getElementById('progress-bar');
            var speedInfo = document.getElementById('speed-info');
            var uploadSpeedInfo = document.getElementById('upload-speed-info');
            var elapsedTimeElem = document.getElementById('elapsed-time');
            var remainingTimeElem = document.getElementById('remaining-time');
            var startTime = Date.now();
            var lastProgress = 0;

            eventSource.onmessage = function (event) {
                var logMessage = event.data;

                if (logMessage === 'done') {
                    progressBar.style.width = '100%';
                    progressBar.textContent = '100%';
                    speedInfo.textContent = 'Vitesse de téléchargement: 0 kB/s';
                    uploadSpeedInfo.textContent = 'Vitesse d\'upload: 0 kB/s';
                    remainingTimeElem.textContent = 'Temps restant: 0s';
                    eventSource.close();
                    isDownloading = false;
                    document.getElementById('download-button').disabled = false;
                    document.getElementById('download-button').style.backgroundColor = "";
                    document.getElementById('download-button').style.cursor = "";
                    return;
                }

                var progressMatch = logMessage.match(/(\d+\.\d+)% complete/);
                var downloadSpeedMatch = logMessage.match(/down: (\d+\.\d+ kB\/s)/);
                var uploadSpeedMatch = logMessage.match(/up: (\d+\.\d+ kB\/s)/);

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
                document.getElementById('download-button').disabled = false;
                document.getElementById('download-button').style.backgroundColor = "";
                document.getElementById('download-button').style.cursor = "";
            };
        } else {
            console.error('Erreur lors du téléchargement du fichier');
            isDownloading = false;
            document.getElementById('download-button').disabled = false;
            document.getElementById('download-button').style.backgroundColor = "";
            document.getElementById('download-button').style.cursor = "";
        }
    }).catch(error => {
        console.error('Erreur réseau ou autre:', error);
        isDownloading = false;
        document.getElementById('download-button').disabled = false;
        document.getElementById('download-button').style.backgroundColor = "";
        document.getElementById('download-button').style.cursor = "";
    });
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