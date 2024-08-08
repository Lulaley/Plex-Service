document.getElementById('torrent-file').addEventListener('change', function (event) {
    var fileInfo = document.getElementById('file-info');
    var fileName = event.target.files[0] ? event.target.files[0].name : 'Aucun fichier sélectionné';
    fileInfo.textContent = 'Nom du fichier: ' + fileName;
});

document.getElementById('torrent-form').addEventListener('submit', function (event) {
    event.preventDefault(); // Empêche le comportement par défaut du formulaire

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

            eventSource.onmessage = function (event) {
                var logMessage = event.data;
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

                    var remainingTime = (100 - progress) / (progress / elapsedTime);
                    remainingTimeElem.textContent = 'Temps restant estimé: ' + formatTime(remainingTime);
                }
            };

            eventSource.onerror = function (error) {
                console.error('Erreur de l\'EventSource:', error);
                eventSource.close();
                alert('Erreur lors du téléchargement du fichier .torrent. Veuillez vérifier les logs du serveur pour plus de détails.');
            };
        } else {
            alert('Erreur lors du téléchargement du fichier .torrent. Réponse du serveur non OK.');
        }
    }).catch(error => {
        console.error('Erreur:', error);
        alert('Erreur lors du téléchargement du fichier .torrent. Veuillez vérifier votre connexion réseau et réessayer.');
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