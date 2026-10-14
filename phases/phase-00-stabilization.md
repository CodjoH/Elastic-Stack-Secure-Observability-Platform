# Phase 00 — Stabilisation de l'existant

> **Objectif :** partir d'une base saine (cluster `green`) avant tout durcissement.

## Contexte

État initial : une Elastic Stack v7 sur un nœud unique, sans chiffrement, dont le statut oscillait entre `yellow` et `red` après une réorganisation réseau.

## Diagnostic

```bash
curl -s "http://localhost:9200/_cluster/health?pretty"
curl -s "http://localhost:9200/_cat/shards?v&h=index,shard,prirep,state,unassigned.reason"
curl -s "http://localhost:9200/_cluster/allocation/explain?pretty"
```

## 🔴 Incident : `UnavailableShardsException` sur l'index `.security`

**Symptôme :** les requêtes d'authentification échouaient ; l'index système `.security` avait des shards non alloués.

**Cause :** sur un nœud unique, les réplicas ne peuvent jamais être alloués (un réplica ne peut pas résider sur le même nœud que son primaire). La réorganisation réseau a bloqué l'allocation et laissé l'index système dans un état indisponible.

## 🟢 Résolution

Stabilisation transitoire en forçant à 0 le nombre de réplicas des index système, le temps d'ajouter le second nœud :

```bash
curl -X PUT "http://localhost:9200/.security-*/_settings" -H 'Content-Type: application/json' -d '{
  "index": { "number_of_replicas": 0, "auto_expand_replicas": "0-1" }
}'

# Relancer les allocations en échec
curl -X POST "http://localhost:9200/_cluster/reroute?retry_failed=true"
```

> `auto_expand_replicas: 0-1` permet aux réplicas de réapparaître automatiquement dès que le second nœud rejoint le cluster ([phase 07](phase-07-cluster.md)).

## Validation

```bash
curl -s "http://localhost:9200/_cluster/health" | grep '"status":"green"'
```

## Résultat

✅ Cluster `green`, index `.security` disponible, base saine pour la suite du durcissement.

➡️ Suite : [Phase 01 — Authentification](phase-01-authentication.md)
