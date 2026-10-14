# Phase 03 : mTLS entre les nœuds (9300)

Le port 9300 transporte la réplication et l'état du cluster. Sans authentification mutuelle, une machine qui connaît le `cluster.name` peut essayer de rejoindre le cluster. C'est aussi un prérequis pour passer à plusieurs nœuds avec la sécurité activée.

## Configuration

Un certificat par nœud (`es-node1/`, `es-node2/`), tous signés par la même CA. Pour es-node1 :

```yaml
# passé en variables d'environnement dans le docker-compose
xpack.security.transport.ssl.enabled: true
xpack.security.transport.ssl.verification_mode: certificate
xpack.security.transport.ssl.certificate: certs/es-node1/es-node1.crt
xpack.security.transport.ssl.key: certs/es-node1/es-node1.key
xpack.security.transport.ssl.certificate_authorities: [ "certs/ca/ca.crt" ]
```

`client_authentication` n'est pas précisé : sur la couche transport, la valeur par défaut est `required`, chaque nœud doit donc présenter son certificat.

`verification_mode: certificate` vérifie la signature par la CA mais pas le nom d'hôte. Ça suffit ici parce que seuls les certificats émis par la CA interne sont acceptés. Sur plusieurs machines physiques, `full` serait préférable.

## Vérification

```bash
curl --cacert $CERTS_DIR/ca/ca.crt -u elastic:$ELASTIC_PASSWORD "https://<ELK_HOST>:9200/_cat/nodes?v"
docker logs elasticsearch 2>&1 | grep -i handshake    # erreurs si un nœud présente un mauvais certificat
```

Suite : [phase 04](phase-04-kibana-https.md)
