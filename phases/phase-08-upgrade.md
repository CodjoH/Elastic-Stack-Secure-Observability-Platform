# Phase 08 : montée de version 7.17.10 vers 8.11.4

La 7.17 est la seule version depuis laquelle on peut passer en 8.x, le cluster était donc déjà au bon point de départ.

## Préparation

- snapshot complet ([backup-restore.md](../docs/backup-restore.md)), le dépôt est monté sur les deux nœuds (`path.repo`)
- Upgrade Assistant de Kibana : aucun problème critique côté Elasticsearch ni Kibana, quelques avertissements à relire, aucun appel d'API déprécié

![Upgrade Assistant](../screenshots/kibana/upgrade-assistant.jpg)

## Mise à jour nœud par nœud

```bash
# éviter que le cluster réplique tout pendant qu'un nœud redémarre
curl ... -X PUT "https://<ELK_HOST>:9200/_cluster/settings" -H 'Content-Type: application/json' \
  -d '{"persistent":{"cluster.routing.allocation.enable":"primaries"}}'

# image passée en 8.11.4 dans le docker-compose, puis un nœud à la fois
docker compose up -d elasticsearch-node2
docker compose up -d elasticsearch

curl ... -X PUT "https://<ELK_HOST>:9200/_cluster/settings" -H 'Content-Type: application/json' \
  -d '{"persistent":{"cluster.routing.allocation.enable":null}}'

# ensuite Kibana, puis Fleet Server, puis les agents
docker compose up -d kibana
```

## Incident 1 : agent local en DEGRADED

Juste après le passage en 8, l'agent de l'hôte central est passé en `DEGRADED`. La 8.x applique une restriction sur les chemins de CA par défaut et l'agent ne trouvait plus la CA.

Correction permanente avec un lien symbolique :

```bash
sudo mkdir -p /etc/elastic-agent/certs
sudo ln -sf <CERTS_DIR>/ca/ca.crt /etc/elastic-agent/certs/elk-ca.crt
sudo systemctl restart elastic-agent
sudo elastic-agent status
```

## Incident 2 : agents 7.x face au Fleet Server 8.x

Les agents étaient encore en 7.17.10 (voir la capture de la [phase 06](phase-06-fleet.md)). Pendant la transition, des erreurs de communication entre versions sont apparues. Plutôt que de réinstaller Client-Lin01, j'ai utilisé la mise à jour à distance de Fleet (Fleet > Agents > Upgrade agent) pour passer l'agent en 8.11.4 depuis Kibana, sans perte de données.

## Vérification

```bash
curl ... "https://<ELK_HOST>:9200/_cat/nodes?v&h=name,version"
./scripts/health-check.sh
./tests/authentication/test-authentication.sh
./tests/tls/test-tls.sh
./tests/ingestion/test-ingestion.sh
```

Les deux nœuds, Kibana, Fleet Server et Client-Lin01 sont en 8.11.4, cluster `green`.

> **Mise à jour :** en réalité, l'agent de Client-Lin01 s'était arrêté en 8.0.0 et a fini *Unhealthy*. La mise à jour à distance n'avait pas abouti. Diagnostic et correction : [phase 09](phase-09-fleet-troubleshooting.md).

Retour au [README](../README.md)
