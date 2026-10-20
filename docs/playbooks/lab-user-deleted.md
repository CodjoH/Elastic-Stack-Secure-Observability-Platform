# 🗑️ Playbook — Suppression de compte
## 🔎 Investigation
- Suppression planifiée (départ, nettoyage) ou effacement de traces après compromission ?
- Le compte a-t-il eu une activité récente (connexions, sudo) ?
## 🛑 Confinement
- Si suspect : isoler l'hôte, préserver les logs (`/var/log/auth.log`)
## 🧹 Remédiation
- Restaurer depuis sauvegarde si légitime ; sinon investigation forensique

## ✅ Clôture
- Documenter les constats dans les commentaires du Case
- Classer : **vrai positif** / **faux positif** / **test**
- Passer le Case en *Closed* (les alertes liées passent en *Closed*)
