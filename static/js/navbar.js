function checkNewUsers() {
    fetch('/check_new_users')
        .then(response => response.json())
        .then(data => {
            const userButton = document.getElementById('user-button');
            if (data.new_users_count > 0) {
                userButton.setAttribute('data-count', data.new_users_count);
            } else {
                userButton.removeAttribute('data-count');
            }
        })
        .catch(error => console.error('Erreur:', error));
}

// Vérifier les nouveaux utilisateurs toutes les 30 secondes
setInterval(checkNewUsers, 30000);
// Vérifier immédiatement au chargement de la page
checkNewUsers();