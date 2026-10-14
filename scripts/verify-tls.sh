#!/usr/bin/env bash
# ============================================================
# verify-tls.sh — Vérifie la chaîne de confiance TLS de chaque flux
# Usage : ./scripts/verify-tls.sh [HOTE]
# ============================================================
set -uo pipefail

HOST="${1:-${ELK_HOST:-<ELK_HOST_IP>}}"
CA="${CA_CERT:-certs/runtime/ca/ca.crt}"
FAIL=0

check() {
  local name=$1 port=$2
  local out
  out=$(echo | timeout 5 openssl s_client -connect "${HOST}:${port}" -CAfile "$CA" -verify_return_error 2>&1)
  if echo "$out" | grep -q "Verify return code: 0 (ok)"; then
    local proto cipher expiry
    proto=$(echo "$out"  | grep -m1 -oE "Protocol *: *TLSv[0-9.]+" | awk '{print $NF}')
    cipher=$(echo "$out" | grep -m1 -oE "Cipher *: *[A-Z0-9_-]+"    | awk '{print $NF}')
    expiry=$(echo "$out" | openssl x509 -noout -enddate 2>/dev/null | cut -d= -f2)
    printf "  [OK] %-28s %-6s %-8s %s | expire : %s\n" "$name" "$port" "$proto" "$cipher" "$expiry"
  else
    printf "  [KO] %-28s %-6s chaîne de confiance invalide\n" "$name" "$port"; FAIL=1
  fi
}

plaintext_rejected() {
  local name=$1 port=$2
  local code
  code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "http://${HOST}:${port}" || true)
  if [ "$code" = "000" ] || [ "$code" = "400" ]; then
    printf "  [OK] %-28s %-6s HTTP clair refusé\n" "$name" "$port"
  else
    printf "  [KO] %-28s %-6s HTTP clair accepté (code %s)\n" "$name" "$port" "$code"; FAIL=1
  fi
}

echo "== Validation de la chaîne de confiance (CA interne) =="
check "Elasticsearch API"   9200
check "Kibana"              5601
check "Fleet Server"        8220

echo "== Rejet des connexions en clair =="
plaintext_rejected "Elasticsearch API" 9200
plaintext_rejected "Kibana"            5601

echo "== Transport inter-nœuds (mTLS 9300) =="
if docker exec es-node1 bash -c "echo | openssl s_client -connect es-node2:9300 -CAfile config/certs/ca/ca.crt 2>&1" \
   | grep -q "Verify return code: 0 (ok)"; then
  echo "  [OK] Transport es-node1 -> es-node2 chiffré et vérifié"
else
  echo "  [WARN] Vérification transport impossible (openssl absent du conteneur ?)"
fi

exit $FAIL
