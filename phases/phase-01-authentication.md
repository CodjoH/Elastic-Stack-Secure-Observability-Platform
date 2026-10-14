# Phase 01 — Authentification obligatoire

> **Objectif :** interdire tout accès anonyme au cluster et appliquer le moindre privilège.

## Actions

### 1. Activer la sécurité X-Pack

```yaml
# config/elasticsearch/es-node1.yml
xpack.security.enabled: true
xpack.security.audit.enabled: true
```

### 2. Initialiser les mots de passe des comptes intégrés

```bash
docker exec -it es-node1 bin/elasticsearch-reset-password -u elastic -i
docker exec -it es-node1 bin/elasticsearch-reset-password -u kibana_system -i
```

Les mots de passe sont ensuite stockés uniquement dans `.env` (non versionné).

### 3. Appliquer le moindre privilège

| Compte | Usage | Privilèges |
|---|---|---|
| `elastic` | Administration ponctuelle | Superutilisateur — usage limité |
| `kibana_system` | Connexion Kibana ➔ Elasticsearch | Rôle système Kibana uniquement |
| Comptes Beats dédiés | Écriture des données | Création de documents sur leurs index ([phase 05](phase-05-beats-authentication.md)) |

## Validation

```bash
./tests/authentication/test-authentication.sh
```

| Test | Attendu |
|---|---|
| Requête anonyme | `401 Unauthorized` |
| Mauvais mot de passe | `401 Unauthorized` |
| `elastic` authentifié | `200 OK` |
| `kibana_system` sur un index métier | `403 Forbidden` |

## Résultat

✅ Plus aucune requête n'aboutit sans identifiants valides. Les accès sont tracés dans le journal d'audit.

⬅️ [Phase 00](phase-00-stabilization.md) · ➡️ [Phase 02 — TLS HTTP](phase-02-http-tls.md)
