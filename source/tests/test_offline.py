"""Offline tests: no Azure needed. Run with:  python -m unittest discover -s tests -v"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from noc.agent_definition import FUNCTION_SCHEMAS, function_tool_dicts  # noqa: E402
from noc.approval import fixed_approver  # noqa: E402
from noc.runner import run_turn  # noqa: E402
from noc.state import DemoState  # noqa: E402
from noc.tools import ApprovalDecision, NocToolbox  # noqa: E402

APPROVE = ApprovalDecision(True, "tester")


def fresh() -> NocToolbox:
    tmp = Path(tempfile.mkdtemp()) / "state.json"
    return NocToolbox(DemoState(tmp))


def open_tr7(tb: NocToolbox) -> str:
    r = tb.call("open_incident", {"transport_ring": "TR-7", "regions": ["Manila", "Cebu"],
                                  "symptoms": ["SGW_LATENCY", "PACKET_LOSS", "DNS_TIMEOUT"],
                                  "enterprise_apn_impact": True, "summary": "TR-7 storm"})
    return r["incident"]["incident_id"]


CHECKS = ("queue_depth", "gateway_restarts", "change_log", "kpi_baseline", "standby_capacity")


def diagnose(tb: NocToolbox, inc: str) -> None:
    for c in CHECKS:
        tb.call("run_diagnostic_check", {"incident_id": inc, "check": c})


def propose(tb, inc, action="ACT-REROUTE-TR5", pattern="FP-TR7-2026", conf=0.85):
    return tb.call("propose_network_action", {"incident_id": inc, "action_id": action,
                                              "fault_pattern_id": pattern, "confidence": conf,
                                              "evidence_summary": "queue 94%, TR-5 61% after move"})


def executed(tb) -> str:
    inc = open_tr7(tb); diagnose(tb, inc); propose(tb, inc)
    tb.call("execute_approved_action", {"incident_id": inc, "action_id": "ACT-REROUTE-TR5"},
            approval=APPROVE)
    return inc


class ToolTests(unittest.TestCase):
    def test_alarm_feed(self):
        r = fresh().call("get_active_alarms", {"window_minutes": 15})
        self.assertEqual(r["totals_by_ring"], {"TR-7": 183, "TR-2": 2})
        self.assertEqual(r["total_alarms"], 185)
        t = r["totals_by_type"]
        self.assertEqual((t["PACKET_LOSS"], t["DNS_TIMEOUT"], t["LINK_UTIL_HIGH"], t["QUEUE_DROP"]),
                         (35, 18, 4, 6))
        tr7_sgw = sum(g["count"] for g in r["groups"]
                      if g["transport_ring"] == "TR-7" and g["alarm_type"] == "SGW_LATENCY")
        self.assertEqual(tr7_sgw, 120)

    def test_severity_impact_and_required_actions(self):
        tb = fresh()
        inc = open_tr7(tb)
        rec = tb.state.get_incident(inc)
        self.assertEqual(rec["severity"], "SEV1")
        self.assertEqual(rec["impact"]["enterprise_sla_accounts_affected"], 46)
        again = tb.call("open_incident", {"transport_ring": "TR-7", "regions": ["Manila"],
                                          "symptoms": [], "enterprise_apn_impact": True, "summary": "x"})
        self.assertEqual(again["incident"]["incident_id"], inc)

    def test_action_blocked_without_standby_capacity(self):
        tb = fresh(); inc = open_tr7(tb)
        for c in ("queue_depth", "change_log"):
            tb.call("run_diagnostic_check", {"incident_id": inc, "check": c})
        r = propose(tb, inc)
        self.assertEqual(r["status"], "BLOCKED")
        self.assertIn("standby_capacity", r["reason"])

    def test_low_confidence_refused(self):
        tb = fresh(); inc = open_tr7(tb); diagnose(tb, inc)
        self.assertEqual(propose(tb, inc, conf=0.4)["status"], "INSUFFICIENT_CONFIDENCE")

    def test_action_must_match_pattern(self):
        tb = fresh(); inc = open_tr7(tb); diagnose(tb, inc)
        self.assertEqual(propose(tb, inc, action="ACT-QOS-ROLLBACK")["status"], "BLOCKED")
        self.assertEqual(propose(tb, inc, action="ACT-QOS-ROLLBACK", pattern="FP-QOS-DRIFT")
                         ["proposal"]["action_id"], "ACT-QOS-ROLLBACK")

    def test_restart_needs_reroute_first(self):
        tb = fresh(); inc = open_tr7(tb); diagnose(tb, inc)
        r = propose(tb, inc, action="ACT-GW-RESTART")
        self.assertEqual(r["status"], "BLOCKED")
        self.assertIn("ACT-REROUTE-TR5", r["reason"])

    def test_one_change_at_a_time(self):
        tb = fresh(); inc = open_tr7(tb); diagnose(tb, inc)
        propose(tb, inc)
        self.assertIn("pending", propose(tb, inc)["reason"])
        tb.call("execute_approved_action", {"incident_id": inc, "action_id": "ACT-REROUTE-TR5"},
                approval=APPROVE)
        tb.state.advance_clock(5)
        self.assertIn("Wait 10 minutes", propose(tb, inc, action="ACT-GW-RESTART")["reason"])

    def test_rejection_does_not_execute(self):
        tb = fresh(); inc = open_tr7(tb); diagnose(tb, inc); propose(tb, inc)
        r = tb.call("execute_approved_action", {"incident_id": inc, "action_id": "ACT-REROUTE-TR5"},
                    approval=ApprovalDecision(False, "tester", "wait for capacity confirmation"))
        self.assertEqual(r["status"], "REJECTED_BY_INCIDENT_MANAGER")
        self.assertEqual(tb.call("verify_service_restore", {"incident_id": inc})["restore_verdict"],
                         "NOT_RESTORED")

    def test_no_approval_object_means_rejected(self):
        tb = fresh(); inc = open_tr7(tb); diagnose(tb, inc); propose(tb, inc)
        r = tb.call("execute_approved_action", {"incident_id": inc, "action_id": "ACT-REROUTE-TR5"})
        self.assertEqual(r["status"], "REJECTED_BY_INCIDENT_MANAGER")

    def test_emergency_change_record(self):
        tb = fresh(); inc = open_tr7(tb); diagnose(tb, inc); propose(tb, inc)
        r = tb.call("execute_approved_action", {"incident_id": inc, "action_id": "ACT-REROUTE-TR5"},
                    approval=APPROVE)
        self.assertEqual(r["change_record"], "ECHG-00001")
        self.assertIn("TR-7", r["fail_back_plan"])

    def test_restore_timeline_applies_all_three_criteria(self):
        tb = fresh(); inc = executed(tb)
        expected = {0: "MONITORING", 5: "MONITORING", 10: "MONITORING", 15: "SERVICE_RESTORED"}
        last = 0
        for minute, verdict in expected.items():
            tb.state.advance_clock(minute - last); last = minute
            r = tb.call("verify_service_restore", {"incident_id": inc})
            self.assertEqual(r["restore_verdict"], verdict, f"T+{minute}: {r}")
        self.assertTrue(any("problem record" in s for s in r["next_steps"]))
        self.assertEqual(tb.state.get_incident(inc)["status"], "SERVICE_RESTORED")

    def test_v03_loophole_closed(self):
        tb = fresh(); inc = executed(tb)
        tb.state.advance_clock(5)
        r = tb.call("verify_service_restore", {"incident_id": inc})
        self.assertEqual(r["criteria"]["C1_latency_improvement"]["result"], "PASS")
        self.assertNotEqual(r["restore_verdict"], "SERVICE_RESTORED")

    def test_problem_record_only_after_restore(self):
        tb = fresh(); inc = executed(tb)
        args = {"incident_id": inc, "root_cause": "TR-7 peak saturation",
                "contributing_factors": ["CHG-88412", "+18% traffic"],
                "permanent_fix_proposal": "TR-7 capacity upgrade and QoS review"}
        self.assertEqual(tb.call("create_problem_record", args)["status"], "BLOCKED")
        tb.state.advance_clock(15)
        tb.call("verify_service_restore", {"incident_id": inc})
        r = tb.call("create_problem_record", args)
        self.assertEqual(r["problem_record"]["workarounds_in_place"], ["ACT-REROUTE-TR5"])
        self.assertEqual(tb.state.get_incident(inc)["status"], "RESOLVED")

    def test_bad_input_returns_error_not_crash(self):
        r = fresh().call("run_diagnostic_check", {"incident_id": "INC-NOPE", "check": "queue_depth"})
        self.assertIn("error", r)

    def test_care_advisory_rejects_internal_terms_and_versions(self):
        tb = fresh(); inc = open_tr7(tb)
        bad = tb.call("publish_care_advisory", {"incident_id": inc,
                                                "customer_message": "TR-7 congestion on SGW",
                                                "workaround_for_customers": "Wi-Fi", "eta_minutes": 30})
        self.assertEqual(bad["status"], "REJECTED")
        ok = {"incident_id": inc, "customer_message": "Some customers may see slow mobile data this evening.",
              "workaround_for_customers": "Use Wi-Fi where available", "eta_minutes": 30}
        self.assertEqual(tb.call("publish_care_advisory", ok)["version"], 1)
        self.assertEqual(tb.call("publish_care_advisory", ok)["version"], 2)

    def test_schemas_strict_and_complete(self):
        tb = fresh()
        self.assertEqual(sorted(s["name"] for s in FUNCTION_SCHEMAS), sorted(tb.names))
        for s in function_tool_dicts():
            props = s["parameters"]["properties"]
            self.assertEqual(sorted(s["parameters"]["required"]), sorted(props))
            self.assertFalse(s["parameters"]["additionalProperties"])


# ---------------------------------------------------------------- fake Foundry client
class FakeResponses:
    """Scripted model: returns function calls in sequence, then text."""

    def __init__(self, script):
        self.script = list(script)
        self.requests = []

    def create(self, stream=True, **kwargs):
        self.requests.append(kwargs)
        step = self.script.pop(0)
        if isinstance(step, str):
            output = [SimpleNamespace(type="message")]
            resp = SimpleNamespace(output=output, output_text=step)
            events = [SimpleNamespace(type="response.output_text.delta", delta=step)]
        else:
            output = [SimpleNamespace(type="function_call", name=n, arguments=json.dumps(a),
                                      call_id=f"call_{i}") for i, (n, a) in enumerate(step)]
            resp = SimpleNamespace(output=output, output_text="")
            events = []
        events.append(SimpleNamespace(type="response.completed", response=resp))
        return iter(events)


class RunnerTests(unittest.TestCase):
    def test_full_turn_with_approval_gate(self):
        tb = fresh()
        fake = FakeResponses([
            [("get_active_alarms", {"window_minutes": 15})],
            [("open_incident", {"transport_ring": "TR-7", "regions": ["Manila", "Cebu"],
                                "symptoms": ["SGW_LATENCY"], "enterprise_apn_impact": True,
                                "summary": "s"})],
            "Incident opened.",
        ])
        client = SimpleNamespace(responses=fake)
        out = run_turn(client, {}, "conv_1", "storm!", tb, fixed_approver(True))
        self.assertEqual(out, "Incident opened.")
        self.assertTrue(all(r["conversation"] == "conv_1" for r in fake.requests))
        self.assertEqual(fake.requests[1]["input"][0]["type"], "function_call_output")
        inc_id = next(iter(tb.state.incidents))

        # second turn: diagnostics + proposal + execution, rejected by the human
        diag = [("run_diagnostic_check", {"incident_id": inc_id, "check": c})
                for c in ("queue_depth", "change_log", "standby_capacity")]
        fake.script = [
            diag,
            [("propose_network_action", {"incident_id": inc_id, "action_id": "ACT-REROUTE-TR5",
                                         "fault_pattern_id": "FP-TR7-2026",
                                         "confidence": 0.85, "evidence_summary": "queue 94%"})],
            [("execute_approved_action", {"incident_id": inc_id, "action_id": "ACT-REROUTE-TR5"})],
            "Rejected; awaiting guidance.",
        ]
        run_turn(client, {}, "conv_1", "proceed", tb, fixed_approver(False))
        last_output = json.loads(fake.requests[-1]["input"][0]["output"])
        self.assertEqual(last_output["status"], "REJECTED_BY_INCIDENT_MANAGER")
        self.assertIsNone(tb.state.get_incident(inc_id)["action_executed"])

    def test_unknown_tool_and_bad_json_do_not_crash(self):
        tb = fresh()
        bad = SimpleNamespace(type="function_call", name="get_active_alarms", arguments="{oops",
                              call_id="c1")

        class Weird(FakeResponses):
            def create(self, stream=True, **kwargs):
                if not self.requests:
                    self.requests.append(kwargs)
                    resp = SimpleNamespace(output=[bad], output_text="")
                    return iter([SimpleNamespace(type="response.completed", response=resp)])
                return super().create(stream, **kwargs)

        fake = Weird(["ok"])
        out = run_turn(SimpleNamespace(responses=fake), {}, "c", "hi", tb, fixed_approver(True))
        self.assertEqual(out, "ok")
        self.assertIn("error", json.loads(fake.requests[-1]["input"][0]["output"]))


if __name__ == "__main__":
    unittest.main()
