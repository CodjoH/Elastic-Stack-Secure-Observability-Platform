#!/usr/bin/env bash
# ============================================================
# Tests d'authentification et de moindre privilège
# Attendu : toute requête anonyme ou mal authentifiée est rejetée.
# ============================================================
set -uo pipefail
[ -f .env ] && { set -a; . ./.env; set +a; }
URL="https://${ELK_HOST:-<ELK_HOST_IP>}:9200"
CA="${CA_CERT:-certs/runtime/ca/ca.crt}"
PASS=0; FAIL=0

expect() {  # expect <description> <code attendu> <args curl...>
  local desc=$1 want=$2; shift 2
  local got; got=$(curl -s -o /dev/null -w "%{http_code}" --cacert "$CA" "$@")
  if [ "$got" = "$want" ]; then echo "  [PASS] $desc ($got)"; PASS=$((PASS+1))
  else echo "  [FAIL] $desc (attendu $want, obtenu $got)"; FAIL=$((FAIL+1)); fi
}

echo "== Authentification =="
expect "Requête anonyme rejetée"                  401 "$URL/"
expect "Mot de passe invalide rejeté"             401 -u elastic:mauvais "$URL/"
expect "Utilisateur inexistant rejeté"            401 -u intrus:intrus "$URL/"
expect "Superutilisateur authentifié"             200 -u "elastic:$ELASTIC_PASSWORD" "$URL/"

echo "== Moindre privilège =="
expect "kibana_system ne lit pas les index métier" 403 -u "kibana_system:$KIBANA_SYSTEM_PASSWORD" "$URL/logs-*/_search"
expect "kibana_system ne crée pas d'utilisateur"   403 -u "kibana_system:$KIBANA_SYSTEM_PASSWORD" \
       -X PUT "$URL/_security/user/test" -H 'Content-Type: application/json' -d '{"password":"xxxxxxxx","roles":[]}'

echo; echo "Résultat : $PASS réussi(s), $FAIL échec(s)"; [ $FAIL -eq 0 ]
