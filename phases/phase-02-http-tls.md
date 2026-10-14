# Phase 02 : HTTPS sur l'API (9200)

Avec la phase 01, les identifiants circulent en Basic Auth : simple encodage base64, lisible par n'importe qui sur le réseau. Il faut chiffrer.

## Mise en place

1. Création de la CA interne et du certificat `es-http` ([docs/certificates.md](../docs/certificates.md))
2. Configuration :

```yaml
xpack.security.http.ssl.enabled: true
xpack.security.http.ssl.certificate: certs/es-http/elasticsearch.crt
xpack.security.http.ssl.key: certs/es-http/elasticsearch.key
xpack.security.http.ssl.certificate_authorities: [ "certs/ca/ca.crt" ]
```

3. Passage de tous les clients (curl, Kibana, Beats) en `https://` avec la CA

## Vérification

```bash
curl -s http://<ELK_HOST>:9200          # échoue
curl --cacert $CERTS_DIR/ca/ca.crt -u elastic:$ELASTIC_PASSWORD https://<ELK_HOST>:9200
openssl s_client -connect <ELK_HOST>:9200 -CAfile $CERTS_DIR/ca/ca.crt </dev/null | grep "Verify return code"
# Verify return code: 0 (ok)
```

Le SAN du certificat doit contenir l'IP ou le nom utilisé par les clients, sinon la vérification échoue côté Kibana (`verificationMode: full`).

Suite : [phase 03](phase-03-transport-tls.md)
