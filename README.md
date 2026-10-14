<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:005571,100:00BFB3&height=170&section=header&text=Elastic%20Stack&fontSize=46&fontColor=ffffff&fontAlignY=36&desc=Secure%20Observability%20Platform&descAlignY=58&descSize=18" width="100%"/>

# 🛡️ Elastic Stack — Secure Observability Platform

**Durcissement et migration d'une Elastic Stack v7 mono-nœud vers un cluster distribué v8.11.4 chiffré de bout en bout**

![Elastic](https://img.shields.io/badge/Elastic_Stack-8.11.4-005571?style=for-the-badge&logo=elastic&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Docker Compose](https://img.shields.io/badge/Docker_Compose-1D63ED?style=for-the-badge&logo=docker&logoColor=white)
![Kibana](https://img.shields.io/badge/Kibana-E8478B?style=for-the-badge&logo=kibana&logoColor=white)
![Kafka](https://img.shields.io/badge/Kafka-231F20?style=for-the-badge&logo=apachekafka&logoColor=white)
![Logstash](https://img.shields.io/badge/Logstash-00BFB3?style=for-the-badge&logo=logstash&logoColor=white)
![TLS](https://img.shields.io/badge/TLS%20%2F%20mTLS-Partout-2E7D32?style=for-the-badge&logo=letsencrypt&logoColor=white)
![Linux](https://img.shields.io/badge/Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black)
![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)

[Architecture](docs/architecture.md) · [Hardening](docs/security-hardening.md) · [Certificats](docs/certificates.md) · [Sauvegarde](docs/backup-restore.md) · [Phases](#️-feuille-de-route--9-phases) · [Captures](#-captures)

</div>

---

## 📌 Présentation

Ce projet documente la sécurisation complète et la migration d'une infrastructure Elastic Stack, d'une topologie v7 standard vers une architecture distribuée v8.11.4.

Trois règles ont guidé le travail : moindre privilège, chiffrement de tous les flux et centralisation de la télémétrie. Chaque étape est documentée et testée, avec les incidents rencontrés et leur résolution.

<p align="center">
  <img src="https://img.shields.io/badge/🔒-Zéro_flux_en_clair-005571?style=flat-square"/>
  <img src="https://img.shields.io/badge/⚙️-Cluster_2_nœuds-00BFB3?style=flat-square"/>
  <img src="https://img.shields.io/badge/📡-Fleet_%2B_Elastic_Agent-E8478B?style=flat-square"/>
  <img src="https://img.shields.io/badge/🔄-v7_→_v8-2E7D32?style=flat-square"/>
</p>

---

## 🏗️ Architecture

```mermaid
flowchart LR
    U[👤 Navigateur] -- "HTTPS :5601" --> K[Kibana v8]
    K -- "HTTPS :9200" --> N1
    subgraph CLUSTER["Cluster Elasticsearch v8.11.4"]
        N1[(es-node1<br/>Master / Data)]
        N2[(es-node2<br/>Data / Réplicas)]
        N1 <-- "mTLS :9300" --> N2
    end
    A[Client-Lin01<br/>Elastic Agent] -- "HTTPS :8220" --> FS[Fleet Server<br/>hôte central]
    A -- "HTTPS :9200" --> N1
    FS -- "HTTPS :9200" --> N1
```

➡️ Détails : [docs/architecture.md](docs/architecture.md)

## 🔐 Matrice de sécurité

| Flux | Port | Protocole | Authentification & confiance |
|---|---|---|---|
| API Elasticsearch | 9200 | HTTPS | Certificat signé par la CA interne + authentification obligatoire |
| Transport inter-nœuds | 9300 | mTLS | `verification_mode: certificate`, CA partagée |
| Kibana | 5601 | HTTPS | Compte restreint `kibana_system` + TLS navigateur |
| Enrôlement Fleet Server | 8220 | HTTPS | Service token Elasticsearch v8 |
| Agents ➔ Fleet | 8220 | HTTPS | Clés d'API rotatives générées par Fleet |

➡️ Détails : [docs/security-hardening.md](docs/security-hardening.md)

---

## 🗺️ Feuille de route : 9 phases

| Phase | Étape | Point clé |
|:---:|---|---|
| 00 | [Stabilisation](phases/phase-00-stabilization.md) | Résolution d'une `UnavailableShardsException` sur `.security` |
| 01 | [Authentification](phases/phase-01-authentication.md) | Fin des accès anonymes, moindre privilège, audit |
| 02 | [TLS HTTP](phases/phase-02-http-tls.md) | API REST en HTTPS via une CA interne |
| 03 | [TLS Transport](phases/phase-03-transport-tls.md) | mTLS entre les nœuds |
| 04 | [Kibana HTTPS](phases/phase-04-kibana-https.md) | HTTPS navigateur + compte `kibana_system` |
| 05 | [Authentification des Beats](phases/phase-05-beats-authentication.md) | Comptes d'écriture dédiés, keystore |
| 06 | [Fleet](phases/phase-06-fleet.md) | Migration vers Elastic Agent + Fleet Server |
| 07 | [Cluster](phases/phase-07-cluster.md) | Ajout d'un 2ᵉ nœud, test de failover |
| 08 | [Upgrade v8](phases/phase-08-upgrade.md) | Rolling upgrade, mise à niveau des agents à distance |

## 📂 Structure du dépôt

```
├── docker-compose.yml        # Cluster 2 nœuds + Kibana, TLS activé
├── .env.example              # Modèle des variables (le .env réel n'est pas versionné)
├── docs/                     # Architecture, hardening, PKI, sauvegarde
├── config/
│   ├── elasticsearch/        # instances.yml (certificats)
│   ├── kibana/               # Paramètres Kibana (HTTPS + Fleet)
│   └── beats/                # filebeat.yml, rôle d'écriture des Beats (phase 05)
├── scripts/                  # health-check.sh, verify-tls.sh
├── tests/                    # authentication/, tls/, ingestion/
├── screenshots/              # architecture/, kibana/, validation/
└── phases/                   # Journal détaillé des 9 phases
```

## 🚀 Démarrage rapide

```bash
# 1. Variables d'environnement
cp .env.example .env && nano .env

# 2. PKI interne : CA + certificats (voir docs/certificates.md)

# 3. Lancement du cluster et de Kibana
set -a; . ./.env; set +a
docker compose up -d

# 4. Vérifications
./scripts/health-check.sh
./scripts/verify-tls.sh
```

Le déploiement du Fleet Server et l'enrôlement des agents sont décrits en [phase 06](phases/phase-06-fleet.md).

## 🧪 Validation

| Domaine | Ce qui est vérifié | Script |
|---|---|---|
| Authentification | Rejet des requêtes anonymes ou mal signées, moindre privilège | [`test-authentication.sh`](tests/authentication/test-authentication.sh) |
| TLS | Chaîne de confiance, rejet d'une CA inconnue (anti-MitM), protocoles obsolètes refusés | [`test-tls.sh`](tests/tls/test-tls.sh) |
| Ingestion | Écriture/lecture de bout en bout, flux des agents | [`test-ingestion.sh`](tests/ingestion/test-ingestion.sh) |
| Résilience | Perte du nœud secondaire sans interruption | [Phase 07](phases/phase-07-cluster.md#test-de-résilience-failover) |

---

## 📸 Captures

### Kibana & Fleet

| | |
|:---:|:---:|
| ![Accueil Kibana](screenshots/kibana/kibana-home-7.17.10.jpg) | ![Connexion Kibana](screenshots/kibana/kibana-login-auth.png) |
| Accueil Kibana | Connexion avec authentification |
| ![Agents Fleet](screenshots/kibana/fleet-agents-7.17.10.jpg) | ![Jetons d'enrôlement](screenshots/kibana/fleet-enrollment-tokens.jpg) |
| Agents enrôlés dans Fleet | Jetons d'enrôlement (secrets floutés) |
| ![Réplicas](screenshots/kibana/index-management-replicas.jpg) | ![Upgrade Assistant](screenshots/kibana/upgrade-assistant.jpg) |
| Index en `green` avec réplicas sur 2 nœuds | Upgrade Assistant avant le passage en v8 |

### Validation

| | |
|:---:|:---:|
| ![curl auth](screenshots/validation/curl-auth-http.jpg) | ![Auditbeat Filebeat](screenshots/validation/beats-test-auditbeat-filebeat.jpg) |
| Requête refusée sans identifiants | Auditbeat / Filebeat en TLS 1.3 |
| ![Metricbeat Packetbeat](screenshots/validation/beats-test-metricbeat-packetbeat.jpg) | ![Heartbeat](screenshots/validation/beats-test-heartbeat.jpg) |
| Metricbeat / Packetbeat | Heartbeat |

Toutes les captures : [`screenshots/`](screenshots/)

---

## 🛠️ Problèmes rencontrés

| Incident | Cause | Résolution |
|---|---|---|
| 🔴 `UnavailableShardsException` sur `.security` | Réplicas impossibles à allouer sur un nœud unique | Réplicas système à 0 puis réintégration à chaud du 2ᵉ nœud ([phase 00](phases/phase-00-stabilization.md)) |
| 🔴 Agent `DEGRADED` après la v8 | Restriction v8 sur les chemins de CA par défaut | Lien symbolique vers `/etc/elastic-agent/certs/elk-ca.crt` ([phase 08](phases/phase-08-upgrade.md)) |
| 🔴 Conflits inter-versions | Agents v7 face à un Fleet v8 | Upgrade des agents à distance depuis Kibana ([phase 08](phases/phase-08-upgrade.md)) |

## 🎯 Résultat

| Objectif | Résultat |
|---|---|
| 🔒 **Zéro flux en clair** | HTTPS/TLS sur toutes les API, **mTLS** entre nœuds, CA racine interne |
| ⚙️ **Haute disponibilité** | Cluster 2 nœuds avec réplication, panne d'un nœud de données testée sans perte de données |
| 📡 **Modernisation de la collecte** | Beats remplacés par **Elastic Agent + Fleet Server**, clés d'API rotatives |
| 🔄 **Cycle de vie maîtrisé** | Montée de version **v7 ➔ v8** sans perte de données ni rupture de collecte |

**Outils :** `Elasticsearch` `Kibana` `Logstash` `Kafka` `Fleet` `Elastic Agent` `Beats` `Docker` `Docker Compose` `PKI / X.509` `TLS / mTLS` `OpenSSL` `Bash` `Linux`

---

<div align="center">

📄 Licence [MIT](LICENSE) · **[CodjoH](https://github.com/CodjoH)**

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:00BFB3,100:005571&height=100&section=footer" width="100%"/>

</div>
