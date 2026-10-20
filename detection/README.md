# Règles de détection

Une règle Kibana Security par fichier JSON dans [rules/](rules), déployées par [scripts/deploy-rules.py](../scripts/deploy-rules.py) (création ou mise à jour par `rule_id`). Toutes portent le tag `SOC-Lab` et s'exécutent chaque minute.

| Règle | Type | Sévérité | Source | MITRE ATT&CK |
|---|---|---|---|---|
| [SSH - Échec d'authentification](rules/lab-ssh-failed-login.json) | query | medium | `logs-system.auth-*` | TA0006 · [T1110](https://attack.mitre.org/techniques/T1110/) Brute Force |
| [SSH - Brute force (≥5 échecs en 5 min)](rules/lab-ssh-bruteforce.json) | threshold (`source.ip` ≥ 5) | **high** | `logs-system.auth-*` | TA0006 · [T1110](https://attack.mitre.org/techniques/T1110/) Brute Force |
| [SSH - Connexion root réussie](rules/lab-ssh-root-login.json) | query | medium | `logs-system.auth-*` | TA0001 · [T1078](https://attack.mitre.org/techniques/T1078/) Valid Accounts |
| [Linux - Commande exécutée via sudo](rules/lab-sudo-command.json) | query | low | `logs-system.auth-*` | TA0004 · [T1548](https://attack.mitre.org/techniques/T1548/) Abuse Elevation Control |
| [Linux - Création d'un compte utilisateur](rules/lab-user-created.json) | query | **high** | `logs-system.auth-*` | TA0003 · [T1136](https://attack.mitre.org/techniques/T1136/) Create Account |
| [Linux - Modification de groupe](rules/lab-group-change.json) | query | medium | `logs-system.auth-*` | TA0003 · [T1098](https://attack.mitre.org/techniques/T1098/) Account Manipulation |
| [Linux - Suppression d'un compte utilisateur](rules/lab-user-deleted.json) | query | medium | `logs-system.auth-*` | TA0040 · [T1531](https://attack.mitre.org/techniques/T1531/) Account Access Removal |
| [Réponse auto - IP bannie par fail2ban](rules/lab-fail2ban-ban.json) | query | **high** | `logs-system.syslog-*` | TA0006 · [T1110](https://attack.mitre.org/techniques/T1110/) Brute Force |

Les alertes de sévérité medium et plus ouvrent automatiquement un Case avec le [playbook](../docs/playbooks) correspondant (voir la [phase 12](../phases/phase-12-incident-response.md)).

## Ajouter une règle

1. Créer `rules/<rule_id>.json` (même structure que les fichiers existants : `rule_id`, `type`, `query`, `index`, `severity`, `risk_score`, `threat`).
2. Valider la requête dans Discover **sur un vrai document indexé** : le pipeline System ne remplit pas toujours les champs ECS attendus (voir la [phase 10](../phases/phase-10-detection-engineering.md)).
3. Écrire `docs/playbooks/<rule_id>.md` si la sévérité est medium ou plus.
4. `./scripts/deploy-rules.py --dry-run` puis `./scripts/deploy-rules.py`.
