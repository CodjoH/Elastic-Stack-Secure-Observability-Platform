#!/usr/bin/env bash
# Requêtes anonymes / mauvais identifiants rejetés, kibana_system limité.

[ -f .env ] && { set -a; . ./.env; set +a; }
URL="https://${ELK_HOST:?ELK_HOST non défini}:9200"
CA="${CERTS_DIR:-./certs/runtime}/ca/ca.crt"
OK=0; KO=0

check() {   # check "description" code_attendu [options curl]
  local desc=$1 want=$2; shift 2
  local got
  got=$(curl -s -o /dev/null -w "%{http_code}" --cacert "$CA" "$@")
  if [ "$got" = "$want" ]; then echo "[ok] $desc ($got)"; OK=$((OK+1))
  else echo "[ko] $desc : attendu $want, reçu $got"; KO=$((KO+1)); fi
}

check "anonyme"                          401 "$URL/"
check "mauvais mot de passe"             401 -u elastic:test "$URL/"
check "utilisateur inconnu"              401 -u inconnu:test "$URL/"
check "elastic authentifié"              200 -u "elastic:$ELASTIC_PASSWORD" "$URL/"
check "kibana_system lit logs-*"         403 -u "kibana_system:$KIBANA_SYSTEM_PASSWORD" "$URL/logs-*/_search"
check "kibana_system crée un user"       403 -u "kibana_system:$KIBANA_SYSTEM_PASSWORD" \
      -X PUT "$URL/_security/user/test" -H 'Content-Type: application/json' -d '{"password":"testtest","roles":[]}'

echo "$OK ok / $KO ko"
[ $KO -eq 0 ]
