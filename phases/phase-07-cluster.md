# Phase 07 : passage à deux nœuds

Objectif : que les données survivent à la perte d'un nœud.

`curl ...` ci-dessous = `curl --cacert $CERTS_DIR/ca/ca.crt -u elastic:$ELASTIC_PASSWORD`

## Incident : UnavailableShardsException sur `.security`

En réorganisant le réseau pour préparer l'ajout du deuxième nœud, l'index `.security` est devenu indisponible (`UnavailableShardsException`). Conséquence directe : plus aucune authentification possible, donc plus d'accès à Kibana.

Diagnostic :

```bash
curl ... "https://<ELK_HOST>:9200/_cat/shards/.security*?v"
curl ... "https://<ELK_HOST>:9200/_cluster/allocation/explain?pretty"
```

Stabilisation temporaire : réplicas des index système à 0 pour revenir à un état sain avant d'ajouter le nœud.

```bash
curl ... -X PUT "https://<ELK_HOST>:9200/.security-*/_settings" -H 'Content-Type: application/json' \
  -d '{"index":{"number_of_replicas":0}}'
curl ... -X POST "https://<ELK_HOST>:9200/_cluster/reroute?retry_failed=true"
```

## Ajout du deuxième nœud

Nouveau service `elasticsearch-node2` (nœud `es-node2`) dans le [docker-compose](../docker-compose.yml) :

- même `cluster.name`, découverte croisée (`discovery.seed_hosts` pointe sur l'autre conteneur)
- mêmes paramètres de sécurité, certificat transport `es-node2/` (phase 03)
- port 9200 non publié : seul le premier nœud est exposé sur l'hôte
- `discovery.type: single-node` retiré du premier nœud

```bash
docker compose up -d elasticsearch-node2
curl ... "https://<ELK_HOST>:9200/_cat/nodes?v"
```

Puis réplicas remis à 1 :

```bash
curl ... -X PUT "https://<ELK_HOST>:9200/_all/_settings" -H 'Content-Type: application/json' \
  -d '{"index":{"number_of_replicas":1}}'
```

Résultat dans Kibana : tous les index des Beats en `green` avec 1 réplica, ce qui n'est possible qu'avec deux nœuds.

![index en green avec 1 réplica](../Proof/kibana/index-management-replicas.jpg)

## Test de panne

```bash
docker stop elasticsearch-node2
curl ... "https://<ELK_HOST>:9200/_cluster/health"      # yellow, les données restent accessibles
./tests/ingestion/test-ingestion.sh                      # l'ingestion continue

docker start elasticsearch-node2
curl ... "https://<ELK_HOST>:9200/_cluster/health?wait_for_status=green&timeout=120s"
```

L'arrêt du second nœud ne coupe ni l'accès ni la collecte, et les réplicas se reconstruisent à son retour. Avec seulement deux nœuds master-eligible, ce n'est pas vrai dans tous les cas : voir [architecture](../docs/architecture.md#limite-connue).

Suite : [phase 08](phase-08-upgrade.md)
