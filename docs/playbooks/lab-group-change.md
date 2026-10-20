# 🧑‍🤝‍🧑 Playbook — Modification de groupe
## 🔎 Investigation
- Quel compte, quel groupe ? Groupe privilégié (`sudo`, `adm`, `docker`, `root`) = **critique**
- Changement attendu ?
## 🛑 Confinement
- Retirer le compte du groupe : `gpasswd -d <compte> <groupe>`
## 🧹 Remédiation
- Revue des membres des groupes privilégiés (`getent group sudo`)

## ✅ Clôture
- Documenter les constats dans les commentaires du Case
- Classer : **vrai positif** / **faux positif** / **test**
- Passer le Case en *Closed* (les alertes liées passent en *Closed*)
