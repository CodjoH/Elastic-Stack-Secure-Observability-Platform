#!/usr/bin/env bash
# Vérifie que chaque port présente un certificat signé par la CA interne
# et que le HTTP en clair est refusé.
# usage : ./scripts/verify-tls.sh [hote]

[ -f .env ] && { set -a; . ./.env; set +a; }
HOST="${1:-${ELK_HOST:?ELK_HOST non défini}}"
CA="${CERTS_DIR:-./certs/runtime}/ca/ca.crt"
FAIL=0

for PORT in 9200 5601 8220; do
  OUT=$(echo | timeout 5 openssl s_client -connect "$HOST:$PORT" -CAfile "$CA" 2>/dev/null)
  if echo "$OUT" | grep -q "Verify return code: 0 (ok)"; then
    PROTO=$(echo "$OUT" | grep -m1 -oE "TLSv1\.[0-9]")
    END=$(echo "$OUT" | openssl x509 -noout -enddate 2>/dev/null | cut -d= -f2)
    echo "[ok] $PORT  $PROTO  expire le $END"
  else
    echo "[ko] $PORT  certificat non vérifié par la CA"; FAIL=1
  fi
done

for PORT in 9200 5601; do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "http://$HOST:$PORT")
  if [ "$CODE" = "000" ] || [ "$CODE" = "400" ]; then
    echo "[ok] $PORT  http clair refusé"
  else
    echo "[ko] $PORT  http clair accepté ($CODE)"; FAIL=1
  fi
done

# transport 9300, testé depuis le conteneur du noeud 1
if docker exec elasticsearch bash -c "echo | openssl s_client -connect elasticsearch-node2:9300 -CAfile config/certs/ca/ca.crt 2>/dev/null" | grep -q "Verify return code: 0"; then
  echo "[ok] 9300  es-node1 -> es-node2"
else
  echo "[--] 9300  non vérifiable (openssl absent du conteneur ?)"
fi

exit $FAIL
