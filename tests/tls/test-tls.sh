#!/usr/bin/env bash
# ============================================================
# Tests TLS — confiance, protocoles, protection MitM
# ============================================================
set -uo pipefail
HOST="${ELK_HOST:-192.168.56.51}"
CA="${CA_CERT:-certs/runtime/ca/ca.crt}"
PASS=0; FAIL=0
res() { if [ "$1" -eq 0 ]; then echo "  [PASS] $2"; PASS=$((PASS+1)); else echo "  [FAIL] $2"; FAIL=$((FAIL+1)); fi; }

for PORT in 9200 5601 8220; do
  echo "== Port $PORT =="
  echo | openssl s_client -connect "$HOST:$PORT" -CAfile "$CA" -verify_return_error >/dev/null 2>&1
  res $? "Certificat validé par la CA interne"

  # Sans la CA interne, la vérification DOIT échouer (simulation MitM / CA inconnue)
  echo | openssl s_client -connect "$HOST:$PORT" -CAfile /etc/ssl/certs/ca-certificates.crt -verify_return_error >/dev/null 2>&1
  [ $? -ne 0 ]; res $? "Rejet si la CA n'est pas de confiance"

  # Protocoles obsolètes refusés
  echo | openssl s_client -connect "$HOST:$PORT" -tls1_1 >/dev/null 2>&1
  [ $? -ne 0 ]; res $? "TLS 1.1 refusé"

  echo | openssl s_client -connect "$HOST:$PORT" -tls1_2 -CAfile "$CA" >/dev/null 2>&1
  res $? "TLS 1.2+ accepté"
done

echo; echo "Résultat : $PASS réussi(s), $FAIL échec(s)"; [ $FAIL -eq 0 ]
