# 👤 Playbook — Création de compte
## 🔎 Investigation
- Qui a créé le compte (session, sudo) ? Création attendue (ticket, changement) ?
- Groupes du compte (`id <compte>`), shell, présence de clés SSH
## 🛑 Confinement
- Si non autorisé : `usermod -L <compte>` puis `chage -E0 <compte>`
## 🧹 Remédiation
- Supprimer le compte (`userdel -r <compte>`) après collecte des preuves
- Rechercher d'autres mécanismes de persistance (crontab, services systemd, authorized_keys)

## ✅ Clôture
- Documenter les constats dans les commentaires du Case
- Classer : **vrai positif** / **faux positif** / **test**
- Passer le Case en *Closed* (les alertes liées passent en *Closed*)
