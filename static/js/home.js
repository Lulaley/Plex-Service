
function toggleMenu() {
    var menu = document.querySelector('.menu');
    menu.classList.toggle('active');
}

window.onload = function() {
    document.querySelector('.center-logo').classList.add('moveLogo');
    document.querySelector('.navbar').classList.add('unblurBackground');
    document.querySelector('.center-container').classList.add('unblurBackground');
    document.querySelector('.navbar').classList.add('fadeInElements');
    document.querySelector('.center-container').classList.add('fadeInElements');

    setTimeout(function() {
        document.querySelector('.navbar').classList.remove('blur-background');
        document.querySelector('.center-container').classList.remove('blur-background');
        document.querySelector('.center-logo').style.display = 'none'; // Hide the logo after animation
    }, 3000); // Match the duration of the animation
};