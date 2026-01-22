
function toggleMenu() {
    var menu = document.querySelector('.menu');
    menu.classList.toggle('active');
}

window.onload = function() {
    const centerLogo = document.querySelector('.center-logo');
    if (centerLogo) {
        centerLogo.classList.add('moveLogo');
    }
    
    const navbar = document.querySelector('.navbar');
    if (navbar) {
        navbar.classList.add('unblurBackground', 'no-blur');
        navbar.classList.add('fadeInElements');
    }
    
    const centerContainer = document.querySelector('.center-container');
    if (centerContainer) {
        centerContainer.classList.add('unblurBackground');
        centerContainer.classList.add('fadeInElements');
    }

    setTimeout(function() {
        if (navbar) {
            navbar.classList.remove('blur-background');
            navbar.classList.add('no-blur');
        }
        if (centerContainer) {
            centerContainer.classList.remove('blur-background');
        }
        if (centerLogo) {
            centerLogo.style.display = 'none'; // Hide the logo after animation
            centerLogo.style.opacity = '0';
        }
    }, 3000); // Match the duration of the animation
};