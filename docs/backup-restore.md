# 💾 Sauvegarde & restauration

Procédure de sauvegarde par **snapshots Elasticsearch** vers un dépôt de type système de fichiers partagé entre les nœuds.

## 1. Déclarer le dépôt

Le chemin est autorisé dans la configuration des deux nœuds (`path.repo`) et monté sur le volume `snapshots` du [docker-compose.yml](../docker-compose.yml).

```bash
curl --cacert certs/runtime/ca/ca.crt -u elastic:$ELASTIC_PASSWORD \
  -X PUT "https://<ELK_HOST_IP>:9200/_snapshot/local_fs" -H 'Content-Type: application/json' -d '{
    "type": "fs",
    "settings": { "location": "/usr/share/elasticsearch/snapshots", "compress": true }
  }'

# Vérifier que tous les nœuds accèdent au dépôt
curl --cacert certs/runtime/ca/ca.crt -u elastic:$ELASTIC_PASSWORD \
  -X POST "https://<ELK_HOST_IP>:9200/_snapshot/local_fs/_verify"
```

## 2. Snapshot manuel (avant toute opération sensible)

Indispensable **avant la montée de version v7 ➔ v8** :

```bash
curl --cacert certs/runtime/ca/ca.crt -u elastic:$ELASTIC_PASSWORD \
  -X PUT "https://<ELK_HOST_IP>:9200/_snapshot/local_fs/pre-upgrade-$(date +%F)?wait_for_completion=true" \
  -H 'Content-Type: application/json' -d '{ "indices": "*", "include_global_state": true }'
```

## 3. Snapshots automatiques (SLM)

```bash
curl --cacert certs/runtime/ca/ca.crt -u elastic:$ELASTIC_PASSWORD \
  -X PUT "https://<ELK_HOST_IP>:9200/_slm/policy/nightly" -H 'Content-Type: application/json' -d '{
    "schedule": "0 30 1 * * ?",
    "name": "<nightly-{now/d}>",
    "repository": "local_fs",
    "config": { "indices": "*", "include_global_state": true },
    "retention": { "expire_after": "14d", "min_count": 3, "max_count": 14 }
  }'
```

## 4. Restauration

```bash
# Lister les snapshots disponibles
curl --cacert certs/runtime/ca/ca.crt -u elastic:$ELASTIC_PASSWORD \
  "https://<ELK_HOST_IP>:9200/_cat/snapshots/local_fs?v"

# Restaurer un index précis sous un nouveau nom (sans écraser l'existant)
curl --cacert certs/runtime/ca/ca.crt -u elastic:$ELASTIC_PASSWORD \
  -X POST "https://<ELK_HOST_IP>:9200/_snapshot/local_fs/<SNAPSHOT>/_restore" \
  -H 'Content-Type: application/json' -d '{
    "indices": "logs-system.syslog-*",
    "rename_pattern": "(.+)",
    "rename_replacement": "restored-$1"
  }'
```

## Bonnes pratiques

- Stocker les snapshots **hors de l'hôte** du cluster (NFS, S3) en production.
- Tester régulièrement une restauration : une sauvegarde non testée n'est pas une sauvegarde.
- Restreindre la gestion des snapshots à un rôle dédié (`manage_slm`, `create_snapshot`).
