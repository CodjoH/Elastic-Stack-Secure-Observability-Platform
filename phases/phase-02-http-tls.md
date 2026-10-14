# Phase 02 — Chiffrement de l'API REST (HTTPS 9200)

> **Objectif :** empêcher l'interception des identifiants et des données échangées avec l'API.

## Pourquoi

Après la phase 01, les identifiants circulent en **Basic Auth** : sans TLS, ils transitent en clair (encodage Base64 seulement) et peuvent être capturés par simple écoute réseau.

## Actions

1. Création de la CA interne et du certificat HTTP — voir [docs/certificates.md](../docs/certificates.md).
2. Activation de TLS sur la couche HTTP :

```yaml
xpack.security.http.ssl:
  enabled: true
  certificate: certs/es-http/elasticsearch.crt
  key: certs/es-http/elasticsearch.key
  certificate_authorities: [ "certs/ca/ca.crt" ]
```

3. Mise à jour de tous les clients (`curl`, Kibana, Beats) pour utiliser `https://` et faire confiance à la CA.

## Validation

```bash
# Le HTTP en clair doit échouer
curl -s http://192.168.56.51:9200          # ➔ connexion refusée / réponse vide

# HTTPS avec vérification de la CA
curl --cacert certs/runtime/ca/ca.crt -u elastic:$ELASTIC_PASSWORD https://192.168.56.51:9200

# Poignée de main TLS
openssl s_client -connect 192.168.56.51:9200 -CAfile certs/runtime/ca/ca.crt </dev/null | grep "Verify return code"
# ➔ Verify return code: 0 (ok)
```

## Résultat

✅ L'API n'accepte plus que des connexions HTTPS dont le certificat est vérifiable par la CA interne.

⬅️ [Phase 01](phase-01-authentication.md) · ➡️ [Phase 03 — TLS Transport](phase-03-transport-tls.md)
