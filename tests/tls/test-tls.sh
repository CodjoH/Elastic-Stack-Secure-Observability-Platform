#!/usr/bin/env bash
# Pour chaque port : certificat validé par la CA interne, rejeté sans elle
# (cas d'un certificat présenté par un tiers), TLS 1.1 refusé.

[ -f .env ] && { set -a; . ./.env; set +a; }
HOST="${ELK_HOST:?ELK_HOST non défini}"
CA="${CERTS_DIR:-./certs/runtime}/ca/ca.crt"
OK=0; KO=0
r() { if [ "$1" -eq 0 ]; then echo "[ok] $2"; OK=$((OK+1)); else echo "[ko] $2"; KO=$((KO+1)); fi; }

for PORT in 9200 5601 8220; do
  echo | openssl s_client -connect "$HOST:$PORT" -CAfile "$CA" -verify_return_error >/dev/null 2>&1
  r $? "$PORT certificat validé par la CA interne"

  echo | openssl s_client -connect "$HOST:$PORT" -CAfile /etc/ssl/certs/ca-certificates.crt -verify_return_error >/dev/null 2>&1
  [ $? -ne 0 ]; r $? "$PORT refusé avec les CA publiques du système"

  echo | openssl s_client -connect "$HOST:$PORT" -tls1_1 >/dev/null 2>&1
  [ $? -ne 0 ]; r $? "$PORT TLS 1.1 refusé"
done

echo "$OK ok / $KO ko"
[ $KO -eq 0 ]
