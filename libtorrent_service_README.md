# Service libtorrent partagé – Documentation rapide

## 1. Lancer le service libtorrent (API Flask)

Dans le dossier du projet :

```bash
python libtorrent_service.py
```

Le service écoute sur `http://127.0.0.1:5005`.

---

## 2. Appeler l’API depuis le site (exemples)

Utilise le client Python fourni :

```python
from static.Controleur.libtorrent_client import add_seed, remove_seed, get_stats

# Ajouter un seed
add_seed('id123', '/chemin/vers/fichier.torrent', '/chemin/vers/dossier')

# Supprimer un seed
remove_seed('id123')

# Récupérer les stats de tous les seeds
stats = get_stats()
```

---

## 3. Endpoints de l’API

- `POST /add_seed` : Ajoute un seed
  - JSON attendu : `{ "seed_id": str, "torrent_path": str, "data_path": str }`
- `POST /remove_seed` : Supprime un seed
  - JSON attendu : `{ "seed_id": str }`
- `GET /get_stats` : Statistiques de tous les seeds

---

## 4. À faire côté site
- Remplacer les appels directs à libtorrent par des appels à `libtorrent_client.py`.
- Garder la logique de gestion (BDD, JSON, UI) côté site, mais toute action sur les seeds passe par l’API.

---

## 5. Astuces
- Le service doit tourner en permanence (screen/tmux/systemd recommandé).
- Un seul service pour tous les workers Gunicorn.
- Pour debug : surveiller les logs du service et tester les endpoints avec curl ou Postman.

---

## 6. Exemple curl

```bash
curl -X POST http://127.0.0.1:5005/add_seed -H "Content-Type: application/json" -d '{"seed_id": "id123", "torrent_path": "/chemin/vers/fichier.torrent", "data_path": "/chemin/vers/dossier"}'
```

---

## 7. Arrêt du service

Ctrl+C dans le terminal où il tourne.

---

**Résumé** : Le site ne manipule plus libtorrent directement : il utilise l’API locale pour toutes les actions sur les seeds. La gestion multi-worker devient illimitée et centralisée.
