# 📸 Proof — Captures du projet

### SOC : détection & réponse

![Dashboard SOC](soc/soc-dashboard.png)

| | |
|:---:|:---:|
| ![Alertes](soc/security-alerts.png) | ![Règles](soc/detection-rules.png) |
| Alertes levées par une attaque SSH simulée | Les 8 règles de détection actives |
| ![Cases](soc/cases-list.png) | ![Case et playbook](soc/case-playbook.png) |
| Cases ouverts automatiquement par SOC-IR | Case avec son playbook et ses alertes |

### Kibana & Fleet

| | |
|:---:|:---:|
| ![Accueil Kibana](kibana/kibana-home-7.17.10.jpg) | ![Connexion Kibana](kibana/kibana-login-auth.png) |
| Accueil Kibana | Connexion avec authentification |
| ![Agents Fleet](kibana/fleet-agents-7.17.10.jpg) | ![Jetons d'enrôlement](kibana/fleet-enrollment-tokens.jpg) |
| Agents enrôlés dans Fleet | Jetons d'enrôlement (secrets floutés) |
| ![Réplicas](kibana/index-management-replicas.jpg) | ![Upgrade Assistant](kibana/upgrade-assistant.jpg) |
| Index en `green` avec réplicas sur 2 nœuds | Upgrade Assistant avant le passage en v8 |

### Validation

| | |
|:---:|:---:|
| ![curl auth](validation/curl-auth-http.jpg) | ![Auditbeat Filebeat](validation/beats-test-auditbeat-filebeat.jpg) |
| Requête refusée sans identifiants | Auditbeat / Filebeat en TLS 1.3 |
| ![Metricbeat Packetbeat](validation/beats-test-metricbeat-packetbeat.jpg) | ![Heartbeat](validation/beats-test-heartbeat.jpg) |
| Metricbeat / Packetbeat | Heartbeat |

Détail par dossier : [soc/](soc/) · [kibana/](kibana/) · [validation/](validation/) · ⬅️ [Retour au README](../README.md)
