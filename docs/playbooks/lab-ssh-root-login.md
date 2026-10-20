# 👑 Playbook — Connexion SSH root
## 🔎 Investigation
- L'IP source est-elle un poste d'administration connu (voir `ignoreip` de fail2ban) ?
- Connexion attendue (maintenance planifiée) ? Méthode : clé ou mot de passe ?
- Activité après connexion : commandes, comptes créés, fichiers modifiés
## 🛑 Confinement
- Si non légitime : `pkill -KILL -t <tty>` ou `loginctl terminate-user root`, bannir l'IP
## 🧹 Remédiation
- Retirer les clés inconnues de `/root/.ssh/authorized_keys`
- `PermitRootLogin no` et utilisation de comptes nominatifs + sudo

## ✅ Clôture
- Documenter les constats dans les commentaires du Case
- Classer : **vrai positif** / **faux positif** / **test**
- Passer le Case en *Closed* (les alertes liées passent en *Closed*)
