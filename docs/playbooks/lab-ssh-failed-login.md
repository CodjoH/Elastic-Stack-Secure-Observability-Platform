# 🔐 Playbook — Échecs d'authentification SSH
## 🔎 Investigation
- Combien d'échecs, depuis quelles IP, sur quels comptes ?
- Compte inexistant (*invalid user*) → reconnaissance / scan ; compte réel → tentative ciblée
- Corréler avec la règle *Brute force* et une éventuelle connexion réussie ultérieure
## 🛑 Confinement
- Si volume élevé : fail2ban bannit automatiquement au-delà de 5 échecs / 10 min
## 🧹 Remédiation
- Sensibiliser l'utilisateur si erreur légitime ; sinon traiter comme brute force

## ✅ Clôture
- Documenter les constats dans les commentaires du Case
- Classer : **vrai positif** / **faux positif** / **test**
- Passer le Case en *Closed* (les alertes liées passent en *Closed*)
