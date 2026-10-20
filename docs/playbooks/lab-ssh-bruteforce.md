# 🔥 Playbook — Brute force SSH
## 🔎 Investigation
- Identifier l'IP source et les comptes ciblés (voir commentaire de synthèse)
- Vérifier si une connexion **réussie** a suivi depuis la même IP : dashboard *SOC Lab* → *Connexions SSH réussies*
- L'IP est-elle interne (lab) ou externe ? Est-elle connue ?
## 🛑 Confinement
- **Automatique** : fail2ban bannit l'IP 1 h sur le client (voir alerte *Réponse auto - IP bannie*)
- Vérifier : `fail2ban-client status sshd` sur l'hôte
- Bannissement prolongé si malveillant : `fail2ban-client set sshd banip <IP>`
## 🧹 Remédiation
- Désactiver l'authentification SSH par mot de passe (`PasswordAuthentication no`)
- Interdire root en SSH (`PermitRootLogin no`)
- Réinitialiser le mot de passe des comptes ciblés existants

## ✅ Clôture
- Documenter les constats dans les commentaires du Case
- Classer : **vrai positif** / **faux positif** / **test**
- Passer le Case en *Closed* (les alertes liées passent en *Closed*)
