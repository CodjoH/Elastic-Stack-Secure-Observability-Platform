# Phase 03 — mTLS inter-nœuds (Transport 9300)

> **Objectif :** chiffrer la réplication et empêcher un nœud non autorisé de rejoindre le cluster.

## Pourquoi

La couche transport véhicule la réplication des données et l'état du cluster. Sans authentification mutuelle, n'importe quelle machine connaissant le `cluster.name` pourrait tenter de rejoindre le cluster et recevoir des copies des données.

## Actions

Un certificat par nœud, signé par la même CA :

```yaml
xpack.security.transport.ssl:
  enabled: true
  verification_mode: certificate     # vérifie la signature par la CA
  client_authentication: required    # chaque nœud doit présenter son certificat
  certificate: certs/es-node1/es-node1.crt
  key: certs/es-node1/es-node1.key
  certificate_authorities: [ "certs/ca/ca.crt" ]
```

> `verification_mode: certificate` valide la chaîne de confiance sans contrôler le nom d'hôte — adapté à un réseau Docker où les noms internes varient. En production multi-hôtes, `full` est recommandé.

## Validation

```bash
# Les deux nœuds sont visibles : la poignée de main mTLS fonctionne
curl --cacert certs/runtime/ca/ca.crt -u elastic:$ELASTIC_PASSWORD "https://<ELK_HOST_IP>:9200/_cat/nodes?v"

# Un nœud sans certificat valide est rejeté (dans les logs) :
docker logs es-node1 2>&1 | grep -i "handshake"
```

## Résultat

✅ Toute communication entre nœuds est chiffrée et authentifiée des deux côtés, ce qui protège le quorum du cluster.

⬅️ [Phase 02](phase-02-http-tls.md) · ➡️ [Phase 04 — Kibana HTTPS](phase-04-kibana-https.md)
