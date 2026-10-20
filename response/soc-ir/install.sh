#!/usr/bin/env bash
# Installe SOC-IR sur l'hôte central (ELK) : script, playbooks, CA, clé API, timer systemd.
# usage : sudo -E ./response/soc-ir/install.sh   (depuis la racine, .env chargé)
#   SOC_IR_API_KEY : clé API Kibana dédiée (Stack Management > API keys), jamais versionnée
set -euo pipefail

[ -f .env ] && { set -a; . ./.env; set +a; }
HOST="${ELK_HOST:?ELK_HOST non défini}"
CA="${CERTS_DIR:-./certs/runtime}/ca/ca.crt"
[ "$(id -u)" -eq 0 ] || { echo "à lancer en root"; exit 1; }
[ -f "$CA" ] || { echo "CA introuvable : $CA"; exit 1; }

install -d -m 700 /etc/soc-ir /etc/soc-ir/playbooks /var/lib/soc-ir
install -m 750 response/soc-ir/soc-ir.py /usr/local/bin/soc-ir.py
install -m 640 docs/playbooks/*.md /etc/soc-ir/playbooks/
install -m 644 "$CA" /etc/soc-ir/ca.crt

if [ -n "${SOC_IR_API_KEY:-}" ]; then
  (umask 077; printf '%s' "$SOC_IR_API_KEY" > /etc/soc-ir/apikey)
elif [ ! -s /etc/soc-ir/apikey ]; then
  echo "SOC_IR_API_KEY non fourni et /etc/soc-ir/apikey absent"; exit 1
fi

# le nom d'hôte doit figurer dans le SAN des certificats Kibana / Elasticsearch
cat > /etc/soc-ir/soc-ir.env <<EOF
SOC_IR_KIBANA=https://$HOST:5601
SOC_IR_ES=https://$HOST:9200
EOF
chmod 600 /etc/soc-ir/soc-ir.env

install -m 644 response/soc-ir/soc-ir.service response/soc-ir/soc-ir.timer /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now soc-ir.timer
systemctl start soc-ir.service
echo "SOC-IR installé ; journal : /var/log/soc-ir.log"
tail -n 5 /var/log/soc-ir.log 2>/dev/null || true
