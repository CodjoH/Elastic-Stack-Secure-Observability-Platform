#!/usr/bin/env python3
"""SOC Lab - réponse à incident automatisée.

Toutes les minutes (timer systemd) : récupère les alertes Security ouvertes de sévérité >= medium,
les regroupe par (règle, hôte), crée ou complète un Case Kibana avec le playbook de la règle,
attache les alertes au Case puis les passe en "acknowledged".

La licence basic ne permet pas aux règles d'ouvrir un Case elles-mêmes : ce service fait le lien.
Configuration par variables d'environnement (voir soc-ir.service) ; playbooks = docs/playbooks/<rule_id>.md
"""
import json, logging, os, ssl, time, urllib.error, urllib.request
from collections import defaultdict
from datetime import datetime, timezone

KB = os.environ.get("SOC_IR_KIBANA", "https://localhost:5601")
ES = os.environ.get("SOC_IR_ES", "https://localhost:9200")
KEYFILE = os.environ.get("SOC_IR_KEYFILE", "/etc/soc-ir/apikey")
CAFILE = os.environ.get("SOC_IR_CA", "/etc/soc-ir/ca.crt")
STATE = os.environ.get("SOC_IR_STATE", "/var/lib/soc-ir/state.json")
PLAYBOOK_DIR = os.environ.get("SOC_IR_PLAYBOOKS", "/etc/soc-ir/playbooks")
ALERTS = ".alerts-security.alerts-default"
SEVERITIES = ["medium", "high", "critical"]

log = logging.getLogger("soc-ir")
_session = {}


def session():
    """Clé API et contexte TLS, chargés au premier appel réseau (le module reste importable pour les tests)."""
    if not _session:
        with open(KEYFILE) as f:
            _session["key"] = f.read().strip()
        _session["ctx"] = ssl.create_default_context(cafile=CAFILE)
    return _session["key"], _session["ctx"]


def playbook(rule_id):
    """Playbook Markdown de la règle (docs/playbooks/<rule_id>.md), sinon le playbook générique."""
    for name in (rule_id, "default"):
        path = os.path.join(PLAYBOOK_DIR, f"{name}.md")
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as f:
                return f.read()
    return "Aucun playbook trouvé pour cette règle.\n"


def call(base, method, path, body=None):
    key, ctx = session()
    req = urllib.request.Request(base + path, method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Authorization": "ApiKey " + key, "kbn-xsrf": "soc-ir",
                                          "Content-Type": "application/json"})
    with urllib.request.urlopen(req, context=ctx, timeout=30) as r:
        return json.loads(r.read() or b"{}")


def acknowledge(ids):
    """Passe les alertes en "acknowledged" ; tolère les conflits de version avec le moteur de règles."""
    for attempt in range(3):
        try:
            return call(KB, "POST", "/api/detection_engine/signals/status",
                        {"signal_ids": ids, "status": "acknowledged", "conflicts": "proceed"})
        except urllib.error.HTTPError as e:
            if e.code != 409 or attempt == 2:
                raise
            time.sleep(2)


def load_state():
    try:
        with open(STATE, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_state(state):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    tmp = STATE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=1)
    os.replace(tmp, STATE)


def fetch_alerts():
    q = {"size": 500, "sort": [{"@timestamp": "asc"}],
         "_source": ["@timestamp", "kibana.alert.rule.rule_id", "kibana.alert.rule.uuid", "kibana.alert.rule.name",
                     "kibana.alert.severity", "kibana.alert.risk_score", "host.name", "source.ip", "user.name",
                     "message", "kibana.alert.original_event.action", "kibana.alert.threshold_result"],
         "query": {"bool": {"filter": [{"term": {"kibana.alert.workflow_status": "open"}},
                                       {"terms": {"kibana.alert.severity": SEVERITIES}}]}}}
    res = call(ES, "POST", f"/{ALERTS}/_search", q)
    return res["hits"]["hits"]


def get(d, key):
    """Lit un champ qu'il soit stocké à plat ("a.b.c") ou imbriqué ({"a": {"b": ...}})."""
    if not isinstance(d, dict):
        return None
    if key in d:
        return d[key]
    parts = key.split(".")
    for i in range(1, len(parts)):
        head = ".".join(parts[:i])
        if head in d:
            found = get(d[head], ".".join(parts[i:]))
            if found is not None:
                return found
    return None


def case_is_open(case_id):
    try:
        return call(KB, "GET", f"/api/cases/{case_id}")["status"] != "closed"
    except Exception:
        return False


def create_case(rule_id, rule_name, host, severity):
    title = f"[{severity.upper()}] {rule_name} — {host}"
    desc = (f"Case ouvert automatiquement par **SOC-IR** le "
            f"{datetime.now(timezone.utc).astimezone():%d/%m/%Y %H:%M}.\n\n"
            f"- **Règle** : {rule_name}\n- **Hôte** : `{host}`\n- **Sévérité** : {severity}\n\n"
            + playbook(rule_id))
    body = {"title": title, "description": desc, "owner": "securitySolution",
            "tags": ["auto-ir", f"rule:{rule_id}", f"host:{host}", f"severity:{severity}"],
            "severity": severity if severity in ("low", "medium", "high", "critical") else "medium",
            "settings": {"syncAlerts": True},
            "connector": {"id": "none", "name": "none", "type": ".none", "fields": None}}
    return call(KB, "POST", "/api/cases", body)["id"]


def threshold_ip(src):
    """Pour une alerte à seuil, renvoie la valeur de source.ip du regroupement (sinon None)."""
    for t in get(src, "kibana.alert.threshold_result.terms") or []:
        if t.get("field") == "source.ip":
            return t.get("value")
    return None


def subject(src):
    """Hôte de l'alerte ; à défaut (règle à seuil), l'IP source regroupée."""
    host = get(src, "host.name")
    if host:
        return host
    ip = threshold_ip(src)
    return f"source {ip}" if ip else "inconnu"


def summary(hits):
    ips, users, msgs = set(), set(), []
    for h in hits:
        s = h["_source"]
        ip, user = get(s, "source.ip") or threshold_ip(s), get(s, "user.name")
        if ip: ips.add(str(ip))
        if user: users.add(str(user))
        m = get(s, "message")
        if m and len(msgs) < 5: msgs.append(str(m)[:200])
    first = hits[0]["_source"]["@timestamp"]; last = hits[-1]["_source"]["@timestamp"]
    lines = [f"**SOC-IR** : {len(hits)} nouvelle(s) alerte(s) rattachée(s).",
             f"- Période : `{first}` → `{last}`",
             f"- IP source : {', '.join(f'`{i}`' for i in sorted(ips)) or '—'}",
             f"- Comptes : {', '.join(f'`{u}`' for u in sorted(users)) or '—'}"]
    if msgs:
        lines.append("- Extraits :\n" + "\n".join(f"  - `{m}`" for m in msgs))
    return "\n".join(lines)


def main():
    hits = fetch_alerts()
    if not hits:
        return
    groups = defaultdict(list)
    for h in hits:
        s = h["_source"]
        groups[(get(s, "kibana.alert.rule.rule_id"), subject(s))].append(h)

    state = load_state()
    for (rule_id, host), items in groups.items():
        s0 = items[0]["_source"]
        rule_name, rule_uuid = get(s0, "kibana.alert.rule.name"), get(s0, "kibana.alert.rule.uuid")
        sev = max((get(h["_source"], "kibana.alert.severity") for h in items), key=SEVERITIES.index)
        key = f"{rule_id}|{host}"
        case_id = state.get(key)
        if not case_id or not case_is_open(case_id):
            case_id = create_case(rule_id, rule_name, host, sev)
            state[key] = case_id
            log.info("case créé %s pour %s", case_id, key)
        acknowledge([h["_id"] for h in items])  # d'abord : évite tout double rattachement
        call(KB, "POST", f"/api/cases/{case_id}/comments",
             {"type": "alert", "owner": "securitySolution",
              "alertId": [h["_id"] for h in items], "index": [h["_index"] for h in items],
              "rule": {"id": rule_uuid, "name": rule_name}})
        call(KB, "POST", f"/api/cases/{case_id}/comments",
             {"type": "user", "owner": "securitySolution", "comment": summary(items)})
        log.info("%d alerte(s) %s rattachée(s) au case %s", len(items), key, case_id)
        save_state(state)


if __name__ == "__main__":
    logging.basicConfig(filename=os.environ.get("SOC_IR_LOG", "/var/log/soc-ir.log"), level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    try:
        main()
    except Exception:
        log.exception("échec du cycle SOC-IR")
        raise
