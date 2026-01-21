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

// Vérifier les nouveaux utilisateurs toutes les 30 secondes
setInterval(checkNewUsers, 30000);
// Vérifier immédiatement au chargement de la page
checkNewUsers();