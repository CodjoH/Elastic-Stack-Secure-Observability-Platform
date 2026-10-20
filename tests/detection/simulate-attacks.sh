#!/usr/bin/env bash
# Scénario bout en bout : brute force SSH -> bannissement fail2ban -> alertes -> Cases SOC-IR.
# A lancer depuis un hôte "attaquant" absent de l'ignoreip de fail2ban (ex. l'hôte ELK lui-même).
# usage : ./tests/detection/simulate-attacks.sh   (depuis la racine, lit .env)
# nettoyage ensuite, sur la cible : fail2ban-client set sshd unbanip <IP de l'attaquant>

[ -f .env ] && { set -a; . ./.env; set +a; }
HOST="${ELK_HOST:?ELK_HOST non défini}"
TARGET="${TARGET_HOST:?TARGET_HOST non défini}"
KEY="${KIBANA_API_KEY:?KIBANA_API_KEY non défini}"
CA="${CERTS_DIR:-./certs/runtime}/ca/ca.crt"
ATTEMPTS="${ATTEMPTS:-8}"
TIMEOUT="${TIMEOUT:-300}"
FAIL=0

api() { curl -s --cacert "$CA" -H "Authorization: ApiKey $KEY" -H 'kbn-xsrf: test' -H 'Content-Type: application/json' "$@"; }

START=$(date -u +%Y-%m-%dT%H:%M:%SZ)
echo "--- attaque : $ATTEMPTS connexions SSH avec un compte inexistant vers $TARGET"
REFUSED=0
for i in $(seq 1 "$ATTEMPTS"); do
  OUT=$(timeout 10 ssh -o BatchMode=yes -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
        -o ConnectTimeout=4 -o PubkeyAuthentication=no "soc-test-$$@$TARGET" true 2>&1)
  echo "$OUT" | grep -q "Connection refused" && REFUSED=$((REFUSED+1))
done
echo "connexions refusées par le pare-feu : $REFUSED"
[ "$REFUSED" -gt 0 ] && echo "confinement : IP bannie par fail2ban" || { echo "confinement : aucun bannissement observé"; FAIL=1; }

count() {  # nombre d'alertes d'une règle depuis le début du test
  api -X POST "https://$HOST:9200/.alerts-security.alerts-default/_count" -d "{\"query\":{\"bool\":{\"filter\":[
    {\"term\":{\"kibana.alert.rule.rule_id\":\"$1\"}},{\"range\":{\"@timestamp\":{\"gte\":\"$START\"}}}]}}}" \
    | grep -o '"count":[0-9]*' | cut -d: -f2
}

echo "--- détection (attente max ${TIMEOUT}s)"
# fail2ban (mode aggressive) compte plusieurs lignes par tentative et bannit souvent avant que
# la règle à seuil "brute force" (>= 5 échecs) ne soit atteinte : elle est seulement rapportée.
EXPECTED="lab-ssh-failed-login lab-fail2ban-ban"
INFO="lab-ssh-bruteforce"
DEADLINE=$(( $(date +%s) + TIMEOUT ))
while :; do
  MISSING=""
  for r in $EXPECTED; do n=$(count "$r"); [ "${n:-0}" -gt 0 ] || MISSING="$MISSING $r"; done
  [ -z "$MISSING" ] || [ "$(date +%s)" -ge "$DEADLINE" ] && break
  sleep 15
done
for r in $EXPECTED; do printf '%-24s %s alerte(s)\n' "$r" "$(count "$r")"; done
for r in $INFO; do printf '%-24s %s alerte(s) (informatif)\n' "$r" "$(count "$r")"; done
[ -n "$MISSING" ] && { echo "règles sans alerte :$MISSING"; FAIL=1; }

echo "--- réponse (Cases ouverts par SOC-IR)"
sleep 70  # laisser passer un cycle du timer SOC-IR
for r in $EXPECTED; do
  N=$(api "https://$HOST:5601/api/cases/_find?tags=rule:$r&status=open" | grep -o '"total":[0-9]*' | cut -d: -f2)
  printf '%-24s %s case(s) ouvert(s)\n' "$r" "${N:-0}"
  [ "${N:-0}" -gt 0 ] || FAIL=1
done

[ "$FAIL" -eq 0 ] && echo "RESULTAT : chaîne détection -> réponse OK" || echo "RESULTAT : ECHEC"
exit $FAIL
