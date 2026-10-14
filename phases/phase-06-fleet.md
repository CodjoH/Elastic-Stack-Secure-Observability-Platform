# Phase 06 — Migration vers Elastic Agent & Fleet

> **Objectif :** remplacer les Beats par un agent unique, administré de façon centralisée depuis Kibana.

## Architecture cible

- **Fleet Server** installé en natif (bare-metal) sur l'hôte central `192.168.56.51`, port 8220
- **Elastic Agent** sur `Client-Lin01`, enrôlé auprès du Fleet Server
- Politiques de collecte (intégration *System*) définies une seule fois dans Kibana

## Actions

### 1. Jeton de service pour le Fleet Server

```bash
docker exec -it es-node1 bin/elasticsearch-service-tokens create elastic/fleet-server token-final
```

### 2. Installation du Fleet Server

```bash
sudo ./elastic-agent install --url=https://192.168.56.51:8220 \
  --fleet-server-es=https://192.168.56.51:9200 \
  --fleet-server-service-token=<TOKEN_GENERE> \
  --fleet-server-policy=<ID_POLITIQUE_FLEET_SERVER> \
  --certificate-authorities=/home/cyber/certs/runtime/ca/ca.crt \
  --fleet-server-es-ca=/home/cyber/certs/runtime/ca/ca.crt \
  --fleet-server-cert=/home/cyber/certs/runtime/kibana/kibana.crt \
  --fleet-server-cert-key=/home/cyber/certs/runtime/kibana/kibana.key
```

### 3. Enrôlement de Client-Lin01

```bash
sudo ./elastic-agent install --url=https://192.168.56.51:8220 \
  --enrollment-token=<JETON_ENROLEMENT_KIBANA> \
  --certificate-authorities=/etc/elastic-agent/certs/elk-ca.crt
```

### 4. Retrait des Beats

```bash
sudo systemctl disable --now filebeat metricbeat
```

## Bénéfices sécurité

| Avant (Beats) | Après (Fleet) |
|---|---|
| Mot de passe statique sur chaque machine | Clés d'API générées et renouvelées par Fleet |
| Configuration locale modifiable | Politique centralisée et versionnée dans Kibana |
| Mises à jour manuelles | Mises à jour pilotées à distance |

## Validation

```bash
sudo elastic-agent status          # ➔ HEALTHY
curl -s --cacert certs/runtime/ca/ca.crt https://192.168.56.51:8220/api/status   # ➔ "HEALTHY"
./tests/ingestion/test-ingestion.sh
```

## Résultat

✅ Agents visibles et `Healthy` dans **Kibana ➔ Fleet**, données `logs-system.*` et `metrics-system.*` reçues.

⬅️ [Phase 05](phase-05-beats-authentication.md) · ➡️ [Phase 07 — Cluster](phase-07-cluster.md)
