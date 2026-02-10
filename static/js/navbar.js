function toggleMenu() {
    const menu = document.querySelector('.navbar .menu');
    const hamburger = document.querySelector('.navbar .hamburger');
    menu.classList.toggle('active');
    hamburger.classList.toggle('active');
}

// Fermer le menu mobile quand on clique sur un lien
function closeMenuOnClick() {
    if (window.innerWidth <= 768) {
        const menu = document.querySelector('.navbar .menu');
        const hamburger = document.querySelector('.navbar .hamburger');
        menu.classList.remove('active');
        hamburger.classList.remove('active');
    }
}

// Fermer le menu si on clique en dehors
document.addEventListener('click', function(event) {
    const navbar = document.querySelector('.navbar');
    const menu = document.querySelector('.navbar .menu');
    const hamburger = document.querySelector('.navbar .hamburger');
    
    if (!navbar.contains(event.target) && menu.classList.contains('active')) {
        menu.classList.remove('active');
        hamburger.classList.remove('active');
    }
});

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

// Vérifier immédiatement au chargement
checkNewUsers();

// Polling optimisé : 60s au lieu de 30s + arrêt si onglet invisible
let newUsersInterval = setInterval(checkNewUsers, 60000);

// Arrêter le polling quand l'onglet n'est pas visible
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        clearInterval(newUsersInterval);
    } else {
        checkNewUsers(); // Rafraîchir immédiatement au retour
        newUsersInterval = setInterval(checkNewUsers, 60000);
    }
});