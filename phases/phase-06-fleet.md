# Phase 06 : Elastic Agent et Fleet

Remplacer les Beats par un agent unique géré depuis Kibana.

- Fleet Server installé directement sur l'hôte central (port 8220)
- Elastic Agent sur Client-Lin01, enrôlé auprès du Fleet Server
- politique avec l'intégration System, définie une seule fois dans Kibana

Cette phase a été faite en 7.17.10. Les agents ont été passés en 8.11.4 en phase 08.

## Service token pour le Fleet Server

```bash
docker exec -it elasticsearch bin/elasticsearch-service-tokens create elastic/fleet-server <nom_du_token>
```

Le token n'est affiché qu'une fois et n'est conservé nulle part dans le dépôt.

## Installation du Fleet Server

```bash
sudo ./elastic-agent install --url=https://<ELK_HOST>:8220 \
  --fleet-server-es=https://<ELK_HOST>:9200 \
  --fleet-server-service-token=<SERVICE_TOKEN> \
  --fleet-server-policy=<FLEET_SERVER_POLICY_ID> \
  --certificate-authorities=<CERTS_DIR>/ca/ca.crt \
  --fleet-server-es-ca=<CERTS_DIR>/ca/ca.crt \
  --fleet-server-cert=<CERTS_DIR>/kibana/kibana.crt \
  --fleet-server-cert-key=<CERTS_DIR>/kibana/kibana.key
```

Le Fleet Server réutilise le certificat Kibana, dont le SAN couvre l'IP de l'hôte.

## Enrôlement de Client-Lin01

```bash
sudo ./elastic-agent install --url=https://<ELK_HOST>:8220 \
  --enrollment-token=<ENROLLMENT_TOKEN> \
  --certificate-authorities=/etc/elastic-agent/certs/elk-ca.crt
```

Les jetons d'enrôlement sont gérés dans Fleet > Enrollment tokens (secrets floutés) :

![jetons d'enrôlement](../screenshots/kibana/fleet-enrollment-tokens.jpg)

Puis arrêt des Beats :

```bash
sudo systemctl disable --now filebeat metricbeat auditbeat heartbeat packetbeat
```

## Ce que ça change

| Beats | Fleet |
|---|---|
| mot de passe stocké sur chaque machine | clés d'API générées par Fleet pour chaque agent |
| configuration locale | politique centralisée dans Kibana |
| mises à jour à la main | mises à jour lancées depuis Kibana |

## Vérification

```bash
sudo elastic-agent status
curl -s --cacert $CERTS_DIR/ca/ca.crt https://<ELK_HOST>:8220/api/status
./tests/ingestion/test-ingestion.sh
```

Les deux agents (l'hôte ELK qui porte le Fleet Server, et Client-Lin01) remontent `Healthy`, encore en 7.17.10. Kibana signale déjà « Upgrade available », traité en phase 08.

![agents Fleet en 7.17.10](../screenshots/kibana/fleet-agents-7.17.10.jpg)

Suite : [phase 07](phase-07-cluster.md)
