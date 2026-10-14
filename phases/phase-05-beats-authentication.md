# Phase 05 — Authentification des Beats

> **Objectif :** que les collecteurs historiques (Filebeat, Metricbeat) continuent d'envoyer des données sur une stack désormais chiffrée et authentifiée, avec des droits minimaux.

## Actions

### 1. Rôle d'écriture minimal

Rôle défini dans [config/beats/beats-writer-role.json](../config/beats/beats-writer-role.json) : création de documents uniquement, sur les index des Beats.

```bash
curl --cacert certs/runtime/ca/ca.crt -u elastic:$ELASTIC_PASSWORD \
  -X PUT "https://192.168.56.51:9200/_security/role/beats_writer" \
  -H 'Content-Type: application/json' -d @config/beats/beats-writer-role.json

curl --cacert certs/runtime/ca/ca.crt -u elastic:$ELASTIC_PASSWORD \
  -X PUT "https://192.168.56.51:9200/_security/user/filebeat_writer" \
  -H 'Content-Type: application/json' -d '{"password":"<MDP_ROBUSTE>","roles":["beats_writer"]}'
```

### 2. Configuration des Beats

- Sortie `https://` avec la CA interne et `ssl.verification_mode: full`
- Mot de passe stocké dans le **keystore** du Beat, jamais en clair dans le fichier :

```bash
sudo filebeat keystore create
sudo filebeat keystore add FILEBEAT_PASSWORD
```

Fichiers : [filebeat.yml](../config/beats/filebeat.yml) · [metricbeat.yml](../config/beats/metricbeat.yml)

## Validation

```bash
sudo filebeat test output
# ➔ talk to server... OK / TLS... OK
```

## Limites constatées ➔ motivation de la phase 06

- Configuration et secrets à maintenir **sur chaque machine**
- Mises à jour manuelles, machine par machine
- Un binaire différent par type de donnée (logs, métriques…)

⬅️ [Phase 04](phase-04-kibana-https.md) · ➡️ [Phase 06 — Fleet](phase-06-fleet.md)
