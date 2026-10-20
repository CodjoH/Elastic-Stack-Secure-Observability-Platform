# Playbooks de réponse à incident

Un playbook par règle de détection, au format *Investigation → Confinement → Remédiation → Clôture*. SOC-IR les recopie dans la description de chaque Case qu'il ouvre (fichier `<rule_id>.md`, sinon [default.md](default.md)) : l'analyste a la procédure sous les yeux, au même endroit que les alertes.

| Règle | Playbook |
|---|---|
| SSH - Brute force | [lab-ssh-bruteforce.md](lab-ssh-bruteforce.md) |
| SSH - Échec d'authentification | [lab-ssh-failed-login.md](lab-ssh-failed-login.md) |
| SSH - Connexion root réussie | [lab-ssh-root-login.md](lab-ssh-root-login.md) |
| Création d'un compte | [lab-user-created.md](lab-user-created.md) |
| Modification de groupe | [lab-group-change.md](lab-group-change.md) |
| Suppression d'un compte | [lab-user-deleted.md](lab-user-deleted.md) |
| IP bannie par fail2ban | [lab-fail2ban-ban.md](lab-fail2ban-ban.md) |
| Toute autre règle | [default.md](default.md) |

La règle *sudo* (sévérité low) n'ouvre pas de Case : elle sert au contexte d'investigation (Timeline, dashboard).

Après modification d'un playbook, le recopier sur l'hôte central : `sudo install -m 640 docs/playbooks/*.md /etc/soc-ir/playbooks/`.
