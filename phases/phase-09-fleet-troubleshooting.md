# Phase 09 : remise en état de Fleet (agents Unhealthy)

Après la [phase 08](phase-08-upgrade.md), Fleet affichait Client-Lin01 en **Unhealthy**, CPU et mémoire à `N/A`. En regardant de près, la mise à jour à distance de l'agent n'avait en fait jamais abouti : l'agent était resté en **8.0.0** face à une stack 8.11.4.

## Diagnostic

```bash
sudo elastic-agent status
# metricbeat_monitoring (DEGRADED) Missed last check-in
# metricbeat (STARTING) / filebeat (CONFIGURING) Updating configuration
sudo elastic-agent version     # Binary: 8.0.0
```

Les journaux des Beats s'arrêtaient tous sur `Applying settings for output` : la policy générée par Fleet 8.11 n'était plus applicable par des Beats 8.0, qui restaient bloqués puis rataient leurs check-ins. Fleet Server, lui, répondait `HEALTHY` depuis le client (`curl https://<ELK_HOST>:8220/api/status`), le réseau et le TLS n'étaient donc pas en cause.

## Incident 1 : l'upgrade Fleet échoue (timeout)

L'action *Upgrade agent* depuis Kibana échouait au bout de deux minutes :

```
failed upgrade of agent binary: fetching package failed:
net/http: request canceled (Client.Timeout ...)
```

Le paquet 8.11.4 fait ~570 Mo et l'agent 8.0 le télécharge avec un timeout fixe de 120 s (`agent.download.timeout`), intenable sur une connexion lente.

## Incident 2 : le paquet pré-téléchargé est effacé

J'ai déposé le paquet et son `.sha512` (vérifié) dans le dossier de téléchargement de l'agent, puis relancé l'upgrade. Nouvel échec :

```
failed verification of agent binary: hash for 'elastic-agent-8.11.4-linux-x86_64.tar.gz' not found
```

Les deux fichiers avaient disparu après l'échec. Mon analyse : en 8.0, le répertoire « drop » (source locale) et le répertoire de téléchargement de l'agent pointent sur le même dossier ; l'agent recopie le paquet sur lui-même, ce qui le vide, la vérification du hash échoue et il nettoie. Dans tous les cas, cette voie ne permet pas de mettre à jour ce 8.0.

## Correction : réinstallation propre

```bash
# paquet téléchargé hors du dossier de l'agent, puis vérifié
curl -LO https://artifacts.elastic.co/downloads/beats/elastic-agent/elastic-agent-8.11.4-linux-x86_64.tar.gz
curl -LO https://artifacts.elastic.co/downloads/beats/elastic-agent/elastic-agent-8.11.4-linux-x86_64.tar.gz.sha512
sha512sum -c elastic-agent-8.11.4-linux-x86_64.tar.gz.sha512

tar xzf elastic-agent-8.11.4-linux-x86_64.tar.gz && cd elastic-agent-8.11.4-linux-x86_64
sudo ./elastic-agent install --force --non-interactive \
  --url=https://<ELK_HOST>:8220 \
  --enrollment-token=<TOKEN_DEFAULT_POLICY> \
  --certificate-authorities=/etc/elk/certs/ca.crt
```

Piège rencontré : le premier jeton utilisé était celui de la *Fleet Server policy*. L'agent tentait alors de démarrer un Fleet Server (`elastic-agent must be bootstrapped with a fleet-server`). Réaffectation à la **Default policy** depuis Fleet, puis l'ancienne entrée 8.0.0 (passée *Offline*) a été désenrôlée.

## Incident 3 : Fleet Server Unhealthy après un changement de policy

L'agent de l'hôte central est passé *Unhealthy* juste après une réaffectation de policy : la nouvelle unité `fleet_server` restait en `STARTING` pendant que l'ancienne tournait encore. Un redémarrage de l'agent a suffi :

```bash
sudo systemctl restart elastic-agent
sudo elastic-agent status   # fleet: HEALTHY / elastic-agent: HEALTHY
```

Le noyau signalait aussi des `rcu: ... OOM is now expected behavior` : la VM centrale (2 nœuds Elasticsearch + Kibana + Fleet Server sur 4 vCPU / 8 Go) manque ponctuellement de CPU, ce qui fait rater des check-ins à tous les composants en même temps. À surveiller dans le [dashboard SOC](phase-11-soc-dashboard.md) (charge système, mémoire).

## Horloges

Les deux hôtes avaient `System clock synchronized: no`. NTP activé partout, pour que les horodatages des logs et des alertes soient cohérents :

```bash
sudo timedatectl set-ntp true
timedatectl | grep synchronized   # yes
```

## Vérification

Les deux agents en 8.11.4, `HEALTHY` dans Fleet, CPU et mémoire remontés pour Client-Lin01.

![Agents Healthy dans Fleet](../screenshots/soc/fleet-healthy.png)

Retour au [README](../README.md)
