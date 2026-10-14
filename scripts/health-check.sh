#!/usr/bin/env bash
# Etat rapide de la plateforme : cluster, noeuds, shards, Kibana, Fleet.
# usage : ./scripts/health-check.sh  (lancé depuis la racine, lit .env)

[ -f .env ] && { set -a; . ./.env; set +a; }
HOST="${ELK_HOST:?ELK_HOST non défini}"
CA="${CERTS_DIR:-./certs/runtime}/ca/ca.crt"
AUTH="elastic:${ELASTIC_PASSWORD:?ELASTIC_PASSWORD non défini}"
FAIL=0

es() { curl -s --cacert "$CA" -u "$AUTH" "https://$HOST:9200$1"; }

echo "--- cluster"
STATUS=$(es "/_cluster/health" | grep -o '"status":"[a-z]*"' | cut -d'"' -f4)
echo "statut : ${STATUS:-injoignable}"
[ "$STATUS" = "red" ] || [ -z "$STATUS" ] && FAIL=1

NODES=$(es "/_cat/nodes?h=name" | wc -l)
echo "noeuds : $NODES"
[ "$NODES" -lt 2 ] && FAIL=1

UNASSIGNED=$(es "/_cat/shards?h=state" | grep -c UNASSIGNED)
echo "shards non alloués : $UNASSIGNED"

echo "--- kibana"
K=$(curl -s --cacert "$CA" -u "$AUTH" "https://$HOST:5601/api/status" | grep -o '"level":"[a-z]*"' | head -1 | cut -d'"' -f4)
echo "kibana : ${K:-injoignable}"
[ "$K" = "available" ] || FAIL=1

echo "--- fleet"
if curl -s --cacert "$CA" "https://$HOST:8220/api/status" | grep -q HEALTHY; then
  echo "fleet server : HEALTHY"
else
  echo "fleet server : KO"; FAIL=1
fi
ONLINE=$(curl -s --cacert "$CA" -u "$AUTH" "https://$HOST:5601/api/fleet/agent_status" | grep -o '"online":[0-9]*' | cut -d: -f2)
echo "agents en ligne : ${ONLINE:-0}"

exit $FAIL
