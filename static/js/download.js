document.addEventListener('DOMContentLoaded', function () {
    const torrentForm = document.getElementById('torrent-form');
    const torrentFileInput = document.getElementById('torrent-file');
    const downloadButton = document.getElementById('download-button');
    const downloadIdInput = document.getElementById('download-id');
    const uploadZone = document.getElementById('upload-zone');
    const downloadInfoCard = document.getElementById('download-info-card');

    let isDownloading = false;
    let eventSource = null;

    // Gestion du drag & drop
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        uploadZone.addEventListener(eventName, () => {
            uploadZone.classList.add('dragover');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        uploadZone.addEventListener(eventName, () => {
            uploadZone.classList.remove('dragover');
        }, false);
    });

    uploadZone.addEventListener('drop', function(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0 && files[0].name.endsWith('.torrent')) {
            torrentFileInput.files = files;
            updateFileInfo(files[0].name);
        }
    }, false);

    // Clic sur la zone d'upload
    uploadZone.addEventListener('click', function(e) {
        e.stopPropagation();
        if (!isDownloading) {
            torrentFileInput.click();
        }
    });

    // Au chargement de la page, vérifier s'il y a des téléchargements en cours
    checkActiveDownloads();

    function checkActiveDownloads() {
        fetch('/get_downloads')
            .then(response => response.json())
            .then(data => {
                if (data.success && data.downloads && data.downloads.length > 0) {
                    const activeDownload = data.downloads.find(dl => dl.is_active);
                    if (activeDownload) {
                        console.log('Téléchargement actif trouvé:', activeDownload);
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
        uploadZone.classList.add('downloading');
        downloadButton.classList.add('cancel');
        downloadButton.innerHTML = '<span class="btn-icon">■</span><span class="btn-text">Annuler le téléchargement</span>';
        downloadIdInput.value = downloadInfo.download_id;

        // Mettre à jour le nom du fichier dans la zone d'upload
        const fileName = downloadInfo.name || 'Téléchargement en cours';
        updateFileInfo(fileName);
        
        // Afficher la carte d'infos et mettre à jour le nom
        downloadInfoCard.style.display = 'block';
        document.getElementById('file-info').textContent = fileName;

        const streamUrl = `/stream_download/${downloadInfo.download_id}`;
        console.log('Reconnexion au stream:', streamUrl);
        connectToStream(streamUrl, downloadInfo.progress || 0);
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
        downloadButton.classList.add('cancel');
        downloadButton.innerHTML = '<span class="btn-icon">■</span><span class="btn-text">Annuler le téléchargement</span>';

        // Afficher la carte d'informations
        downloadInfoCard.style.display = 'block';

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
                        downloadIdInput.value = data.download_id;
                        connectToStream(data.redirect_url);
                    } else {
                        console.error('Erreur lors du téléchargement');
                        resetDownloadUI();
                    }
                });
            }
        });
    }

    function resetDownloadUI() {
        isDownloading = false;
        torrentFileInput.disabled = false;
        downloadButton.classList.remove('cancel');
        downloadButton.innerHTML = '<span class="btn-icon">▶</span><span class="btn-text">Lancer le téléchargement</span>';
        downloadInfoCard.style.display = 'none';
    }

    function updateFileInfo(fileName) {
        const uploadText = document.querySelector('.upload-text');
        const uploadSubtext = document.querySelector('.upload-subtext');
        if (uploadText && uploadSubtext) {
            uploadText.textContent = fileName;
            uploadText.style.color = '#333';
            uploadSubtext.textContent = 'Fichier sélectionné';
            uploadSubtext.style.color = '#22c55e';
        }
    }

    function connectToStream(streamUrl, initialProgress = 0) {
        eventSource = new EventSource(streamUrl);
        var progressBar = document.getElementById('progress-bar');
        var progressText = progressBar.querySelector('.progress-text');
        var progressPercentage = document.getElementById('progress-percentage');
        var speedInfo = document.getElementById('speed-info');
        var uploadSpeedInfo = document.getElementById('upload-speed-info');
        var elapsedTimeElem = document.getElementById('elapsed-time');
        var remainingTimeElem = document.getElementById('remaining-time');
        var startTime = Date.now();
        var lastProgress = initialProgress;
        var progressHistory = [];
        var lastProgressUpdate = Date.now();

        eventSource.onmessage = function (event) {
            var logMessage = event.data;

            if (logMessage === 'done' || logMessage === 'cancelled' || logMessage === 'not_found') {
                if (logMessage === 'done') {
                    progressBar.style.width = '100%';
                    progressText.textContent = '100%';
                    progressPercentage.textContent = '100%';
                }
                speedInfo.textContent = '0 kB/s';
                uploadSpeedInfo.textContent = '0 kB/s';
                remainingTimeElem.textContent = logMessage === 'done' ? 'Terminé !' : 'Annulé';
                eventSource.close();
                
                setTimeout(() => {
                    resetDownloadUI();
                }, 2000);
                return;
            }

            var progressMatch = logMessage.match(/(\d+\.\d+)% complete/);
            var downloadSpeedMatch = logMessage.match(/down: (\d+\.\d+) kB\/s/);
            var uploadSpeedMatch = logMessage.match(/up: (\d+\.\d+) kB\/s/);

            if (progressMatch) {
                var progress = parseFloat(progressMatch[1]);
                progressBar.style.width = progress + '%';
                progressText.textContent = progress.toFixed(2) + '%';
                progressPercentage.textContent = progress.toFixed(1) + '%';

                var elapsedTime = (Date.now() - startTime) / 1000;
                elapsedTimeElem.textContent = formatTime(elapsedTime);

                var downloadSpeed = 0;
                if (downloadSpeedMatch) {
                    downloadSpeed = parseFloat(downloadSpeedMatch[1]);
                    speedInfo.textContent = formatSpeed(downloadSpeed);
                }

                if (uploadSpeedMatch) {
                    var uploadSpeed = parseFloat(uploadSpeedMatch[1]);
                    uploadSpeedInfo.textContent = formatSpeed(uploadSpeed);
                }

                // Calculer le temps restant seulement si le progrès avance et qu'on a une vitesse
                if (progress > lastProgress && downloadSpeed > 0) {
                    var now = Date.now();
                    var timeDiff = (now - lastProgressUpdate) / 1000; // en secondes
                    var progressDiff = progress - lastProgress;
                    
                    // Ajouter à l'historique
                    progressHistory.push({
                        time: now,
                        progress: progress,
                        speed: progressDiff / timeDiff
                    });
                    
                    // Garder seulement les 5 dernières mesures
                    if (progressHistory.length > 5) {
                        progressHistory.shift();
                    }
                    
                    // Calculer la vitesse moyenne
                    var avgSpeed = progressHistory.reduce((sum, item) => sum + item.speed, 0) / progressHistory.length;
                    
                    // Calculer le temps restant basé sur la vitesse moyenne
                    var remainingProgress = 100 - progress;
                    var remainingTime = remainingProgress / avgSpeed;
                    
                    // Afficher seulement si le calcul est valide
                    if (isFinite(remainingTime) && remainingTime > 0) {
                        remainingTimeElem.textContent = formatTime(remainingTime);
                    }
                    
                    lastProgress = progress;
                    lastProgressUpdate = now;
                } else if (downloadSpeed === 0 && progress < 100) {
                    // Pendant le file check ou si la vitesse est 0
                    remainingTimeElem.textContent = 'Calcul...';
                }
            }
        };

        eventSource.onopen = function () {
            console.log('Connection opened');
        };

        eventSource.onerror = function () {
            console.log('Connection closed');
            eventSource.close();
            resetDownloadUI();
        };
    }

    function stopDownload() {
        const downloadState = {
            download_id: downloadIdInput.value
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
                resetDownloadUI();
            } else {
                console.error('Erreur lors de l\'annulation du téléchargement');
            }
        })
        .catch(error => {
            console.error('Erreur réseau ou autre:', error);
        });
    }

    // Gestion du changement de fichier
    torrentFileInput.addEventListener('change', function (event) {
        if (event.target.files[0]) {
            updateFileInfo(event.target.files[0].name);
        }
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