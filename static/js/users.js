function validateUser(username) {
    fetch('/users', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username: username, action: 'validate' })
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            alert(data.message);
            location.reload();  // Rafraîchir la page après validation
        } else if (data.error) {
            alert(data.error);
        }
    })
    .catch(error => console.error('Erreur:', error));
}

function deleteUser(username) {
    fetch('/users', {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username: username })
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            alert(data.message);
            location.reload();  // Rafraîchir la page après suppression
        } else if (data.error) {
            alert(data.error);
        }
    })
    .catch(error => console.error('Erreur:', error));
}

function makeAdmin(username) {
    fetch('/users', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username: username, action: 'make_admin' })
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            alert(data.message);
            location.reload();  // Rafraîchir la page après mise à jour
        } else if (data.error) {
            alert(data.error);
        }
    })
    .catch(error => console.error('Erreur:', error));
}