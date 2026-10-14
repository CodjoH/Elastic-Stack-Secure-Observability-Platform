#!/usr/bin/env bash
# ============================================================
# health-check.sh — État de santé global de la plateforme
# Usage : ./scripts/health-check.sh   (lit les variables de .env)
# ============================================================
set -uo pipefail

[ -f .env ] && { set -a; . ./.env; set +a; }
HOST="${ELK_HOST:-<ELK_HOST_IP>}"
CA="${CA_CERT:-certs/runtime/ca/ca.crt}"
AUTH="elastic:${ELASTIC_PASSWORD:?ELASTIC_PASSWORD non défini}"

GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()   { echo -e "  ${GREEN}[OK]${NC}   $1"; }
warn() { echo -e "  ${YELLOW}[WARN]${NC} $1"; }
ko()   { echo -e "  ${RED}[KO]${NC}   $1"; FAIL=1; }
FAIL=0
es() { curl -s --cacert "$CA" -u "$AUTH" "https://${HOST}:9200$1"; }

echo "== Cluster Elasticsearch =="
STATUS=$(es "/_cluster/health" | grep -o '"status":"[a-z]*"' | cut -d'"' -f4)
case "$STATUS" in
  green)  ok "Statut du cluster : green" ;;
  yellow) warn "Statut du cluster : yellow (réplicas non alloués ?)" ;;
  *)      ko "Statut du cluster : ${STATUS:-injoignable}" ;;
esac
NODES=$(es "/_cat/nodes?h=name" | wc -l)
[ "$NODES" -ge 2 ] && ok "Nœuds actifs : $NODES" || ko "Nœuds actifs : $NODES (2 attendus)"
UNASSIGNED=$(es "/_cat/shards?h=state" | grep -c UNASSIGNED || true)
[ "$UNASSIGNED" -eq 0 ] && ok "Aucun shard non alloué" || warn "$UNASSIGNED shard(s) non alloué(s)"

echo "== Kibana =="
KSTATUS=$(curl -s --cacert "$CA" -u "$AUTH" "https://${HOST}:5601/api/status" | grep -o '"level":"[a-z]*"' | head -1 | cut -d'"' -f4)
[ "$KSTATUS" = "available" ] && ok "Kibana disponible" || ko "Kibana : ${KSTATUS:-injoignable}"

echo "== Fleet Server =="
curl -s --cacert "$CA" "https://${HOST}:8220/api/status" | grep -q '"HEALTHY"' \
  && ok "Fleet Server HEALTHY" || ko "Fleet Server indisponible"

AGENTS=$(curl -s --cacert "$CA" -u "$AUTH" "https://${HOST}:5601/api/fleet/agent_status" | grep -o '"online":[0-9]*' | cut -d: -f2)
[ "${AGENTS:-0}" -ge 1 ] && ok "Agents en ligne : $AGENTS" || warn "Aucun agent en ligne"

echo
[ $FAIL -eq 0 ] && echo -e "${GREEN}Plateforme opérationnelle.${NC}" || echo -e "${RED}Anomalies détectées.${NC}"
exit $FAIL
