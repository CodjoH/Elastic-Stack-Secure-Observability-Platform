# Configuration Kibana

Kibana est configuré par variables d'environnement dans le [docker-compose.yml](../../docker-compose.yml). Équivalent `kibana.yml` :

```yaml
elasticsearch.hosts: [ "https://elasticsearch:9200" ]
elasticsearch.username: "kibana_system"
elasticsearch.password: "${KIBANA_SYSTEM_PASSWORD}"
elasticsearch.ssl.certificateAuthorities: [ "/usr/share/kibana/config/certs/ca/ca.crt" ]

server.ssl.enabled: true
server.ssl.certificate: /usr/share/kibana/config/certs/kibana/kibana.crt
server.ssl.key: /usr/share/kibana/config/certs/kibana/kibana.key
```

- Kibana parle à Elasticsearch avec `kibana_system`, jamais avec `elastic`
- `verificationMode` n'est pas précisé, donc `full` par défaut : le certificat `es-http` doit contenir le nom `elasticsearch`
- le certificat `kibana` sert aussi au Fleet Server sur le port 8220
