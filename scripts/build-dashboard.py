#!/usr/bin/env python3
"""Génère le dashboard « SOC Lab - Vue d'ensemble » (Kibana 8.11) : 3 data views, 20 visualisations Lens.

usage (depuis la racine, .env chargé) :
  ./scripts/build-dashboard.py                                 # import direct dans Kibana
  ./scripts/build-dashboard.py --out dashboards/soc-overview.ndjson   # export seul (aucun appel réseau)

L'export NDJSON peut aussi être importé à la main : Stack Management > Saved objects > Import.
"""
import argparse, json, os, ssl, sys, uuid, urllib.error, urllib.request

ap = argparse.ArgumentParser()
ap.add_argument("--out", help="écrit le NDJSON dans ce fichier au lieu de l'importer")
ARGS = ap.parse_args()

DV = {  # id: (title, name)
    "lab-dv-alerts": (".alerts-security.alerts-default", "Lab - Alertes sécurité"),
    "lab-dv-auth": ("logs-system.auth-*", "Lab - Logs d'authentification"),
    "lab-dv-metrics": ("metrics-system.*-*", "Lab - Métriques système"),
}

objects = []
for dv_id, (title, name) in DV.items():
    objects.append({"type": "index-pattern", "id": dv_id,
                    "attributes": {"title": title, "name": name, "timeFieldName": "@timestamp"},
                    "references": []})


# ---------- Lens column helpers ----------
def count(label="Nombre"):
    return {"label": label, "customLabel": True, "dataType": "number", "operationType": "count", "isBucketed": False,
            "scale": "ratio", "sourceField": "___records___", "params": {"emptyAsNull": False}}


def metric(op, field, label, pct=False):
    c = {"label": label, "customLabel": True, "dataType": "number", "operationType": op, "isBucketed": False,
         "scale": "ratio", "sourceField": field, "params": {"emptyAsNull": True}}
    if pct:
        c["params"]["format"] = {"id": "percent", "params": {"decimals": 1}}
    return c


def date_hist(label="@timestamp"):
    return {"label": label, "dataType": "date", "operationType": "date_histogram", "isBucketed": True,
            "scale": "interval", "sourceField": "@timestamp",
            "params": {"interval": "auto", "includeEmptyRows": True, "dropPartials": False}}


def terms(field, order_col, size=10, label=None, other=False, missing=False):
    return {"label": label or field, "customLabel": bool(label), "dataType": "ip" if field.endswith(".ip") else "string", "operationType": "terms", "isBucketed": True,
            "scale": "ordinal", "sourceField": field,
            "params": {"size": size, "orderBy": {"type": "column", "columnId": order_col},
                       "orderDirection": "desc", "otherBucket": other, "missingBucket": missing,
                       "parentFormat": {"id": "terms"}}}


def lens(title, vis_type, dv, columns, order, visualization, query=""):
    layer = "layer1"
    attrs = {"title": title, "description": "", "visualizationType": vis_type,
             "state": {"datasourceStates": {"formBased": {"layers": {layer: {
                 "columns": columns, "columnOrder": order, "incompleteColumns": {}, "sampling": 1}}}},
                 "visualization": visualization, "query": {"query": query, "language": "kuery"},
                 "filters": [], "internalReferences": [], "adHocDataViews": {}},
             }
    oid = "lab-lens-" + uuid.uuid5(uuid.NAMESPACE_URL, title).hex[:12]
    objects.append({"type": "lens", "id": oid, "attributes": attrs,
                    "references": [{"type": "index-pattern", "id": dv,
                                    "name": f"indexpattern-datasource-layer-{layer}"}]})
    return oid


L = "layer1"


def metric_vis(title, dv, col, query="", color=None, subtitle=""):
    vis = {"layerId": L, "layerType": "data", "metricAccessor": "m"}
    if color:
        vis["color"] = color
    if subtitle:
        vis["subtitle"] = subtitle
    return lens(title, "lnsMetric", dv, {"m": col}, ["m"], vis, query)


def xy(title, dv, series, cols, order, y, x="x", split=None, query="", palette=None, extra=None):
    layer = {"layerId": L, "layerType": "data", "seriesType": series, "xAccessor": x,
             "accessors": y, "position": "top", "showGridlines": False}
    if split:
        layer["splitAccessor"] = split
    if palette:
        layer["palette"] = {"type": "palette", "name": palette}
    vis = {"preferredSeriesType": series, "layers": [layer],
           "legend": {"isVisible": True, "position": "right"}, "valueLabels": "hide",
           "fittingFunction": "Linear", "axisTitlesVisibilitySettings": {"x": False, "yLeft": False, "yRight": True}}
    if extra:
        vis.update(extra)
    return lens(title, "lnsXY", dv, cols, order, vis, query)


def pie(title, dv, field, query="", size=10, shape="donut"):
    cols = {"g": terms(field, "m", size, other=True), "m": count()}
    vis = {"shape": shape, "layers": [{"layerId": L, "layerType": "data", "primaryGroups": ["g"],
                                       "metrics": ["m"], "numberDisplay": "percent", "categoryDisplay": "default",
                                       "legendDisplay": "show", "nestedLegend": False}]}
    return lens(title, "lnsPie", dv, cols, ["g", "m"], vis, query)


def table(title, dv, groups, query="", size=10, missing=False):
    cols, order = {}, []
    for i, (field, label) in enumerate(groups):
        cid = f"g{i}"
        cols[cid] = terms(field, "m", size, label, missing=missing)
        order.append(cid)
    cols["m"] = count("Événements")
    order.append("m")
    vis = {"layerId": L, "layerType": "data",
           "columns": [{"columnId": c} for c in order]}
    return lens(title, "lnsDatatable", dv, cols, order, vis, query)


# ---------- Queries ----------
SSH_FAIL = 'event.action:"ssh_login" and event.outcome:"failure"'
SSH_OK = 'event.action:"ssh_login" and event.outcome:"success"'
ACCOUNT = 'log.syslog.appname:("useradd" or "userdel" or "usermod" or "gpasswd" or "passwd")'
OPEN = 'kibana.alert.workflow_status:"open"'

# ---------- Visualisations ----------
A, AU, M = "lab-dv-alerts", "lab-dv-auth", "lab-dv-metrics"
p = {}
p["k_alerts"] = metric_vis("Alertes ouvertes", A, count("Alertes ouvertes"), OPEN, "#6092C0")
p["k_high"] = metric_vis("Alertes High / Critical", A, count("High / Critical"),
                         'kibana.alert.severity:("high" or "critical")', "#E7664C")
p["k_sshfail"] = metric_vis("Échecs SSH", AU, count("Échecs SSH"), SSH_FAIL, "#D6BF57")
p["k_sudo"] = metric_vis("Commandes sudo", AU, count("Commandes sudo"),
                         'log.syslog.appname:"sudo" and message:"COMMAND"', "#54B399")
p["k_hosts"] = metric_vis("Hôtes surveillés", M, metric("unique_count", "host.name", "Hôtes surveillés"),
                          "", "#9170B8")

p["alerts_time"] = xy("Alertes dans le temps par sévérité", A, "bar_stacked",
                      {"x": date_hist(), "s": terms("kibana.alert.severity", "y", 5, "Sévérité"), "y": count("Alertes")},
                      ["x", "s", "y"], ["y"], split="s", palette="status")
p["alerts_rule"] = pie("Alertes par règle", A, "kibana.alert.rule.name")
p["alerts_sev"] = pie("Répartition par sévérité", A, "kibana.alert.severity", shape="pie")
p["alerts_tbl"] = table("Alertes par règle, hôte et utilisateur", A,
                        [("kibana.alert.rule.name", "Règle"), ("kibana.alert.severity", "Sévérité"),
                         ("host.name", "Hôte"), ("user.name", "Utilisateur")], size=20, missing=True)
p["alerts_tactic"] = xy("Tactiques MITRE ATT&CK détectées", A, "bar_horizontal",
                        {"x": terms("kibana.alert.rule.threat.tactic.name", "y", 10, "Tactique"), "y": count("Alertes")},
                        ["x", "y"], ["y"])

p["ssh_time"] = xy("Connexions SSH : succès vs échecs", AU, "bar_stacked",
                   {"x": date_hist(), "s": terms("event.outcome", "y", 3, "Résultat"), "y": count("Connexions")},
                   ["x", "s", "y"], ["y"], split="s", query='event.action:"ssh_login"')
p["ssh_ip"] = table("Top IP sources (échecs SSH)", AU, [("source.ip", "IP source")], SSH_FAIL)
p["ssh_user"] = table("Comptes ciblés (échecs SSH)", AU, [("user.name", "Utilisateur")], SSH_FAIL)
p["ssh_ok"] = table("Connexions SSH réussies", AU,
                    [("user.name", "Utilisateur"), ("source.ip", "IP source"), ("host.name", "Hôte")], SSH_OK)
p["acct"] = table("Gestion des comptes (useradd / userdel / usermod)", AU,
                  [("log.syslog.appname", "Programme"), ("user.name", "Compte"), ("host.name", "Hôte")], ACCOUNT)
p["auth_prog"] = xy("Événements d'authentification par programme", AU, "bar_horizontal",
                    {"x": terms("log.syslog.appname", "y", 10, "Programme"), "y": count("Événements")},
                    ["x", "y"], ["y"])

p["cpu"] = xy("CPU utilisé (%) par hôte", M, "line",
              {"x": date_hist(), "s": terms("host.name", "y", 5, "Hôte"),
               "y": metric("average", "system.cpu.total.norm.pct", "CPU", True)},
              ["x", "s", "y"], ["y"], split="s", query='data_stream.dataset:"system.cpu"')
p["mem"] = xy("Mémoire utilisée (%) par hôte", M, "line",
              {"x": date_hist(), "s": terms("host.name", "y", 5, "Hôte"),
               "y": metric("average", "system.memory.actual.used.pct", "Mémoire", True)},
              ["x", "s", "y"], ["y"], split="s", query='data_stream.dataset:"system.memory"')
p["load"] = xy("Charge système (load 1 min)", M, "line",
               {"x": date_hist(), "s": terms("host.name", "y", 5, "Hôte"),
                "y": metric("average", "system.load.1", "Load 1m")},
               ["x", "s", "y"], ["y"], split="s", query='data_stream.dataset:"system.load"')
p["disk"] = xy("Disque utilisé (%) par hôte", M, "bar_horizontal",
               {"x": terms("host.name", "y", 5, "Hôte"),
                "y": metric("max", "system.filesystem.used.pct", "Disque", True)},
               ["x", "y"], ["y"], query='data_stream.dataset:"system.filesystem" and system.filesystem.mount_point:"/"')

# ---------- Dashboard layout (48-column grid) ----------
MD = ("## 🛡️ SOC Lab — Vue d'ensemble\n"
      "Surveillance de **Client-Lin01** et **ELK** : alertes de détection, activité SSH, élévation de privilèges, "
      "gestion des comptes et santé des machines.  \n"
      "➡️ Détails des alertes : **Security → Alerts** · Règles : **Security → Rules** (tag `SOC-Lab`)")
layout = [  # (key, x, y, w, h)
    ("md", 0, 0, 48, 5),
    ("k_alerts", 0, 5, 10, 7), ("k_high", 10, 5, 10, 7), ("k_sshfail", 20, 5, 10, 7),
    ("k_sudo", 30, 5, 9, 7), ("k_hosts", 39, 5, 9, 7),
    ("alerts_time", 0, 12, 30, 13), ("alerts_rule", 30, 12, 18, 13),
    ("alerts_tbl", 0, 25, 30, 13), ("alerts_sev", 30, 25, 9, 13), ("alerts_tactic", 39, 25, 9, 13),
    ("ssh_time", 0, 38, 24, 13), ("ssh_ip", 24, 38, 12, 13), ("ssh_user", 36, 38, 12, 13),
    ("ssh_ok", 0, 51, 16, 12), ("acct", 16, 51, 18, 12), ("auth_prog", 34, 51, 14, 12),
    ("cpu", 0, 63, 24, 12), ("mem", 24, 63, 24, 12),
    ("load", 0, 75, 30, 12), ("disk", 30, 75, 18, 12),
]
panels, refs = [], []
for i, (key, x, y, w, h) in enumerate(layout):
    pid = f"p{i}"
    grid = {"x": x, "y": y, "w": w, "h": h, "i": pid}
    if key == "md":
        panels.append({"type": "visualization", "gridData": grid, "panelIndex": pid, "embeddableConfig": {
            "savedVis": {"title": "", "description": "", "type": "markdown", "uiState": {},
                         "params": {"fontSize": 12, "openLinksInNewTab": False, "markdown": MD},
                         "data": {"aggs": [], "searchSource": {"query": {"query": "", "language": "kuery"},
                                                               "filter": []}}},
            "hidePanelTitles": True, "enhancements": {}}})
    else:
        ref = f"panel_{pid}"
        panels.append({"type": "lens", "gridData": grid, "panelIndex": pid,
                       "embeddableConfig": {"enhancements": {}}, "panelRefName": ref})
        refs.append({"type": "lens", "id": p[key], "name": f"{pid}:{ref}"})

objects.append({"type": "dashboard", "id": "lab-soc-dashboard", "references": refs, "attributes": {
    "title": "SOC Lab - Vue d'ensemble", "description": "Alertes, authentification et santé des hôtes du lab",
    "panelsJSON": json.dumps(panels), "timeRestore": True, "timeFrom": "now-24h", "timeTo": "now",
    "refreshInterval": {"pause": False, "value": 60000},
    "optionsJSON": json.dumps({"useMargins": True, "syncColors": True, "syncCursor": True,
                               "syncTooltips": True, "hidePanelTitles": False}),
    "kibanaSavedObjectMeta": {"searchSourceJSON": json.dumps({"query": {"query": "", "language": "kuery"},
                                                              "filter": []})}}})

# ---------- Export / import ----------
TMV = {"lens": "8.9.0", "dashboard": "8.9.0", "index-pattern": "8.0.0"}  # sans ça, Kibana rejoue d'anciennes migrations
for o in objects:
    o["coreMigrationVersion"] = "8.8.0"
    o["typeMigrationVersion"] = TMV[o["type"]]
ndjson = "\n".join(json.dumps(o, ensure_ascii=False) for o in objects) + "\n"

if ARGS.out:
    with open(ARGS.out, "w", encoding="utf-8", newline="\n") as f:
        f.write(ndjson)
    print(f"{len(objects)} objets écrits dans {ARGS.out}")
    sys.exit(0)

host = os.environ.get("ELK_HOST") or sys.exit("ELK_HOST non défini")
key = os.environ.get("KIBANA_API_KEY") or sys.exit("KIBANA_API_KEY non défini")
ctx = ssl.create_default_context(cafile=os.path.join(os.environ.get("CERTS_DIR", "./certs/runtime"), "ca", "ca.crt"))
url = os.environ.get("KIBANA_URL", f"https://{host}:5601")

boundary = "----soc" + uuid.uuid4().hex
body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"soc.ndjson\"\r\n"
        f"Content-Type: application/ndjson\r\n\r\n").encode() + ndjson.encode() + f"\r\n--{boundary}--\r\n".encode()
req = urllib.request.Request(url + "/api/saved_objects/_import?overwrite=true", data=body, method="POST",
                             headers={"Authorization": "ApiKey " + key, "kbn-xsrf": "build-dashboard",
                                      "Content-Type": f"multipart/form-data; boundary={boundary}"})
try:
    with urllib.request.urlopen(req, context=ctx, timeout=60) as r:
        res = json.loads(r.read())
except urllib.error.HTTPError as e:
    sys.exit(f"import refusé ({e.code}) : {e.read().decode()}")
print(f"import : success={res.get('success')} objets={res.get('successCount')}")
for err in res.get("errors") or []:
    print("erreur :", err.get("id"), err.get("error"))
sys.exit(0 if res.get("success") else 1)
