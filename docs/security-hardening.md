# Durcissement

## Flux et protection

| Flux | Port | Protocole | Authentification / confiance |
|---|---|---|---|
| API Elasticsearch | 9200 | HTTPS | certificat signé par la CA interne, identifiants obligatoires |
| Transport entre nœuds | 9300 | mTLS | `verification_mode: certificate`, CA partagée |
| Kibana | 5601 | HTTPS | Kibana se connecte à ES avec `kibana_system` |
| Enrôlement Fleet Server | 8220 | HTTPS | service token Elasticsearch |
| Agents vers Fleet | 8220 | HTTPS | clés d'API générées par Fleet |

## Mesures par phase

| Mesure | Ce qu'elle empêche | Phase |
|---|---|---|
| `xpack.security.enabled` + mots de passe des comptes intégrés | accès libre aux données | [01](../phases/phase-01-authentication.md) |
| HTTPS sur 9200 | capture des identifiants Basic Auth sur le réseau | [02](../phases/phase-02-http-tls.md) |
| mTLS sur 9300 | un nœud non autorisé qui rejoint le cluster | [03](../phases/phase-03-transport-tls.md) |
| HTTPS Kibana, compte `kibana_system` | session en clair, Kibana avec des droits superutilisateur | [04](../phases/phase-04-kibana-https.md) |
| Beats en HTTPS avec vérification de la CA et compte d'écriture limité | un collecteur compromis qui donne accès à tout le cluster | [05](../phases/phase-05-beats-authentication.md) |
| Fleet : service token + clés d'API | mots de passe stockés en clair sur chaque machine | [06](../phases/phase-06-fleet.md) |
| Second nœud + réplicas | perte de données si un nœud tombe | [07](../phases/phase-07-cluster.md) |
| Passage en 8.11.4 | rester sur une branche 7.x en fin de vie | [08](../phases/phase-08-upgrade.md) |

## Secrets

- mots de passe dans `.env`, exclu du dépôt (modèle : [.env.example](../.env.example))
- `certs/` et les fichiers `*.key` exclus par le [.gitignore](../.gitignore)
- IP de l'hôte remplacée par `<ELK_HOST>` dans la doc et masquée sur les captures
- secrets des jetons d'enrôlement floutés sur les captures
- le service token Fleet est généré au moment de l'installation et n'est stocké nulle part dans le dépôt

## Vérification

| Contrôle | Script |
|---|---|
| rejet anonyme / mauvais mot de passe, droits de `kibana_system` | [tests/authentication](../tests/authentication/test-authentication.sh) |
| chaîne de confiance, rejet hors CA interne, TLS 1.1 refusé | [tests/tls](../tests/tls/test-tls.sh) |
| ingestion de bout en bout | [tests/ingestion](../tests/ingestion/test-ingestion.sh) |

## Ce qui reste à faire

- alerte avant expiration des certificats
- règles de détection Elastic Security
- secrets dans un coffre plutôt qu'un `.env`
- troisième nœud master-eligible (voir [architecture](architecture.md#limite-connue))
