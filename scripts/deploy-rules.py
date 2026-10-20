#!/usr/bin/env python3
"""Déploie les règles de détection versionnées dans detection/rules/ (Detection-as-Code).

Chaque fichier JSON est une règle Kibana Security identifiée par son rule_id :
mise à jour si elle existe déjà, création sinon. Le TLS est vérifié avec la CA interne.

usage (depuis la racine, .env chargé) :
  set -a; . ./.env; set +a
  ./scripts/deploy-rules.py              # toutes les règles
  ./scripts/deploy-rules.py --dry-run    # validation locale uniquement
"""
import argparse, glob, json, os, ssl, sys, urllib.error, urllib.request

REQUIRED = ("rule_id", "name", "description", "type", "query", "severity", "risk_score", "index")


def kibana():
    host = os.environ.get("ELK_HOST") or sys.exit("ELK_HOST non défini")
    key = os.environ.get("KIBANA_API_KEY") or sys.exit("KIBANA_API_KEY non défini")
    ca = os.path.join(os.environ.get("CERTS_DIR", "./certs/runtime"), "ca", "ca.crt")
    ctx = ssl.create_default_context(cafile=ca)
    url = os.environ.get("KIBANA_URL", f"https://{host}:5601")

    def call(method, path, body=None):
        req = urllib.request.Request(url + path, method=method,
                                     data=json.dumps(body).encode() if body is not None else None,
                                     headers={"Authorization": "ApiKey " + key, "kbn-xsrf": "deploy-rules",
                                              "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=30) as r:
                return r.status, json.loads(r.read() or b"{}")
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read() or b"{}")
    return call


def load(path):
    with open(path, encoding="utf-8") as f:
        rule = json.load(f)
    missing = [k for k in REQUIRED if k not in rule]
    if missing:
        raise ValueError(f"{path}: champs manquants {missing}")
    if rule["type"] == "threshold" and "threshold" not in rule:
        raise ValueError(f"{path}: règle threshold sans bloc 'threshold'")
    return rule


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="detection/rules")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    files = sorted(glob.glob(os.path.join(args.dir, "*.json")))
    rules = [load(f) for f in files]
    print(f"{len(rules)} règle(s) valide(s) dans {args.dir}")
    if args.dry_run:
        return 0

    call = kibana()
    failed = 0
    for rule in rules:
        rid = rule["rule_id"]
        code, _ = call("GET", f"/api/detection_engine/rules?rule_id={rid}")
        method, verb = ("PUT", "mise à jour") if code == 200 else ("POST", "création")
        code, res = call(method, "/api/detection_engine/rules", rule)
        ok = code == 200
        failed += not ok
        print(f"{'OK ' if ok else 'KO '} {verb:<12} {rid}" + ("" if ok else f" -> {res.get('message', res)}"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
