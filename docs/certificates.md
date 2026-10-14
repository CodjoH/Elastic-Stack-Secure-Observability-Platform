# Certificats

Une CA interne signe tous les certificats de la plateforme.

## Arborescence sur l'hôte

`<CERTS_DIR>` correspond au répertoire des certificats sur l'hôte central (variable `CERTS_DIR` du `.env`).

```
<CERTS_DIR>/
├── ca/ca.crt
├── es-http/elasticsearch.crt
├── es-http/elasticsearch.key
├── es-node1/es-node1.crt
├── es-node1/es-node1.key
├── es-node2/es-node2.crt
├── es-node2/es-node2.key
├── kibana/kibana.crt
└── kibana/kibana.key
```

| Dossier | Utilisé par |
|---|---|
| `ca/` | tous les clients (curl, Kibana, Beats, agents) |
| `es-http/` | API Elasticsearch 9200 |
| `es-node1/`, `es-node2/` | transport 9300 |
| `kibana/` | Kibana 5601 et Fleet Server 8220 |

Rien de ce dossier n'est versionné. La clé de la CA reste hors du serveur.

## Génération

CA :

```bash
docker run --rm -v "$PWD/certs:/certs" docker.elastic.co/elasticsearch/elasticsearch:8.11.4 \
  bin/elasticsearch-certutil ca --pem --out /certs/ca.zip
unzip certs/ca.zip -d certs/runtime
```

Certificats, à partir de [instances.yml](../config/elasticsearch/instances.yml) (mettre l'IP réelle dans le fichier avant) :

```bash
docker run --rm -v "$PWD/certs:/certs" -v "$PWD/config/elasticsearch:/cfg" \
  docker.elastic.co/elasticsearch/elasticsearch:8.11.4 \
  bin/elasticsearch-certutil cert --pem \
    --ca-cert /certs/runtime/ca/ca.crt --ca-key /certs/runtime/ca/ca.key \
    --in /cfg/instances.yml --out /certs/bundle.zip
unzip certs/bundle.zip -d certs/runtime
mv certs/runtime/elasticsearch certs/runtime/es-http
```

Droits :

```bash
chmod 600 certs/runtime/*/*.key
chown -R 1000:0 certs/runtime
```

## Côté agents

```bash
sudo mkdir -p /etc/elastic-agent/certs
sudo cp ca.crt /etc/elastic-agent/certs/elk-ca.crt
```

C'est ce chemin qui a réglé le statut DEGRADED après le passage en 8 (voir [phase 08](../phases/phase-08-upgrade.md)).

## Contrôles

```bash
openssl verify -CAfile $CERTS_DIR/ca/ca.crt $CERTS_DIR/es-http/elasticsearch.crt
openssl x509 -in $CERTS_DIR/es-http/elasticsearch.crt -noout -ext subjectAltName
openssl x509 -in $CERTS_DIR/es-http/elasticsearch.crt -noout -enddate
```

[scripts/verify-tls.sh](../scripts/verify-tls.sh) fait la même chose sur les ports ouverts.
