// Fonction de validation de l'email
function validateEmail(email) {
    var emailPattern = /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}$/;
    return emailPattern.test(email);
}

// Fonction de validation du mot de passe
function validatePassword(password) {
    var passwordPattern = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{10,}$/;
    return passwordPattern.test(password);
}

// Ajouter des écouteurs d'événements pour les champs de formulaire
document.querySelector('input[name="email"]').addEventListener('input', function (event) {
    var email = event.target.value;
    var emailTooltip = document.getElementById('email-tooltip');
    if (!validateEmail(email)) {
        event.target.classList.add('error');
        event.target.classList.remove('valid');
        emailTooltip.textContent = "Adresse email invalide.";
    } else {
        event.target.classList.remove('error');
        event.target.classList.add('valid');
        emailTooltip.textContent = "Adresse email valide.";
    }
});

document.querySelector('input[name="createPassword"]').addEventListener('input', function (event) {
    var password = event.target.value;
    var passwordTooltip = document.getElementById('password-tooltip');
    if (!validatePassword(password)) {
        event.target.classList.add('error');
        event.target.classList.remove('valid');
        passwordTooltip.textContent = "Le mot de passe doit contenir au moins 10 caractères, une majuscule, une minuscule, un caractère spécial et un chiffre.";
    } else {
        event.target.classList.remove('error');
        event.target.classList.add('valid');
        passwordTooltip.textContent = "Mot de passe valide.";
    }
});

document.querySelector('input[name="confirm_password"]').addEventListener('input', function (event) {
    var confirmPassword = event.target.value;
    var password = document.querySelector('input[name="createPassword"]').value;
    var confirmPasswordTooltip = document.getElementById('confirm-password-tooltip');
    if (password !== confirmPassword) {
        event.target.classList.add('error');
        event.target.classList.remove('valid');
        confirmPasswordTooltip.textContent = "Les mots de passe ne correspondent pas.";
    } else {
        event.target.classList.remove('error');
        event.target.classList.add('valid');
        confirmPasswordTooltip.textContent = "Les mots de passe correspondent.";
    }
});

document.getElementById('create-form').addEventListener('submit', function (event) {
    // Récupérer les valeurs des champs
    var email = document.querySelector('input[name="email"]').value;
    var password = String(document.querySelector('input[name="createPassword"]').value);
    var confirmPassword = String(document.querySelector('input[name="confirm_password"]').value);

    // Récupérer les éléments des champs
    var emailField = document.querySelector('input[name="email"]');
    var passwordField = document.querySelector('input[name="createPassword"]');
    var confirmPasswordField = document.querySelector('input[name="confirm_password"]');

    // Récupérer les éléments des tooltips
    var emailTooltip = document.getElementById('email-tooltip');
    var passwordTooltip = document.getElementById('password-tooltip');
    var confirmPasswordTooltip = document.getElementById('confirm-password-tooltip');

    // Réinitialiser les styles et les tooltips
    emailField.classList.remove('error');
    passwordField.classList.remove('error');
    confirmPasswordField.classList.remove('error');
    emailTooltip.textContent = "";
    passwordTooltip.textContent = "";
    confirmPasswordTooltip.textContent = "";

    // Valider l'email
    if (!validateEmail(email)) {
        emailField.classList.add('error');
        emailTooltip.textContent = "Adresse email invalide.";
        event.preventDefault();
    }

    // Valider le mot de passe
    if (!validatePassword(password)) {
        passwordField.classList.add('error');
        passwordTooltip.textContent = "Le mot de passe doit contenir au moins 10 caractères, une majuscule, une minuscule, un caractère spécial et un chiffre.";
        event.preventDefault();
    }

    // Valider la confirmation du mot de passe
    if (password !== confirmPassword) {
        confirmPasswordField.classList.add('error');
        confirmPasswordTooltip.textContent = "Les mots de passe ne correspondent pas.";
        event.preventDefault();
    }

    // Bloquer la soumission si un des tooltips est invalide
    if (emailTooltip.textContent || passwordTooltip.textContent || confirmPasswordTooltip.textContent) {
        event.preventDefault();
    }
});


let formsVisible = false;

function hideForms(callback) {
    const buttons = document.getElementById('buttons');
    const createForm = document.getElementById('create-form');
    const loginForm = document.getElementById('login-form');
    const forms = [createForm, loginForm, buttons];

    buttons.style.display = 'none';
    forms.forEach(form => {
        if (form.style.display === 'block') {
            form.style.opacity = 0;
            setTimeout(() => {
                form.style.display = 'none';
                formsVisible = false;
                if (callback) callback();
            }, 500); // Duration of the fade-out animation
        }
    });

    if (!forms.some(form => form.style.display === 'block') && callback) {
        callback();
    }
}

function showButtons() {
    const logo = document.querySelector('.plex-logo');
    const buttons = document.getElementById('buttons');

    if (formsVisible) {
        hideForms(() => {
            buttons.style.display = 'none';
            setTimeout(() => {
                buttons.style.opacity = 0;
            }, 500);
        });
    } else {
        buttons.style.display = 'block';
        setTimeout(() => {
            buttons.style.opacity = 1;
        }, 500);
        setTimeout(() => {
            showLoginForm();
        }, 50);
    }
}

function showLoginForm() {
    const btnLogin = document.getElementById('connexion');
    const btnRegister = document.getElementById('creer');
    btnRegister.style.backgroundColor = '#ff9900';
    btnLogin.style.backgroundColor = '#ffb84d';

    const createForm = document.getElementById('create-form');
    createForm.style.display = 'none';
    createForm.style.opacity = 0;

    const loginForm = document.getElementById('login-form');
    const inputs = loginForm.querySelectorAll('input');
    const submitContainer = loginForm.querySelector('.submit-container');
    loginForm.style.display = 'block';

    setTimeout(() => {
        loginForm.style.opacity = 1;
        inputs.forEach((input, index) => {
            setTimeout(() => {
                input.style.opacity = 1;
            }, index * 500);
        });
        setTimeout(() => {
            submitContainer.style.opacity = 1;
        }, inputs.length * 250);
    }, 500);
    formsVisible = true;
}

function showCreateForm() {
    const btnLogin = document.getElementById('connexion');
    const btnRegister = document.getElementById('creer');

    btnRegister.style.backgroundColor = '#ffb84d';
    btnLogin.style.backgroundColor = '#ff9900';

    const loginForm = document.getElementById('login-form');
    loginForm.style.display = 'none';
    loginForm.style.opacity = 0;

    const createForm = document.getElementById('create-form');
    const inputs = createForm.querySelectorAll('input');
    const submitContainer = createForm.querySelector('.submit-container');
    createForm.style.display = 'block';

    setTimeout(() => {
        createForm.style.opacity = 1;
        inputs.forEach((input, index) => {
            setTimeout(() => {
                input.style.opacity = 1;
            }, index * 500);
        });
        setTimeout(() => {
            submitContainer.style.opacity = 1;
        }, inputs.length * 250);
    }, 500);
    formsVisible = true;
}

document.querySelector('.plex-logo').addEventListener('click', showButtons);

document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('#create-form form');
    const submitBtn = document.getElementById('submit-btn');
    const inputs = form.querySelectorAll('input');

    function validateForm() {
        let allValid = true;
        inputs.forEach(input => {
            const tooltip = document.getElementById(`${input.id}-tooltip`);
            if (!input.checkValidity()) {
                tooltip.style.visibility = 'visible';
                tooltip.style.opacity = '1';
                input.classList.add('error');
                allValid = false;
            } else {
                tooltip.style.visibility = 'hidden';
                tooltip.style.opacity = '0';
                input.classList.remove('error');
            }
        });
        submitBtn.style.display = allValid ? 'block' : 'none';
    }

    inputs.forEach(input => {
        input.addEventListener('input', validateForm);
    });

    form.addEventListener('submit', function(event) {
        validateForm();
        if (!form.checkValidity()) {
            event.preventDefault();
        }
    });
});