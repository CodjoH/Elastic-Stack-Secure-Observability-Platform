# Phase 07 — Passage en cluster distribué

> **Objectif :** supprimer le point unique de défaillance et garantir la disponibilité des données.

## Actions

### 1. Ajout de `es-node2`

- Rôle : données + réplicas ([es-node2.yml](../config/elasticsearch/es-node2.yml))
- Certificat transport dédié signé par la CA ([phase 03](phase-03-transport-tls.md))
- Découverte via `discovery.seed_hosts: [ "es-node1", "es-node2" ]`

```bash
docker compose up -d es-node2
```

### 2. Rétablissement des réplicas

Les réplicas mis à 0 en [phase 00](phase-00-stabilization.md) sont restaurés :

```bash
curl --cacert certs/runtime/ca/ca.crt -u elastic:$ELASTIC_PASSWORD \
  -X PUT "https://<ELK_HOST_IP>:9200/_all/_settings" -H 'Content-Type: application/json' \
  -d '{"index":{"number_of_replicas":1}}'
```

### 3. Retrait de `cluster.initial_master_nodes`

Paramètre à n'utiliser qu'au tout premier démarrage : il est retiré une fois le cluster formé.

## Test de résilience (failover)

```bash
# 1. Cluster nominal
curl ... "https://<ELK_HOST_IP>:9200/_cluster/health"        # ➔ green, 2 nœuds

# 2. Simulation de panne du nœud secondaire
docker stop es-node2
curl ... "https://<ELK_HOST_IP>:9200/_cluster/health"        # ➔ yellow : données toujours accessibles
./tests/ingestion/test-ingestion.sh                           # ➔ l'ingestion continue

# 3. Retour du nœud
docker start es-node2
curl ... "https://<ELK_HOST_IP>:9200/_cluster/health?wait_for_status=green&timeout=120s"   # ➔ green
```

## Résultat

✅ La perte d'un nœud de données n'entraîne ni perte de données ni interruption de la collecte ; les shards sont reconstruits automatiquement à son retour.

> 💡 Amélioration : un 3ᵉ nœud maître éligible permettrait aussi de tolérer la perte du maître (quorum à 2 sur 3).

⬅️ [Phase 06](phase-06-fleet.md) · ➡️ [Phase 08 — Montée de version](phase-08-upgrade.md)
