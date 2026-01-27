document.addEventListener('DOMContentLoaded', function () {
    const mediaSelect = document.getElementById('media-select');
    const startSeedFromMediaBtn = document.getElementById('start-seed-from-media');
    const torrentUploadForm = document.getElementById('torrent-upload-form');
    const seedsContainer = document.getElementById('seeds-container');
    const seedsCountElem = document.getElementById('seeds-count');

    let updateInterval = null;

    // Charger la liste des médias disponibles
    loadMediaList();

    // Charger les seeds actifs
    loadActiveSeeds();

    // Démarrer la mise à jour automatique des stats
    startAutoUpdate();

    // Event: Démarrer un seed depuis la sélection de médias
    startSeedFromMediaBtn.addEventListener('click', function () {
        const selectedPath = mediaSelect.value;
        if (!selectedPath) {
            alert('Veuillez sélectionner un média');
            return;
        }
        startSeed(selectedPath, null);
    });

    // Event: Upload d'un fichier torrent
    torrentUploadForm.addEventListener('submit', function (event) {
        event.preventDefault();
        uploadTorrentAndStartSeed();
    });

    function loadMediaList() {
        fetch('/get_media_list')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    mediaSelect.innerHTML = '<option value="">-- Sélectionner un média --</option>';
                    data.media_list.forEach(media => {
                        const option = document.createElement('option');
                        option.value = media.path;
                        option.textContent = `[${media.type.toUpperCase()}] ${media.name}`;
                        mediaSelect.appendChild(option);
                    });
                } else {
                    console.error('Erreur lors du chargement de la liste des médias');
                }
            })
            .catch(error => {
                console.error('Erreur réseau:', error);
            });
    }

    function startSeed(dataPath, torrentFilePath) {
        const payload = {
            data_path: dataPath
        };
        if (torrentFilePath) {
            payload.torrent_file_path = torrentFilePath;
        }

        // Récupérer le token CSRF depuis le DOM
        var csrfToken = document.querySelector('input[name="csrf_token"]').value;
        fetch('/start_seed', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify(payload)
        })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                console.log('Seed démarré avec succès:', result.seed_id);
                loadActiveSeeds();
                alert('Seed démarré avec succès !');
            } else {
                const errorMsg = result.message || 'Erreur inconnue';
                alert('Erreur lors du démarrage du seed: ' + errorMsg);
                console.error('Erreur détaillée:', result);
            }
        })
        .catch(error => {
            console.error('Erreur réseau:', error);
            alert('Erreur réseau lors du démarrage du seed: ' + error.message);
        });
    }

    function uploadTorrentAndStartSeed() {
        const dataPath = document.getElementById('data-path-input').value;
        const torrentFile = document.getElementById('torrent-file-input').files[0];

        if (!dataPath || !torrentFile) {
            alert('Veuillez remplir tous les champs');
            return;
        }

        const formData = new FormData();
        formData.append('torrent-file', torrentFile);
        formData.append('data_path', dataPath);
        
        // Ajouter le token CSRF
        const csrfToken = document.querySelector('input[name="csrf_token"]').value;
        formData.append('csrf_token', csrfToken);

        fetch('/upload_torrent_for_seed', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            // Vérifier le status HTTP
            if (!response.ok) {
                return response.text().then(text => {
                    console.error('Réponse du serveur:', text);
                    throw new Error(`Erreur HTTP ${response.status}: Le serveur a retourné une erreur`);
                });
            }
            return response.text().then(text => {
                try {
                    return JSON.parse(text);
                } catch (e) {
                    console.error('Réponse non-JSON du serveur:', text);
                    throw new Error('Le serveur a retourné une réponse invalide');
                }
            });
        })
        .then(result => {
            if (result.success) {
                console.log('Torrent uploadé et seed démarré:', result.seed_id);
                document.getElementById('data-path-input').value = '';
                document.getElementById('torrent-file-input').value = '';
                loadActiveSeeds();
                alert('Seed démarré avec succès !');
            } else {
                const errorMsg = result.message || 'Erreur inconnue';
                alert('Erreur: ' + errorMsg);
                console.error('Erreur détaillée:', result);
            }
        })
        .catch(error => {
            console.error('Erreur complète:', error);
            alert('Erreur lors de l\'upload: ' + error.message);
        });
    }

    function loadActiveSeeds() {
        fetch('/get_seeds_stats')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    displaySeeds(data.seeds);
                } else {
                    console.error('Erreur lors du chargement des seeds');
                }
            })
            .catch(error => {
                console.error('Erreur réseau:', error);
            });
    }

    function displaySeeds(seeds) {
        seedsCountElem.textContent = seeds.length;

        if (seeds.length === 0) {
            seedsContainer.innerHTML = '<p class="no-seeds">Aucun seed actif pour le moment</p>';
            return;
        }

        // Créer un Map des seeds actuels pour comparaison
        const currentSeedIds = new Set(
            Array.from(seedsContainer.children)
                .filter(el => el.id && el.id.startsWith('seed-'))
                .map(el => el.id.replace('seed-', ''))
        );

        const newSeedIds = new Set(seeds.map(s => s.id));

        // Supprimer les seeds qui n'existent plus
        Array.from(seedsContainer.children).forEach(child => {
            if (child.id && child.id.startsWith('seed-')) {
                const seedId = child.id.replace('seed-', '');
                if (!newSeedIds.has(seedId)) {
                    child.remove();
                }
            }
        });

        // Ajouter ou mettre à jour les seeds
        seeds.forEach(seed => {
            const existingCard = document.getElementById(`seed-${seed.id}`);
            if (existingCard) {
                // Mettre à jour la carte existante sans la recréer
                updateSeedCard(existingCard, seed);
            } else {
                // Créer une nouvelle carte
                const seedCard = createSeedCard(seed);
                seedsContainer.appendChild(seedCard);
            }
        });
    }

    function updateSeedCard(card, seed) {
        const uploadRate = seed.stats.upload_rate ? seed.stats.upload_rate.toFixed(2) : '0.00';
        const uploaded = seed.stats.uploaded ? formatBytes(seed.stats.uploaded) : '0 B';
        const peers = seed.stats.peers || 0;
        const seedsCount = seed.stats.seeds || 0;
        const progress = seed.stats.progress ? seed.stats.progress.toFixed(1) : '0.0';
        const state = seed.stats.state || seed.state || 'unknown';

        // Mettre à jour seulement le contenu qui change
        const statusBadge = card.querySelector('.status-badge');
        if (statusBadge) {
            statusBadge.className = `status-badge ${seed.is_active ? 'active' : 'inactive'}`;
            statusBadge.textContent = seed.is_active ? 'Actif' : 'Inactif';
        }

        const stateBadge = card.querySelector('.state-badge');
        if (stateBadge) {
            stateBadge.textContent = state;
        }

        const statValues = card.querySelectorAll('.stat-value');
        if (statValues[0]) statValues[0].textContent = `${uploadRate} kB/s`;
        if (statValues[1]) statValues[1].textContent = uploaded;
        if (statValues[2]) statValues[2].textContent = peers;
        if (statValues[3]) statValues[3].textContent = seedsCount;
        if (statValues[4]) statValues[4].textContent = `${progress}%`;
    }

    function createSeedCard(seed) {
        const card = document.createElement('div');
        card.className = 'seed-card';
        card.id = `seed-${seed.id}`;

        const uploadRate = seed.stats.upload_rate ? seed.stats.upload_rate.toFixed(2) : '0.00';
        const uploaded = seed.stats.uploaded ? formatBytes(seed.stats.uploaded) : '0 B';
        const peers = seed.stats.peers || 0;
        const seedsCount = seed.stats.seeds || 0;
        const progress = seed.stats.progress ? seed.stats.progress.toFixed(1) : '0.0';
        const state = seed.stats.state || seed.state || 'unknown';

        card.innerHTML = `
            <div class="seed-header">
                <h3 class="seed-name">${seed.name}</h3>
                <button class="btn-stop" onclick="stopSeed('${seed.id}')">Arrêter</button>
            </div>
            <div class="seed-info">
                <p><strong>Chemin:</strong> ${seed.data_path}</p>
                <p><strong>Statut:</strong> <span class="status-badge ${seed.is_active ? 'active' : 'inactive'}">${seed.is_active ? 'Actif' : 'Inactif'}</span></p>
                <p><strong>État:</strong> <span class="state-badge">${state}</span></p>
            </div>
            <div class="seed-stats">
                <div class="stat-item">
                    <span class="stat-label">Vitesse d'upload</span>
                    <span class="stat-value">${uploadRate} kB/s</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Total uploadé</span>
                    <span class="stat-value">${uploaded}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Peers connectés</span>
                    <span class="stat-value">${peers}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Seeds</span>
                    <span class="stat-value">${seedsCount}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Progression</span>
                    <span class="stat-value">${progress}%</span>
                </div>
            </div>
        `;

        return card;
    }

    function startAutoUpdate() {
        updateInterval = setInterval(() => {
            loadActiveSeeds();
        }, 3000); // Mettre à jour toutes les 3 secondes
    }

    function formatBytes(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // Nettoyer l'intervalle quand on quitte la page
    window.addEventListener('beforeunload', function () {
        if (updateInterval) {
            clearInterval(updateInterval);
        }
    });
});

// Fonction globale pour arrêter un seed
function stopSeed(seedId) {
    if (!confirm('Êtes-vous sûr de vouloir arrêter ce seed ?')) {
        return;
    }

    // Récupérer le token CSRF depuis le DOM
    var csrfToken = document.querySelector('input[name="csrf_token"]').value;

    fetch('/stop_seed', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({ seed_id: seedId })
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            console.log('Seed arrêté avec succès');
            // Recharger la liste des seeds
            setTimeout(() => {
                location.reload();
            }, 500);
        } else {
            alert('Erreur lors de l\'arrêt du seed: ' + result.message);
        }
    })
    .catch(error => {
        console.error('Erreur réseau:', error);
        alert('Erreur réseau lors de l\'arrêt du seed');
    });
}
