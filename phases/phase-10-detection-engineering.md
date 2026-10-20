# Phase 10 : Detection Engineering

Objectif : que des comportements suspects sur Client-Lin01 fassent remonter des alertes dans **Security > Alerts**, avec des règles versionnées dans le dépôt (*Detection-as-Code*).

## Prérequis 1 : clés de chiffrement Kibana

La page Alerts affichait *API integration key required* : sans clé persistante, Kibana en génère une nouvelle à chaque démarrage et les règles deviennent impossibles à modifier après un redémarrage. Trois clés ajoutées au [docker-compose.yml](../docker-compose.yml), valeurs dans le `.env` :

```bash
openssl rand -hex 32   # x3 : KIBANA_ESO_KEY, KIBANA_SECURITY_KEY, KIBANA_REPORTING_KEY
docker compose up -d --no-deps kibana
```

## Prérequis 2 : des logs d'authentification

L'intégration System lit `/var/log/auth.log`... qui n'existe pas sur Debian 12 (journald seul). Aucun événement SSH ni sudo ne remontait. Sur le client :

```bash
sudo apt-get install -y rsyslog
# format syslog classique, attendu par le pipeline d'ingestion
sudo sed -i 's|^module(load="builtin:omfile".*|module(load="builtin:omfile" Template="RSYSLOG_TraditionalFileFormat")|' /etc/rsyslog.conf
sudo systemctl restart rsyslog
```

Les événements arrivent ensuite dans `logs-system.auth-default`, avec `event.action: ssh_login`, `event.outcome`, `source.ip`, `user.name`.

## Les règles

Huit règles dans [detection/rules/](../detection/rules), une par fichier JSON, exécutées chaque minute. Détail et matrice MITRE ATT&CK : [detection/README.md](../detection/README.md).

```bash
./scripts/deploy-rules.py --dry-run   # validation locale du format
./scripts/deploy-rules.py             # création ou mise à jour par rule_id
```

## Incident : des règles qui ne déclenchent jamais

Après un premier test (création de compte, ajout à un groupe, sudo), seules les règles SSH produisaient des alertes. En inspectant les documents indexés, le pipeline System 1.53.1 ne renseigne ni `event.category: iam` ni `process.name` pour ces lignes :

```json
{"log": {"syslog": {"appname": "useradd"}},
 "system": {"auth": {"useradd": {"home": "/home/labtest", "shell": "/bin/sh"}}},
 "user": {"name": "labtest"}}
```

Pour `useradd`, le message est même supprimé après parsing. Les requêtes ont été réécrites sur les champs réellement présents :

| Règle | Requête initiale (doc ECS) | Requête retenue |
|---|---|---|
| Création de compte | `event.category:"iam" and event.type:"creation"` | `log.syslog.appname:"useradd" and system.auth.useradd.home:*` |
| Modification de groupe | `event.category:"iam" and event.type:"change"` | `log.syslog.appname:("usermod" or "gpasswd") and message:"to group"` |
| sudo | `process.name:"sudo" and system.auth.sudo.command:*` | `log.syslog.appname:"sudo" and message:"COMMAND"` |

Leçon : toujours valider une règle sur un vrai document indexé, pas sur la documentation du schéma.

## Vérification

Événements de test générés sur le client (échecs SSH avec un compte inexistant, `sudo`, `useradd` / `usermod` / `userdel` d'un compte jetable) : chaque règle a produit au moins une alerte.

![Règles de détection actives](../screenshots/soc/detection-rules.png)

![Alertes levées par une attaque SSH simulée](../screenshots/soc/security-alerts.png)

Retour au [README](../README.md)
