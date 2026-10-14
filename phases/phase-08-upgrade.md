# Phase 08 — Montée de version majeure v7 ➔ v8.11.4

> **Objectif :** passer en v8 sans perte de données ni rupture de la collecte.

## Préparation

1. **Snapshot complet** avant toute action — voir [docs/backup-restore.md](../docs/backup-restore.md)
2. **Upgrade Assistant** de Kibana : correction des paramètres et index dépréciés
3. Mise à niveau préalable vers la dernière **7.17.x** (passage obligatoire vers la v8)

## Séquence : rolling upgrade

```bash
# 1. Désactiver l'allocation des réplicas pendant le redémarrage d'un nœud
curl ... -X PUT "https://192.168.56.51:9200/_cluster/settings" -H 'Content-Type: application/json' \
  -d '{"persistent":{"cluster.routing.allocation.enable":"primaries"}}'

# 2. Mettre à jour un nœud à la fois (STACK_VERSION=8.11.4 dans .env)
docker compose up -d es-node2      # puis es-node1

# 3. Réactiver l'allocation et attendre le statut green
curl ... -X PUT "https://192.168.56.51:9200/_cluster/settings" -H 'Content-Type: application/json' \
  -d '{"persistent":{"cluster.routing.allocation.enable":null}}'

# 4. Kibana, puis Fleet Server, puis les agents
docker compose up -d kibana
```

## Incidents & résolutions

### 🔴 Agent local en statut `DEGRADED` après le passage en v8

**Cause :** la v8 applique une restriction de sécurité sur les chemins de CA par défaut : l'agent ne trouvait plus l'autorité de certification.

**🟢 Résolution permanente :** lien symbolique système vers un emplacement autorisé :

```bash
sudo mkdir -p /etc/elastic-agent/certs
sudo ln -sf /home/cyber/certs/runtime/ca/ca.crt /etc/elastic-agent/certs/elk-ca.crt
sudo systemctl restart elastic-agent
sudo elastic-agent status    # ➔ HEALTHY
```

### 🔴 Conflits de communication inter-versions

**Cause :** des agents encore en v7 dialoguant avec un Fleet Server v8.

**🟢 Résolution :** utilisation du mécanisme d'**upgrade à distance de Fleet** : mise à niveau de `Client-Lin01` vers 8.11.4 directement depuis **Kibana ➔ Fleet ➔ Agents ➔ Upgrade agent**, sans intervention sur la machine et sans perte d'évènements.

## Validation

```bash
curl ... "https://192.168.56.51:9200/_cat/nodes?v&h=name,version"   # ➔ 8.11.4 sur les 2 nœuds
./scripts/health-check.sh
./tests/authentication/test-authentication.sh
./tests/tls/test-tls.sh
./tests/ingestion/test-ingestion.sh
```

## Résultat

✅ Stack entièrement en **v8.11.4** : cluster `green`, agents `Healthy`, aucune donnée perdue, collecte continue pendant toute l'opération.

⬅️ [Phase 07](phase-07-cluster.md) · 🏠 [Retour au README](../README.md)
