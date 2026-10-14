# Phase 04 : Kibana en HTTPS

Deux liaisons à sécuriser : navigateur vers Kibana, et Kibana vers Elasticsearch.

## Navigateur vers Kibana

```yaml
server.ssl.enabled: true
server.ssl.certificate: config/certs/kibana/kibana.crt
server.ssl.key: config/certs/kibana/kibana.key
```

## Kibana vers Elasticsearch

```yaml
elasticsearch.hosts: [ "https://elasticsearch:9200" ]
elasticsearch.username: "kibana_system"
elasticsearch.password: "${KIBANA_SYSTEM_PASSWORD}"
elasticsearch.ssl.certificateAuthorities: [ "config/certs/ca/ca.crt" ]
```

Kibana n'utilise jamais le compte `elastic`. Les utilisateurs se connectent avec leur propre compte.

Dans le compose, ces paramètres sont passés en variables d'environnement (`ELASTICSEARCH_HOSTS`, `SERVER_SSL_ENABLED`…), voir [config/kibana](../config/kibana/README.md). Le mode de vérification n'étant pas précisé, Kibana applique `full` : le certificat `es-http` doit contenir le nom `elasticsearch`.

## Vérification

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://<ELK_HOST>:5601    # échoue
curl -s --cacert $CERTS_DIR/ca/ca.crt -u elastic:$ELASTIC_PASSWORD https://<ELK_HOST>:5601/api/status | grep -o '"level":"[a-z]*"'
```

Suite : [phase 05](phase-05-beats-authentication.md)
