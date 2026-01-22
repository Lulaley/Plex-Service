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
            buttons.style.opacity = 0;
        });
    } else {
        buttons.style.display = 'flex';
        setTimeout(() => {
            buttons.style.opacity = 1;
        }, 50);
        setTimeout(() => {
            showLoginForm();
        }, 600);
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
            }, index * 150);
        });
        setTimeout(() => {
            submitContainer.style.opacity = 1;
        }, inputs.length * 150 + 100);
    }, 100);
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
    const submitBtn = createForm.querySelector('#submit-btn');
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
            submitBtn.style.display = 'none';
        }, inputs.length * 250);
    }, 500);
    formsVisible = true;
}

function togglePasswordVisibility(element) {
    const passwordInput = element.previousElementSibling;
    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        element.textContent = '🙈'; // Icône pour masquer le mot de passe
    } else {
        passwordInput.type = 'password';
        element.textContent = '👁️'; // Icône pour révéler le mot de passe
    }
}

document.querySelector('.plex-logo').addEventListener('click', showButtons);
document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('#create-form form');
    const submitBtn = document.getElementById('submit-btn');
    const inputs = form.querySelectorAll('input');
    let currentTooltip = null;

    function validateForm() {
        let allValid = true;
        inputs.forEach(input => {
            const tooltip = document.getElementById(`${input.id}-tooltip`);
            if (tooltip !== null) {
                if (input.value.trim() === '') {
                    tooltip.style.visibility = 'hidden';
                    tooltip.style.opacity = '0';
                    input.classList.remove('error');
                    input.style.border = ''; // Réinitialiser la bordure
                } else if (!input.checkValidity()) {
                    allValid = false;
                    tooltip.style.visibility = 'visible';
                    tooltip.style.opacity = '1';
                    input.classList.add('error');
                    input.style.border = '1px solid red'; // Ajouter une bordure rouge pour indiquer l'erreur
                } else {
                    tooltip.style.visibility = 'hidden';
                    tooltip.style.opacity = '0';
                    input.classList.remove('error');
                    input.style.border = ''; // Réinitialiser la bordure
                }
            }
        });
        submitBtn.style.display = allValid ? 'block' : 'none';
    }

    let emailValid = false;
    let passwordValid = false;
    let confirmPasswordValid = false;
    
    document.querySelector('input[name="email"]').addEventListener('input', function (event) {
        var email = event.target.value;
        var emailTooltip = document.getElementById('email-tooltip');
        if (!validateEmail(email) && email.length > 0) {
            event.target.classList.add('error');
            event.target.classList.remove('valid');
            emailTooltip.textContent = "Adresse email invalide.";
            emailTooltip.style.visibility = 'visible';
            emailTooltip.style.opacity = '1';
            emailValid = false;
        } else {
            event.target.classList.remove('error');
            event.target.classList.add('valid');
            emailTooltip.textContent = "Adresse email valide.";
            emailTooltip.style.visibility = 'hidden';
            emailTooltip.style.opacity = '0';
            emailValid = true;
        }
        toggleSubmitButton();
    });
    
    document.querySelector('input[name="createPassword"]').addEventListener('input', function (event) {
        var password = event.target.value;
        var passwordTooltip = document.getElementById('createPassword-tooltip');
        if (!validatePassword(password) && password.length > 0) {
            event.target.classList.add('error');
            event.target.classList.remove('valid');
            passwordTooltip.textContent = "Le mot de passe doit contenir au moins 10 caractères, une majuscule, une minuscule, un caractère spécial et un chiffre.";
            passwordTooltip.style.visibility = 'visible';
            passwordTooltip.style.opacity = '1';
            passwordValid = false;
        } else {
            event.target.classList.remove('error');
            event.target.classList.add('valid');
            passwordTooltip.textContent = "Mot de passe valide.";
            passwordTooltip.style.visibility = 'hidden';
            passwordTooltip.style.opacity = '0';
            passwordValid = true;
        }
        toggleSubmitButton();
    });
    
    document.querySelector('input[name="confirm_password"]').addEventListener('input', function (event) {
        var confirmPassword = event.target.value;
        var password = document.querySelector('input[name="createPassword"]').value;
        var confirmPasswordTooltip = document.getElementById('confirm_password-tooltip');
        if (password !== confirmPassword && confirmPassword.length > 0 && password.length > 0) {
            event.target.classList.add('error');
            event.target.classList.remove('valid');
            confirmPasswordTooltip.textContent = "Les mots de passe ne correspondent pas.";
            confirmPasswordTooltip.style.visibility = 'visible';
            confirmPasswordTooltip.style.opacity = '1';
            confirmPasswordValid = false;
        } else {
            event.target.classList.remove('error');
            event.target.classList.add('valid');
            confirmPasswordTooltip.textContent = "Les mots de passe correspondent.";
            confirmPasswordTooltip.style.visibility = 'hidden';
            confirmPasswordTooltip.style.opacity = '0';
            confirmPasswordValid = true;
        }
        toggleSubmitButton();
    });
    
    function toggleSubmitButton() {
        const submitBtn = document.getElementById('submit-btn');
        if (emailValid && passwordValid && confirmPasswordValid) {
            console.log('All fields are valid');
            submitBtn.style.display = 'block';
        } else {
            submitBtn.style.display = 'none';
        }
    }

    inputs.forEach(input => {
        input.addEventListener('focus', () => {
            if (currentTooltip) {
                currentTooltip.style.visibility = 'hidden';
                currentTooltip.style.opacity = '0';
                currentTooltip = null;
            }
        });
    });

    form.addEventListener('submit', function(event) {
        validateForm();
        if (!form.checkValidity()) {
            event.preventDefault();
        }
    });

    // Initial validation check to ensure the button is displayed if all fields are valid on page load
    validateForm();
});