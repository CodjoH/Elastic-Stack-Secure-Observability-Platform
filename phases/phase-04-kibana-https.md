# Phase 04 — Kibana en HTTPS

> **Objectif :** sécuriser l'accès utilisateur et la liaison Kibana ➔ Elasticsearch.

## Actions

### 1. HTTPS côté navigateur

```yaml
server.ssl.enabled: true
server.ssl.certificate: config/certs/kibana/kibana.crt
server.ssl.key: config/certs/kibana/kibana.key
```

### 2. Connexion sécurisée vers Elasticsearch avec un compte restreint

```yaml
elasticsearch.hosts: [ "https://es-node1:9200" ]
elasticsearch.username: "kibana_system"
elasticsearch.password: "${KIBANA_SYSTEM_PASSWORD}"
elasticsearch.ssl.certificateAuthorities: [ "config/certs/ca/ca.crt" ]
elasticsearch.ssl.verificationMode: full
```

### 3. Clés de chiffrement

`xpack.encryptedSavedObjects.encryptionKey` est indispensable pour Fleet et les règles d'alerte : sans elle, les secrets enregistrés dans Kibana ne peuvent pas être chiffrés.

Configuration complète : [config/kibana/kibana.yml](../config/kibana/kibana.yml)

## Validation

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://<ELK_HOST_IP>:5601     # ➔ échec (clair refusé)
curl -s --cacert certs/runtime/ca/ca.crt https://<ELK_HOST_IP>:5601/api/status -u elastic:$ELASTIC_PASSWORD | grep available
```

## Résultat

✅ Interface accessible uniquement en HTTPS ; Kibana n'utilise jamais le superutilisateur.

⬅️ [Phase 03](phase-03-transport-tls.md) · ➡️ [Phase 05 — Authentification des Beats](phase-05-beats-authentication.md)
