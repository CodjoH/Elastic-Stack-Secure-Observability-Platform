# Elastic-Stack-Secure-Observability-Platform


## 📌 Présentation du Projet

Ce projet documente la conception, la sécurisation critique (*Security Hardening*) et la migration d'une infrastructure **Elastic Stack (ELK)** d'une topologie v7 standard vers une **architecture distribuée v8.11.4 de niveau production**.

Conçu sous la forme d'un **Security Hardening Lab**, ce projet applique les principes du moindre privilège, du chiffrement systématique des flux réseaux et de la centralisation moderne de la télémétrie.

### 🎯 Objectifs Stratégiques
* **Zéro Flux en Clair :** Chiffrement intégral (HTTPS/TLS) des API publiques, du transport inter-nœuds et des accès utilisateurs.
* **Haute Disponibilité :** Transition d'un nœud isolé vers un cluster distribué multi-nœuds résilient face aux pannes.
* **Modernisation SecOps :** Migration d'une flotte d'agents Beats historiques vers une architecture centralisée pilotée par **Elastic Agent & Fleet Server**.
* **Cycle de Vie Maîtrisé :** Exécution d'un saut de version majeure (v7 ➔ v8) sans perte de données ni rupture de la collecte.

---

## 🔗 Architecture Cible

L'infrastructure finale colocalise la puissance d'un cluster distribué et la flexibilité d'une flotte d'agents centralisée :

```text
       [ Navigateur Client ] ──( HTTPS:5601 )──> [ Kibana v8 ]
                                                       │
                                                 ( HTTPS:9200 )
                                                       │
                                                       ▼
  [ Machine Distante : Client-Lin01 ] ───> [ Cluster Elasticsearch v8 ] <─── [ Fleet Server Natif ]
     └─ Elastic Agent (v8.11.4)              ├── es-node1 (Master/Data)         └─ Hôte local (v8.11.4)
                                             └── es-node2 (Data / Réplicas)
                                                    ▲                ▲
                                                    └─( TLS mTLS:9300)┘
```

---

## 🔒 Matrice de Sécurité & Chiffrement TLS

| **Flux Réseau** | **Protocole / Mode** | **Mécanisme d'Authentification & Confiance** |
|:---|:---|:---|
| **API Externe Elasticsearch** | **HTTPS (9200)** | Certificats Web signés par une CA racine interne dédiée. |
| **Transport Inter-Nœuds** | **mTLS (9300)** | `verification_mode: certificate` via CA partagée (Contrôle du quorum). |
| **Interface Kibana** | **HTTPS (5601)** | Compte système restreint `kibana_system` + TLS Navigateur. |
| **Enrôlement Fleet Server** | **HTTPS (8220)** | Service Token Elasticsearch dynamique de niveau v8 (`token-final`). |
| **Collecte Client ➔ Fleet** | **HTTPS (8220)** | Clés d'API rotatives générées automatiquement par le moteur Fleet. |

---

## 🚀 Guide de Déploiement Rapide

### 1. Initialisation de la Chaîne de Confiance (CA)
Avant d'initier la stack, les paires de clés et l'autorité de certification doivent être injectées dans le répertoire partagé :
```bash
certs/runtime/
├── ca/ca.crt
├── es-http/elasticsearch.crt
└── kibana/kibana.crt
```

### 2. Initialisation des Variables d'Environnement
Déclarez vos secrets d'infrastructure dans un fichier `.env` local :
```env
ELASTIC_PASSWORD=votre_mot_de_passe_robuste
KIBANA_SYSTEM_PASSWORD=votre_mot_de_passe_systeme
```

### 3. Orchestration du Cluster Multi-Nœuds
Démarrer la topologie Elasticsearch distribuée et l'interface Kibana :
```bash
set -a; . ./.env; set +a
docker-compose up -d
```

### 4. Déploiement Bare-Metal du Fleet Server (Hôte Central)
Générer le jeton de service v8 depuis le cœur du cluster :
```bash
docker exec -it elasticsearch /usr/share/elasticsearch/bin/elasticsearch-service-tokens create elastic/fleet-server token-final
```
Exécuter l'installation et l'enrôlement automatique du superviseur de flotte :
```bash
sudo ./elastic-agent install --url=https://<ELK_HOST_IP>:8220 \
  --fleet-server-es=https://<ELK_HOST_IP>:9200 \
  --fleet-server-service-token=VOTRE_TOKEN_GENERE \
  --fleet-server-policy=499b5aa7-d214-5b5d-838b-3cd76469844e \
  --certificate-authorities=/home/cyber/certs/runtime/ca/ca.crt \
  --fleet-server-es-ca=/home/cyber/certs/runtime/ca/ca.crt \
  --fleet-server-cert=/home/cyber/certs/runtime/kibana/kibana.crt \
  --fleet-server-cert-key=/home/cyber/certs/runtime/kibana/kibana.key
```

---

## 🧪 Matrice de Validation & Tests de Sécurité

Le maintien opérationnel et la conformité du durcissement ont été validés par des tests unitaires stricts à chaque jalon :
* **Vérification d'Authentification :** Audit et validation du rejet systématique de toutes les requêtes anonymes ou non signées.
* **Validation de Confiance TLS :** Tests de poignées de main (handshakes) via OpenSSL pour éliminer les risques d'attaques de l'homme du milieu (MitM).
* **Continuité de Service (Failover) :** Simulation de perte du nœud de données secondaire pour valider la réplication immédiate des shards et la résilience de la plateforme.

---

## 🛠️ Journal de Dépannage & Retours d'Expérience (*Post-Mortem*)

* 🔴 **Incident :** `UnavailableShardsException` sur l'index `.security` lors de la réorganisation réseau.  
  🟢 **Résolution :** Stabilisation transitoire via l'API de routage en forçant l'allocation des réplicas système à `0`, offrant une base saine avant l'injection à chaud du second nœud.
* 🔴 **Incident :** Statut `DEGRADED` de l'agent de collecte local juste après le saut de version v8.  
  🟢 **Résolution :** Identification d'une restriction de sécurité native de la v8 sur les chemins de CA par défaut. Résolu de manière permanente via l'implémentation d'un lien symbolique système vers `/etc/elastic-agent/certs/elk-ca.crt`.
* 🔴 **Incident :** Conflits de communication inter-versions lors de la mise à niveau globale.  
  🟢 **Résolution :** Exploitation réussie du mécanisme d'auto-upgrade descendant de Fleet v8, permettant de télé-administrer la mise à niveau de `Client-Lin01` directement depuis Kibana, sans aucune perte de paquets.

---
💡 *Ce projet a été réalisé dans un cadre de durcissement de niveau Enterprise. Les configurations et processus appliqués reflètent les meilleures pratiques de l'industrie en matière de sécurité des architectures SIEM.*