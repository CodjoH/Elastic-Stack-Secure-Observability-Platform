# 🛡️ Playbook — Confinement automatique (fail2ban)
## 🔎 Investigation
- Une IP a été bannie automatiquement : retrouver le Case *Brute force* associé
- Vérifier qu'aucune connexion n'a réussi avant le bannissement
## 🛑 Confinement
- Déjà appliqué (nftables, port 22, 1 h). Vérifier : `fail2ban-client status sshd`
- Levée manuelle si faux positif : `fail2ban-client set sshd unbanip <IP>`
## 🧹 Remédiation
- Si attaque réelle : bannissement permanent / règle pare-feu en amont

## ✅ Clôture
- Documenter les constats dans les commentaires du Case
- Classer : **vrai positif** / **faux positif** / **test**
- Passer le Case en *Closed* (les alertes liées passent en *Closed*)
