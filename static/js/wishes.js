function showDetails(element) {
    const details = element.querySelector('.wish-details');
    const id = element.getAttribute('data-id');
    
    // Si les détails sont déjà chargés, juste les afficher
    if (details.innerHTML.trim() !== '') {
        details.classList.add('show');
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
            details.classList.add('show');
        })
        .catch(error => console.error('Erreur:', error));
}

function hideDetails(element) {
    const details = element.querySelector('.wish-details');
    details.classList.remove('show');
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