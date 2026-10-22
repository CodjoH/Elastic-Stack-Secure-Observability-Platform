<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:005571,100:00BFB3&height=170&section=header&text=Elastic%20Stack&fontSize=46&fontColor=ffffff&fontAlignY=36&desc=Secure%20Observability%20Platform&descAlignY=58&descSize=18" width="100%"/>

# 🛡️ Elastic Stack — Secure Observability Platform

**Conception et déploiement d'une plateforme d'observabilité sécurisée basée sur Elastic Stack 8.11, intégrant la centralisation des logs, la détection des menaces à l'aide de règles alignées sur MITRE ATT&CK et la réponse automatisée aux incidents.**

`Elastic Stack 8.11.4` · `Kibana` · `Fleet / Elastic Agent` · `Docker Compose` · `Kafka` · `TLS / mTLS` · `MITRE ATT&CK` · `Python` · `Licence MIT`

[Architecture](docs/architecture.md) · [Hardening](docs/security-hardening.md) · [Certificats](docs/certificates.md) · [Sauvegarde](docs/backup-restore.md) · [Détection](detection/README.md) · [Playbooks](docs/playbooks/README.md) · [Phases](phases/) · [Captures](#-captures)

</div>

---

## 📌 Présentation

Ce projet présente la sécurisation complète et la migration d'une infrastructure Elastic Stack, d'un nœud unique en version 7.17 vers un cluster distribué en version 8.11.4.

Trois principes ont guidé le travail : moindre privilège, chiffrement de tous les flux et centralisation de la télémétrie. Chaque étape est documentée et testée, avec les incidents rencontrés et leur résolution.

Une fois sécurisée, la plateforme a été exploitée comme un SOC : règles de détection versionnées et alignées sur MITRE ATT&CK, tableau de bord d'analyse, confinement automatique des attaques SSH et ouverture de Cases accompagnés de leur playbook.

## 🎯 Objectifs

- 🔐 Sécuriser l'accès à Kibana et Elasticsearch : authentification obligatoire et moindre privilège.
- 🔒 Chiffrer les communications HTTP et transport avec TLS et mTLS.
- 🪪 Mettre en place une PKI interne : autorité de certification et certificats vérifiés.
- 📊 Maintenir la collecte et l'ingestion des événements à chaque évolution.
- ⚙️ Déployer Fleet Server et migrer les Beats vers Elastic Agent.
- 🏗️ Passer à un cluster Elasticsearch à deux nœuds et en tester la résilience.
- 🔄 Préparer, réaliser et documenter la montée de version de la 7.17 à la 8.11.
- 🚨 Détecter les menaces avec des règles alignées sur MITRE ATT&CK.
- 🛡️ Automatiser la réponse aux incidents : confinement, Cases et playbooks.

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

## 🚨 Détection & réponse à incident

```mermaid
flowchart LR
    ATK[Brute force SSH] --> C[Client-Lin01]
    C -- "auth.log / syslog" --> AG[Elastic Agent]
    C -- "fail2ban : IP bannie" --> FW[nftables :22]
    AG --> R[8 règles de détection<br/>MITRE ATT&CK]
    R --> AL[Alertes]
    AL --> IR[SOC-IR<br/>timer 1 min]
    IR --> CS[Case Kibana<br/>+ playbook]
    AL --> D[Dashboard SOC]
```

---

## 📂 Structure du dépôt

```
├── docker-compose.yml        # Cluster 2 nœuds + Kibana, TLS activé
├── .env.example              # Modèle des variables (le .env réel n'est pas versionné)
├── docs/                     # Architecture, hardening, PKI, sauvegarde
├── config/
│   ├── elasticsearch/        # instances.yml (certificats)
│   ├── kibana/               # Paramètres Kibana (HTTPS + Fleet)
│   └── beats/                # filebeat.yml, rôle d'écriture des Beats (phase 05)
├── detection/rules/          # Règles de détection (JSON, une par fichier)
├── dashboards/               # Export NDJSON du dashboard SOC
├── response/
│   ├── fail2ban/             # Confinement automatique des brute force SSH
│   └── soc-ir/               # Service de création des Cases + unités systemd
├── docs/playbooks/           # Un playbook de réponse par règle
├── scripts/                  # health-check, verify-tls, deploy-rules, build-dashboard
├── tests/                    # authentication/, tls/, ingestion/, detection/, response/
├── screenshots/              # architecture/, kibana/, validation/, soc/
└── phases/                   # Journal détaillé des 13 phases
```

## 🚀 Guide de déploiement

**Prérequis :** Docker et Docker Compose, OpenSSL, un hôte Linux avec au moins 8 Go de RAM (deux nœuds Elasticsearch, Kibana et Fleet Server).

### 1. Générer la PKI interne

Une autorité de certification dédiée signe les certificats de l'API, du transport et de Kibana ([docs/certificates.md](docs/certificates.md)) :

```text
certs/runtime/              # monté en lecture seule dans les conteneurs
├── ca/ca.crt
├── es-http/elasticsearch.crt
├── es-node1/  es-node2/    # certificats de transport (mTLS)
└── kibana/kibana.crt
```

### 2. Configurer l'environnement

Le fichier `.env` contient les secrets d'infrastructure et n'est jamais versionné ([.env.example](.env.example)) :

```bash
cp .env.example .env
```

```env
ELASTIC_PASSWORD=<mot_de_passe_robuste>
KIBANA_SYSTEM_PASSWORD=<mot_de_passe_kibana_system>
KIBANA_ESO_KEY=<openssl rand -hex 32>
CERTS_DIR=/chemin/vers/certs/runtime
ELK_HOST=<adresse_de_l_hote_central>
```

### 3. Démarrer la stack

```bash
set -a; . ./.env; set +a
docker compose up -d                      # ou docker-compose up -d (Compose v1)
./scripts/health-check.sh && ./scripts/verify-tls.sh
```

### 4. Initialiser Fleet Server (agent natif sur l'hôte central)

Générer un jeton de service v8 depuis le conteneur Elasticsearch :

```bash
docker exec -it elasticsearch bin/elasticsearch-service-tokens create elastic/fleet-server fleet-token
```

Installer l'Elastic Agent en mode Fleet Server :

```bash
sudo ./elastic-agent install --url=https://<ELK_HOST>:8220 \
  --fleet-server-es=https://<ELK_HOST>:9200 \
  --fleet-server-service-token=<SERVICE_TOKEN> \
  --fleet-server-policy=<FLEET_SERVER_POLICY_ID> \
  --certificate-authorities=$CERTS_DIR/ca/ca.crt \
  --fleet-server-es-ca=$CERTS_DIR/ca/ca.crt \
  --fleet-server-cert=$CERTS_DIR/kibana/kibana.crt \
  --fleet-server-cert-key=$CERTS_DIR/kibana/kibana.key
```

L'enrôlement des agents clients est détaillé en [phase 06](phases/phase-06-fleet.md).

### 5. Activer la couche SOC

```bash
./scripts/deploy-rules.py                 # règles de détection (clé API Kibana dans .env)
./scripts/build-dashboard.py              # dashboard SOC
sudo -E ./response/soc-ir/install.sh      # ouverture automatique des Cases
```

Installer ensuite fail2ban sur chaque client Linux ([phase 12](phases/phase-12-incident-response.md)), puis valider la chaîne complète avec `./tests/detection/simulate-attacks.sh`.

## 🧪 Validation

| Domaine | Ce qui est vérifié | Script |
|---|---|---|
| Authentification | Rejet des requêtes anonymes ou mal signées, moindre privilège | [`test-authentication.sh`](tests/authentication/test-authentication.sh) |
| TLS | Chaîne de confiance, rejet d'une CA inconnue (anti-MitM), protocoles obsolètes refusés | [`test-tls.sh`](tests/tls/test-tls.sh) |
| Ingestion | Écriture/lecture de bout en bout, flux des agents | [`test-ingestion.sh`](tests/ingestion/test-ingestion.sh) |
| Résilience | Perte du nœud secondaire sans interruption | [Phase 07](phases/phase-07-cluster.md#test-de-résilience-failover) |
| Détection → réponse | Brute force simulé : IP bannie, alertes levées, Cases ouverts | [`simulate-attacks.sh`](tests/detection/simulate-attacks.sh) |
| Logique SOC-IR | Regroupement, playbooks, acquittement avant rattachement (sans réseau) | [`test_soc_ir.py`](tests/response/test_soc_ir.py) |

---

## 📸 Captures

### SOC : détection & réponse

![Dashboard SOC](screenshots/soc/soc-dashboard.png)

| | |
|:---:|:---:|
| ![Alertes](screenshots/soc/security-alerts.png) | ![Règles](screenshots/soc/detection-rules.png) |
| Alertes levées par une attaque SSH simulée | Les 8 règles de détection actives |
| ![Cases](screenshots/soc/cases-list.png) | ![Case et playbook](screenshots/soc/case-playbook.png) |
| Cases ouverts automatiquement par SOC-IR | Case avec son playbook et ses alertes |

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
| 🔴 Agent 8.0 Unhealthy, upgrade impossible | Timeout de téléchargement de 120 s, puis paquet local effacé par l'agent 8.0 | Réinstallation propre en 8.11.4 + réaffectation de policy ([phase 09](phases/phase-09-fleet-troubleshooting.md)) |
| 🟠 Aucun log d'authentification | Debian 12 n'écrit plus `/var/log/auth.log` (journald seul) | rsyslog au format classique ([phase 10](phases/phase-10-detection-engineering.md)) |
| 🟠 Règles qui ne déclenchent jamais | Le pipeline System 1.53 ne remplit pas `event.category: iam` / `process.name` | Requêtes réécrites sur les champs réellement indexés ([phase 10](phases/phase-10-detection-engineering.md)) |
| 🟠 Pas de Case automatique en licence basic | Connecteur Cases indisponible | Service SOC-IR via l'API Cases ([phase 12](phases/phase-12-incident-response.md)) |

## 🏆 Résultats

<div align="center">

| 🔒 **0** | 🧱 **2** | 🎯 **8** | 🧭 **6** | ⚡ **< 2 min** | 📚 **13** |
|:---:|:---:|:---:|:---:|:---:|:---:|
| flux en clair | nœuds en cluster | règles de détection | techniques ATT&CK | de l'attaque au Case | phases documentées |

</div>

---

<div align="center">

<p align="center">
  🛡️ <strong>Hubert Codjo</strong><br>
  <sub>Cybersecurity Engineer • SOC Analyst • Blue Team</sub><br><br>
  📧 <a href="mailto:houet.hubert@gmail.com"><strong>Click to contact me</strong></a><br><br>
  ─ · ─<br><br>
</p>

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:00BFB3,100:005571&height=100&section=footer" width="100%"/>

</div>
