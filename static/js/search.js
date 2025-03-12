document.getElementById('search-input').addEventListener('input', function() {
    const query = this.value.trim();
    if (query.length < 3) {
        document.getElementById('results').innerHTML = '';
        return;
    }

    fetch(`/search_tmdb?query=${query}`)
        .then(response => response.json())
        .then(data => {
            const resultsDiv = document.getElementById('results');
            resultsDiv.innerHTML = '';

            if (data.movies.length > 0) {
                const moviesDiv = document.createElement('div');
                moviesDiv.innerHTML = '<h2>Films</h2>';
                data.movies.forEach(movie => {
                    const movieDiv = document.createElement('div');
                    movieDiv.classList.add('result-item');
                    movieDiv.innerHTML = `
                        <img src="https://image.tmdb.org/t/p/w500${movie.poster_path}" alt="${movie.title}">
                        <div>
                            <p><strong>${movie.title}</strong> (${movie.release_date})</p>
                            <p>${movie.overview}</p>
                            <button class="request-button" onclick="createWish('${movie.title}', 'movie')">Demander</button>
                        </div>
                    `;
                    moviesDiv.appendChild(movieDiv);
                });
                resultsDiv.appendChild(moviesDiv);
            }

            if (data.tv_shows.length > 0) {
                const tvShowsDiv = document.createElement('div');
                tvShowsDiv.innerHTML = '<h2>Séries</h2>';
                data.tv_shows.forEach(tvShow => {
                    const tvShowDiv = document.createElement('div');
                    tvShowDiv.classList.add('result-item');
                    tvShowDiv.innerHTML = `
                        <img src="https://image.tmdb.org/t/p/w500${tvShow.poster_path}" alt="${tvShow.name}">
                        <div>
                            <p><strong>${tvShow.name}</strong> (${tvShow.first_air_date})</p>
                            <p>${tvShow.overview}</p>
                            <button class="request-button" onclick="createWish('${tvShow.name}', 'series')">Demander</button>
                        </div>
                    `;
                    tvShowsDiv.appendChild(tvShowDiv);
                });
                resultsDiv.appendChild(tvShowsDiv);
            }
        })
        .catch(error => console.error('Erreur:', error));
});

function createWish(title, type) {
    fetch('/create_wish', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ title: title, type: type })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Demande créée avec succès');
        } else {
            alert('Erreur lors de la création de la demande');
        }
    })
    .catch(error => console.error('Erreur:', error));
}