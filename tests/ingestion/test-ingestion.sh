#!/usr/bin/env bash
# Ecriture/lecture d'un document puis présence de données récentes des agents.

[ -f .env ] && { set -a; . ./.env; set +a; }
HOST="${ELK_HOST:?ELK_HOST non défini}"
CA="${CERTS_DIR:-./certs/runtime}/ca/ca.crt"
AUTH="elastic:${ELASTIC_PASSWORD:?ELASTIC_PASSWORD non défini}"
es() { curl -s --cacert "$CA" -u "$AUTH" -H 'Content-Type: application/json' "$@"; }
OK=0; KO=0
r() { if [ "$1" -eq 0 ]; then echo "[ok] $2"; OK=$((OK+1)); else echo "[ko] $2"; KO=$((KO+1)); fi; }

ID="t$(date +%s)"
es -X POST "https://$HOST:9200/test-ingestion/_doc/$ID?refresh=true" \
   -d "{\"message\":\"test\",\"@timestamp\":\"$(date -u +%FT%TZ)\"}" | grep -q '"result":"created"'
r $? "indexation"
es "https://$HOST:9200/test-ingestion/_doc/$ID" | grep -q '"found":true'
r $? "relecture"
es -X DELETE "https://$HOST:9200/test-ingestion" >/dev/null

for DS in logs-system.syslog-default metrics-system.cpu-default; do
  N=$(es "https://$HOST:9200/$DS/_count?q=@timestamp:>now-5m" | grep -o '"count":[0-9]*' | cut -d: -f2)
  [ "${N:-0}" -gt 0 ]; r $? "$DS : ${N:-0} docs sur 5 min"
done

es "https://$HOST:9200/logs-*/_count?q=host.name:Client-Lin01" | grep -qE '"count":[1-9]'
r $? "données reçues de Client-Lin01"

echo "$OK ok / $KO ko"
[ $KO -eq 0 ]
