#!/usr/bin/env python3
"""Tests unitaires de response/soc-ir/soc-ir.py, sans Kibana ni réseau.

usage : python3 -m unittest discover -s tests/response -v   (depuis la racine)
"""
import importlib.util, os, tempfile, unittest
from unittest import mock

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
os.environ["SOC_IR_PLAYBOOKS"] = os.path.join(ROOT, "docs", "playbooks")
os.environ["SOC_IR_STATE"] = os.path.join(tempfile.mkdtemp(), "state.json")

spec = importlib.util.spec_from_file_location("soc_ir", os.path.join(ROOT, "response", "soc-ir", "soc-ir.py"))
soc_ir = importlib.util.module_from_spec(spec)
spec.loader.exec_module(soc_ir)


def alert(_id, rule_id, sev, host=None, ip=None, user=None, threshold_ip=None):
    src = {"@timestamp": f"2026-10-19T20:00:0{_id[-1]}Z", "kibana.alert.rule.rule_id": rule_id,
           "kibana.alert.rule.uuid": f"uuid-{rule_id}", "kibana.alert.rule.name": f"Règle {rule_id}",
           "kibana.alert.severity": sev}
    if host:
        src["host"] = {"name": host}
    if ip:
        src["source"] = {"ip": ip}
    if user:
        src["user"] = {"name": user}
    if threshold_ip:
        src["kibana.alert.threshold_result"] = {"terms": [{"field": "source.ip", "value": threshold_ip}]}
    return {"_id": _id, "_index": ".internal.alerts-security.alerts-default-000001", "_source": src}


class FieldAccess(unittest.TestCase):
    def test_flat_and_nested(self):
        doc = {"kibana.alert.rule.name": "x", "host": {"name": "h1"}, "kibana": {"alert": {"severity": "high"}}}
        self.assertEqual(soc_ir.get(doc, "kibana.alert.rule.name"), "x")
        self.assertEqual(soc_ir.get(doc, "host.name"), "h1")
        self.assertEqual(soc_ir.get(doc, "kibana.alert.severity"), "high")
        self.assertIsNone(soc_ir.get(doc, "user.name"))

    def test_subject_falls_back_to_threshold_ip(self):
        self.assertEqual(soc_ir.subject(alert("a1", "r", "high", host="client")["_source"]), "client")
        self.assertEqual(soc_ir.subject(alert("a2", "r", "high", threshold_ip="<IP_ATTAQUANT>")["_source"]),
                         "source <IP_ATTAQUANT>")
        self.assertEqual(soc_ir.subject(alert("a3", "r", "high")["_source"]), "inconnu")


class Playbooks(unittest.TestCase):
    def test_every_rule_has_a_playbook(self):
        rules = [f[:-5] for f in os.listdir(os.path.join(ROOT, "detection", "rules")) if f.endswith(".json")]
        for rule_id in rules:
            # sudo (sévérité low) n'ouvre pas de Case : pas de playbook dédié requis
            if rule_id == "lab-sudo-command":
                continue
            self.assertTrue(os.path.isfile(os.path.join(os.environ["SOC_IR_PLAYBOOKS"], f"{rule_id}.md")), rule_id)

    def test_unknown_rule_gets_default(self):
        self.assertIn("générique", soc_ir.playbook("regle-inconnue"))


class Workflow(unittest.TestCase):
    def test_one_case_per_rule_and_host_and_ack_before_attach(self):
        hits = [alert("a1", "lab-ssh-failed-login", "medium", host="client", ip="<IP_ATTAQUANT>", user="bob"),
                alert("a2", "lab-ssh-failed-login", "medium", host="client", ip="<IP_ATTAQUANT>", user="eve"),
                alert("a3", "lab-ssh-bruteforce", "high", threshold_ip="<IP_ATTAQUANT>")]
        calls = []

        def fake_call(base, method, path, body=None):
            calls.append((method, path, body))
            if path == "/api/cases":
                return {"id": f"case-{len(calls)}"}
            return {}

        with mock.patch.object(soc_ir, "fetch_alerts", return_value=hits), \
                mock.patch.object(soc_ir, "call", side_effect=fake_call):
            soc_ir.main()

        created = [b for m, p, b in calls if p == "/api/cases"]
        self.assertEqual(len(created), 2)
        self.assertIn("— client", created[0]["title"])
        self.assertIn("— source <IP_ATTAQUANT>", created[1]["title"])
        self.assertIn("Playbook", created[0]["description"])

        paths = [p for _, p, _ in calls]
        ack = paths.index("/api/detection_engine/signals/status")
        attach = next(i for i, (_, p, b) in enumerate(calls) if p.endswith("/comments") and b["type"] == "alert")
        self.assertLess(ack, attach, "les alertes doivent être acquittées avant d'être rattachées")

        summary = next(b for _, p, b in calls if p.endswith("/comments") and b["type"] == "user")["comment"]
        self.assertIn("`<IP_ATTAQUANT>`", summary)
        self.assertIn("`bob`", summary)


if __name__ == "__main__":
    unittest.main()
