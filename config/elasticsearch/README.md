# Configuration Elasticsearch

La configuration est passée en variables d'environnement dans le [docker-compose.yml](../../docker-compose.yml), pas dans un `elasticsearch.yml` monté. Récapitulatif des paramètres de sécurité :

| Paramètre | es-node1 | es-node2 |
|---|---|---|
| `cluster.name` | cyber-cluster | cyber-cluster |
| `xpack.security.enabled` | true | true |
| `xpack.security.http.ssl.enabled` | true | true |
| `xpack.security.http.ssl.certificate` | `es-http/elasticsearch.crt` | `es-http/elasticsearch.crt` |
| `xpack.security.http.ssl.client_authentication` | optional | (défaut : none) |
| `xpack.security.transport.ssl.enabled` | true | true |
| `xpack.security.transport.ssl.verification_mode` | certificate | certificate |
| certificat transport | `es-node1/es-node1.crt` | `es-node2/es-node2.crt` |
| `path.repo` | `/usr/share/elasticsearch/snapshots` | `/usr/share/elasticsearch/snapshots` |
| `bootstrap.memory_lock` | true | true |

Les deux nœuds partagent le certificat HTTP (`es-http`) : c'est la même API exposée, seul es-node1 publie le port 9200 sur l'hôte.

`instances.yml` est un exemple de définition pour régénérer les certificats avec `elasticsearch-certutil` (voir [docs/certificates.md](../../docs/certificates.md)).
