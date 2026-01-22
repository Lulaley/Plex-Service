function showDetails(element) {
    // D'abord, masquer tous les autres détails et retirer la classe
    document.querySelectorAll('.wish-card.details-open').forEach(card => {
        card.classList.remove('details-open');
        const detail = card.querySelector('.wish-details');
        if (detail) {
            detail.classList.remove('show');
        }
    });
    
    const details = element.querySelector('.wish-details');
    const id = element.getAttribute('data-id');
    
    console.log('Adding details-open class to:', element);
    console.log('Element classes before:', element.className);
    
    // Si les détails sont déjà chargés, juste les afficher
    if (details.innerHTML.trim() !== '') {
        // Forcer un reflow pour que le navigateur applique bien le CSS
        void element.offsetHeight;
        details.classList.add('show');
        element.classList.add('details-open');
        // Forcer encore une fois le recalcul du style
        void element.offsetHeight;
        console.log('Element classes after:', element.className);
        return;
    }
    
    // Sinon, charger les détails
    fetch(`/wish_details/${id}`)
        .then(response => response.json())
        .then(data => {
            details.innerHTML = `
                <p><strong>Date de sortie:</strong> ${data.release_date}</p>
                <p><strong>Utilisateur:</strong> ${data.wishOwner}</p>
                <p><strong>Date de la demande:</strong> ${data.requestDate}</p>
            `;
            // Forcer un reflow pour que le navigateur applique bien le CSS
            void element.offsetHeight;
            details.classList.add('show');
            element.classList.add('details-open');
            // Forcer encore une fois le recalcul du style
            void element.offsetHeight;
            console.log('Element classes after fetch:', element.className);
        })
        .catch(error => console.error('Erreur:', error));
}

function hideDetails(element) {
    const details = element.querySelector('.wish-details');
    details.classList.remove('show');
    element.classList.remove('details-open');
}

function validateWish(element) {
    const status = element.getAttribute('data-status');
    if (status === 'validated') {
        alert('Cette demande est déjà validée.');
        return;
    }

    const id = element.getAttribute('data-id');
    fetch(`/validate_wish/${id}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Demande validée avec succès');
            location.reload();
        } else {
            alert('Erreur lors de la validation de la demande: ' + data.message);
        }
    })
    .catch(error => console.error('Erreur:', error));
}