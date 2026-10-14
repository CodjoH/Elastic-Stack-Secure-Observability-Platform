# Sauvegarde et restauration

Snapshots Elasticsearch vers un dépôt de type `fs`. Le chemin est déclaré dans `path.repo` sur les deux nœuds et monté sur le volume `snapshots` du docker-compose.

Variables utilisées dans les commandes :

```bash
ES="https://$ELK_HOST:9200"
C="curl --cacert $CERTS_DIR/ca/ca.crt -u elastic:$ELASTIC_PASSWORD"
```

## Déclarer le dépôt

```bash
$C -X PUT "$ES/_snapshot/local_fs" -H 'Content-Type: application/json' -d '{
  "type": "fs",
  "settings": { "location": "/usr/share/elasticsearch/snapshots", "compress": true }
}'
$C -X POST "$ES/_snapshot/local_fs/_verify"
```

## Snapshot manuel

À faire avant une opération à risque, en particulier avant la montée de version :

```bash
$C -X PUT "$ES/_snapshot/local_fs/pre-upgrade?wait_for_completion=true" \
  -H 'Content-Type: application/json' -d '{"indices":"*","include_global_state":true}'
```

## Snapshots planifiés (SLM)

```bash
$C -X PUT "$ES/_slm/policy/nightly" -H 'Content-Type: application/json' -d '{
  "schedule": "0 30 1 * * ?",
  "name": "<nightly-{now/d}>",
  "repository": "local_fs",
  "config": { "indices": "*", "include_global_state": true },
  "retention": { "expire_after": "14d", "min_count": 3, "max_count": 14 }
}'
```

## Restaurer

```bash
$C "$ES/_cat/snapshots/local_fs?v"

# restauration sous un autre nom pour ne pas écraser l'index existant
$C -X POST "$ES/_snapshot/local_fs/<snapshot>/_restore" -H 'Content-Type: application/json' -d '{
  "indices": "logs-system.syslog-*",
  "rename_pattern": "(.+)",
  "rename_replacement": "restored-$1"
}'
```

## Remarques

- ici le dépôt est sur le même hôte que le cluster ; en production il faudrait un stockage externe (NFS, S3)
- une restauration doit être testée régulièrement, sinon on ne sait pas si la sauvegarde est exploitable
