# 🔒 Security Hardening

Ce document récapitule les mesures de durcissement appliquées et la menace que chacune neutralise.

## Matrice de sécurité des flux

| Flux réseau | Port | Protocole | Authentification & confiance |
|---|---|---|---|
| API externe Elasticsearch | 9200 | HTTPS | Certificat signé par la CA interne + authentification obligatoire |
| Transport inter-nœuds | 9300 | mTLS | `verification_mode: certificate`, certificat client exigé, CA partagée |
| Interface Kibana | 5601 | HTTPS | TLS navigateur ; Kibana se connecte avec le compte restreint `kibana_system` |
| Enrôlement Fleet Server | 8220 | HTTPS | Service token Elasticsearch v8 (`elastic/fleet-server`) |
| Agents ➔ Fleet | 8220 | HTTPS | Clés d'API générées et renouvelées automatiquement par Fleet |

## Mesures appliquées

| # | Mesure | Menace couverte | Phase |
|---|---|---|---|
| 1 | Activation de `xpack.security` et mots de passe robustes | Accès non authentifié aux données | [01](../phases/phase-01-authentication.md) |
| 2 | Aucun rôle anonyme | Lecture/écriture anonyme | [01](../phases/phase-01-authentication.md) |
| 3 | TLS sur l'API REST | Interception des identifiants et des données (sniffing) | [02](../phases/phase-02-http-tls.md) |
| 4 | mTLS sur le transport | Nœud malveillant rejoignant le cluster | [03](../phases/phase-03-transport-tls.md) |
| 5 | HTTPS Kibana + compte `kibana_system` | Vol de session, sur-privilège de Kibana | [04](../phases/phase-04-kibana-https.md) |
| 6 | Comptes Beats dédiés à privilèges minimaux | Compromission d'un collecteur = compromission du cluster | [05](../phases/phase-05-beats-authentication.md) |
| 7 | Service token + clés d'API Fleet rotatives | Secrets statiques stockés sur chaque machine | [06](../phases/phase-06-fleet.md) |
| 8 | Cluster multi-nœuds + réplicas | Perte de données en cas de panne | [07](../phases/phase-07-cluster.md) |
| 9 | Montée de version v8 | Vulnérabilités connues des versions anciennes | [08](../phases/phase-08-upgrade.md) |
| 10 | Journal d'audit (`xpack.security.audit`) | Absence de traçabilité des accès | [01](../phases/phase-01-authentication.md) |

## Gestion des secrets

- Les mots de passe sont injectés via un fichier `.env` **exclu du dépôt** ([.env.example](../.env.example) fourni comme modèle).
- Les clés privées et certificats (`certs/`, `*.key`) sont exclus par le [.gitignore](../.gitignore).
- Le service token Fleet est généré à la demande et n'est jamais versionné.

## Validation

Chaque mesure est vérifiée par un test automatisé :

| Test | Script |
|---|---|
| Rejet des requêtes anonymes ou mal authentifiées, moindre privilège | [`tests/authentication/test-authentication.sh`](../tests/authentication/test-authentication.sh) |
| Chaîne de confiance, rejet d'une CA inconnue (MitM), protocoles obsolètes | [`tests/tls/test-tls.sh`](../tests/tls/test-tls.sh) |
| Ingestion de bout en bout | [`tests/ingestion/test-ingestion.sh`](../tests/ingestion/test-ingestion.sh) |

## Pistes d'amélioration

- Rotation planifiée des certificats et alerte avant expiration
- Intégration d'Elastic Security (règles de détection, Elastic Defend)
- Stockage des secrets dans un coffre (HashiCorp Vault) plutôt qu'un fichier `.env`
- Ajout d'un troisième nœud maître éligible pour un quorum tolérant à la panne du maître
