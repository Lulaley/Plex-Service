# 🔄 Système Hybride JSON ↔ SQLite

## 📝 Configuration

Dans `static/Conf/config.ini`, section `[BDD]` :

```ini
[BDD]
sql = false  # true pour SQLite, false pour JSON
db_path = /var/www/public/Plex-Service/data/plex_service.db
```

---

## 🎯 Fonctionnement

### **Mode actuel : JSON (défaut)**
- Stockage dans `/tmp/active_downloads.json` et `/tmp/active_seeds.json`
- Utilise `fcntl` pour verrouillage multi-worker
- Comportement actuel préservé

### **Mode SQLite**
- Stockage dans base SQLite : `/data/plex_service.db`
- Thread-safe natif (pas de fcntl nécessaire)
- Historique permanent (même après terminaison)
- Requêtes SQL pour stats/recherches

---

## 🔄 Migration Automatique

**Lors du changement de mode (JSON → SQL ou SQL → JSON)** :

1. **Détection automatique** via `sync_on_mode_change()`
2. **Comparaison des timestamps** :
   - JSON : `os.path.getmtime(active_downloads.json)`
   - SQL : `MAX(updated_at)` dans la table
3. **Migration de la version la plus récente** :
   - Si JSON plus récent et mode SQL activé → Migre JSON → SQL
   - Si SQL plus récent et mode JSON activé → Migre SQL → JSON

### **Exemple de changement** :

```bash
# 1. Éditer config.ini
nano static/Conf/config.ini
# Changer: sql = true

# 2. Redémarrer le service
sudo systemctl restart plex-service

# 3. Vérifier les logs
tail -f /var/log/plex-service.log
# Vous verrez :
# [INFO] JSON downloads plus récent, migration JSON→SQL
# [INFO] Migration JSON→SQL: 3 downloads migrés
```

---

## 📊 Tables SQLite

### **downloads**
```sql
CREATE TABLE downloads (
    id TEXT PRIMARY KEY,
    torrent_name TEXT,
    torrent_path TEXT,
    save_path TEXT,
    username TEXT,
    status TEXT,  -- 'downloading', 'seeding', 'completed', 'stopped'
    progress REAL,
    total_size INTEGER,
    downloaded_size INTEGER,
    upload_rate REAL,
    download_rate REAL,
    peers INTEGER,
    created_at TIMESTAMP,
    started_at TIMESTAMP,
    finished_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### **seeds**
```sql
CREATE TABLE seeds (
    id TEXT PRIMARY KEY,
    torrent_name TEXT,
    torrent_path TEXT,
    data_path TEXT,
    username TEXT,
    status TEXT,  -- 'seeding', 'stopped'
    uploaded_size INTEGER,
    upload_rate REAL,
    peers INTEGER,
    created_at TIMESTAMP,
    stopped_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

---

## 🛠️ Commandes Utiles

### **Consulter la base SQLite**
```bash
sqlite3 /var/www/public/Plex-Service/data/plex_service.db

# Lister les downloads actifs
SELECT id, torrent_name, progress, status FROM downloads WHERE status = 'downloading';

# Historique complet
SELECT * FROM downloads ORDER BY created_at DESC LIMIT 10;

# Stats du mois
SELECT COUNT(*), SUM(total_size)/1073741824 as total_gb 
FROM downloads 
WHERE created_at >= date('now', '-1 month');
```

### **Backup de la base**
```bash
# Backup
cp /var/www/public/Plex-Service/data/plex_service.db ~/backup_$(date +%Y%m%d).db

# Restauration
cp ~/backup_20260210.db /var/www/public/Plex-Service/data/plex_service.db
sudo systemctl restart plex-service
```

### **Revenir à JSON (rollback)**
```bash
# 1. Éditer config
sudo nano /var/www/public/Plex-Service/static/Conf/config.ini
# sql = false

# 2. Redémarrer
sudo systemctl restart plex-service

# 3. Vérifier migration SQL→JSON dans les logs
tail -f /var/log/plex-service.log
```

---

## ⚠️ Important

1. **Pas de modification manuelle en cours d'exécution** :
   - Ne pas modifier directement `active_downloads.json` ou la BDD SQLite pendant que le service tourne

2. **Changement de mode** :
   - Toujours redémarrer le service après modification de `sql = true/false`
   - La migration se fait automatiquement au démarrage

3. **Backup avant changement** :
   ```bash
   # Backup JSON
   cp -r /var/www/public/Plex-Service/tmp/*.json ~/backup/
   
   # Backup SQLite
   cp /var/www/public/Plex-Service/data/plex_service.db ~/backup/
   ```

---

## 🎯 Avantages SQLite

✅ **Robustesse** : Transactions ACID, pas de corruption  
✅ **Historique** : Conservation des downloads terminés  
✅ **Stats** : Requêtes SQL pour analyses  
✅ **Thread-safe** : Pas besoin de fcntl  
✅ **Backup** : 1 seul fichier à copier  

## 🎯 Avantages JSON

✅ **Simplicité** : Édition manuelle facile  
✅ **Léger** : Pas de parsing SQL  
✅ **Debugging** : Lisible en direct  
✅ **Portable** : Copier/coller simple  

---

## 🔍 Troubleshooting

### **Problème : Migration ne se fait pas**
```bash
# Vérifier les timestamps
stat /var/www/public/Plex-Service/tmp/active_downloads.json

# Vérifier les logs
grep -i "migration" /var/log/plex-service.log
```

### **Problème : SQLite verrouillé**
```bash
# Vérifier les processus
lsof | grep plex_service.db

# Redémarrer proprement
sudo systemctl stop plex-service
sleep 2
sudo systemctl start plex-service
```

### **Problème : Données perdues**
```bash
# Restaurer depuis backup
cp ~/backup_DATE.db /var/www/public/Plex-Service/data/plex_service.db

# OU depuis JSON
# Éditer config: sql = false
# Redémarrer → migration JSON vers SQL automatique
```

---

**Date de création** : 10 février 2026  
**Version** : 1.0  
**Auteur** : System Optimization Phase 4
