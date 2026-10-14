# 🔑 Gestion des certificats (PKI interne)

Toute la confiance de la plateforme repose sur une **autorité de certification racine interne**. Elle signe les certificats HTTP, transport, Kibana et Fleet Server.

## Arborescence attendue

```
certs/runtime/
├── ca/
│   └── ca.crt                 # CA racine (publique, distribuée aux clients)
├── es-http/
│   ├── elasticsearch.crt      # API REST 9200
│   └── elasticsearch.key
├── es-node1/                  # Transport mTLS 9300
│   ├── es-node1.crt
│   └── es-node1.key
├── es-node2/
│   ├── es-node2.crt
│   └── es-node2.key
└── kibana/
    ├── kibana.crt             # Kibana 5601 + Fleet Server 8220
    └── kibana.key
```

> ⚠️ Le dossier `certs/` est exclu du dépôt. Seule la CA **publique** (`ca.crt`) doit être distribuée ; la clé de la CA reste hors ligne.

## 1. Créer la CA

```bash
docker run --rm -v "$PWD/certs:/certs" docker.elastic.co/elasticsearch/elasticsearch:8.11.4 \
  bin/elasticsearch-certutil ca --pem --out /certs/ca.zip
unzip certs/ca.zip -d certs/runtime
```

## 2. Émettre les certificats

Les noms DNS et IP sont définis dans [`config/elasticsearch/instances.yml`](../config/elasticsearch/instances.yml).

```bash
docker run --rm -v "$PWD/certs:/certs" -v "$PWD/config/elasticsearch:/cfg" \
  docker.elastic.co/elasticsearch/elasticsearch:8.11.4 \
  bin/elasticsearch-certutil cert --pem \
    --ca-cert /certs/runtime/ca/ca.crt --ca-key /certs/runtime/ca/ca.key \
    --in /cfg/instances.yml --out /certs/bundle.zip
unzip certs/bundle.zip -d certs/runtime
mv certs/runtime/elasticsearch certs/runtime/es-http
```

## 3. Restreindre les permissions

```bash
chmod 600 certs/runtime/*/*.key
chown -R 1000:0 certs/runtime   # UID de l'utilisateur elasticsearch dans le conteneur
```

## 4. Distribuer la CA aux agents

Sur chaque machine équipée d'Elastic Agent :

```bash
sudo mkdir -p /etc/elastic-agent/certs
sudo cp ca.crt /etc/elastic-agent/certs/elk-ca.crt
```

> 💡 En v8, l'agent ne lit plus la CA depuis certains chemins par défaut : un lien symbolique vers `/etc/elastic-agent/certs/elk-ca.crt` a résolu le statut `DEGRADED` (voir [phase 08](../phases/phase-08-upgrade.md)).

## 5. Empreinte de la CA (Fleet)

Fleet peut épingler la CA par son empreinte SHA-256 (`ca_trusted_fingerprint` dans [`kibana.yml`](../config/kibana/kibana.yml)) :

```bash
openssl x509 -in certs/runtime/ca/ca.crt -noout -fingerprint -sha256 | cut -d= -f2 | tr -d ':'
```

## 6. Contrôles

```bash
# Vérifier qu'un certificat est bien signé par la CA
openssl verify -CAfile certs/runtime/ca/ca.crt certs/runtime/es-http/elasticsearch.crt

# Vérifier les SAN (noms et IP couverts)
openssl x509 -in certs/runtime/es-http/elasticsearch.crt -noout -ext subjectAltName

# Date d'expiration
openssl x509 -in certs/runtime/es-http/elasticsearch.crt -noout -enddate
```

Le script [`scripts/verify-tls.sh`](../scripts/verify-tls.sh) automatise ces vérifications sur les ports exposés.
