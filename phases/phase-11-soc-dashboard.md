# Phase 11 : dashboard SOC

Un tableau de bord unique pour l'analyste : alertes, activité d'authentification et santé des hôtes. Il est entièrement généré par script, donc reproductible et versionné.

```bash
./scripts/build-dashboard.py                                        # import direct (clé API dans .env)
./scripts/build-dashboard.py --out dashboards/soc-overview.ndjson   # régénère l'export versionné
```

Sans script : Stack Management > Saved objects > Import > [dashboards/soc-overview.ndjson](../dashboards/soc-overview.ndjson).

## Contenu

| Bloc | Panneaux | Data view |
|---|---|---|
| Indicateurs | alertes ouvertes, High/Critical, échecs SSH, commandes sudo, hôtes surveillés | toutes |
| Alertes | évolution par sévérité, répartition par règle et par sévérité, tactiques MITRE, tableau règle / hôte / utilisateur | `.alerts-security.alerts-default` |
| SSH | succès vs échecs, top IP sources, comptes ciblés, connexions réussies | `logs-system.auth-*` |
| Comptes | `useradd` / `userdel` / `usermod`, événements par programme | `logs-system.auth-*` |
| Santé | CPU, mémoire, charge, disque par hôte | `metrics-system.*-*` |

Plage par défaut : 24 h, rafraîchissement automatique chaque minute.

![Dashboard SOC](../Proof/soc/soc-dashboard.png)

*« Alertes ouvertes : 0 » : toutes les alertes ont été prises en charge par SOC-IR ([phase 12](phase-12-incident-response.md)).*

## Incidents

**Import refusé (HTTP 500)** : `Cannot read properties of undefined (reading 'layers')`. Sans `typeMigrationVersion`, Kibana considère les objets Lens comme anciens et leur applique des migrations qui attendent l'ancien format (`indexpattern` au lieu de `formBased`). Corrigé en déclarant les versions (`lens` / `dashboard` 8.9.0, `index-pattern` 8.0.0).

**Tableaux vides** : les panneaux groupés par `source.ip` n'affichaient rien. Dans Lens, une colonne *terms* sur un champ de type `ip` doit être déclarée `dataType: ip`, pas `string`.

**Libellés ignorés** : les tuiles affichaient *Count of records*. Un libellé personnalisé n'est pris en compte qu'avec `customLabel: true`.

## Ce que le dashboard a montré

Dès sa mise en service, il a confirmé le diagnostic de la [phase 09](phase-09-fleet-troubleshooting.md) : la VM centrale tourne à ~75-80 % de mémoire et une charge proche de 2,5, contre moins de 1 pour le client.

Retour au [README](../README.md)
