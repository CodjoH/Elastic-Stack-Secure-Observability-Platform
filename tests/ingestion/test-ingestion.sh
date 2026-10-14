#!/usr/bin/env bash
# ============================================================
# Tests d'ingestion — la télémétrie arrive bien dans le cluster
# ============================================================
set -uo pipefail
[ -f .env ] && { set -a; . ./.env; set +a; }
HOST="${ELK_HOST:-192.168.56.51}"
CA="${CA_CERT:-certs/runtime/ca/ca.crt}"
AUTH="elastic:${ELASTIC_PASSWORD:?ELASTIC_PASSWORD non défini}"
es() { curl -s --cacert "$CA" -u "$AUTH" -H 'Content-Type: application/json' "$@"; }
PASS=0; FAIL=0
res() { if [ "$1" -eq 0 ]; then echo "  [PASS] $2"; PASS=$((PASS+1)); else echo "  [FAIL] $2"; FAIL=$((FAIL+1)); fi; }

echo "== Écriture / lecture de bout en bout =="
ID="ingest-test-$(date +%s)"
es -X POST "https://$HOST:9200/ingestion-test/_doc/$ID?refresh=true" -d "{\"message\":\"test\",\"@timestamp\":\"$(date -u +%FT%TZ)\"}" | grep -q '"result":"created"'
res $? "Indexation d'un document"
es "https://$HOST:9200/ingestion-test/_doc/$ID" | grep -q '"found":true'
res $? "Relecture du document"
es -X DELETE "https://$HOST:9200/ingestion-test" >/dev/null

echo "== Flux Elastic Agent =="
for DS in "logs-system.syslog-default" "metrics-system.cpu-default"; do
  COUNT=$(es "https://$HOST:9200/$DS/_count?q=@timestamp:>now-5m" | grep -o '"count":[0-9]*' | cut -d: -f2)
  [ "${COUNT:-0}" -gt 0 ]; res $? "$DS : ${COUNT:-0} évènement(s) sur les 5 dernières minutes"
done

echo "== Client-Lin01 =="
es "https://$HOST:9200/logs-*/_count?q=host.name:Client-Lin01" | grep -qE '"count":[1-9]'
res $? "Évènements reçus depuis Client-Lin01"

echo; echo "Résultat : $PASS réussi(s), $FAIL échec(s)"; [ $FAIL -eq 0 ]
