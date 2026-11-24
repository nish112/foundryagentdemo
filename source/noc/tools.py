"""Custom function tools for the NOC incident coordinator.

Operational rules implemented here (aligned with RB-NOC-014 v3.0):
* Tools read telemetry themselves; the model never supplies alarm or KPI numbers.
* Severity and impact come from the runbook rules and the service impact model.
* Actions come only from the approved catalog, must match the fault pattern and meet
  their precondition, and follow "one change at a time".
* Execution is an emergency change gated by a human Incident Manager decision made in
  application code, never by the model.
* Restoration uses all three runbook criteria; a workaround leads to a problem record.
"""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable

from .state import ROOT, DemoState, utc_now

TELEMETRY_DIR = ROOT / "data" / "telemetry"

MIN_CONFIDENCE = 0.60
LATENCY_IMPROVEMENT_PCT = 35.0      # C1
PACKET_LOSS_PCT_OF_PEAK = 20.0      # C2
PACKET_LOSS_DEADLINE_MIN = 10       # C2
CLEAN_DNS_WINDOWS = 2               # C3
CHANGE_SETTLE_MIN = 10              # one change at a time
SOAK_MINUTES = 30

DIAGNOSTIC_CHECKS = ["queue_depth", "gateway_restarts", "change_log", "kpi_baseline",
                     "standby_capacity"]
REQUIRED_BEFORE_ACTION = {"queue_depth", "change_log", "standby_capacity"}

ACTION_CATALOG: dict[str, dict[str, str]] = {
    "ACT-REROUTE-TR5": {
        "fault_pattern_id": "FP-TR7-2026",
        "action": "Move enterprise APN VRF traffic from TR-7 to TR-5 by traffic-engineering policy (no session drop)",
        "risk": "Medium", "type": "workaround",
        "fail_back": "Move enterprise APN VRF back to TR-7 as a planned change off-peak, after the TR-7 capacity/QoS fix",
    },
    "ACT-GW-RESTART": {
        "fault_pattern_id": "FP-TR7-2026",
        "action": "Controlled restart of the affected gateway user-plane process (drops active sessions on that process)",
        "risk": "High", "type": "escalation",
        "fail_back": "Not applicable (restart). Monitor session re-attach rate for 15 minutes",
    },
    "ACT-QOS-ROLLBACK": {
        "fault_pattern_id": "FP-QOS-DRIFT",
        "action": "Roll back the most recent QoS / shaping profile change on the affected ring",
        "risk": "Low", "type": "fix",
        "fail_back": "Re-apply the change only after CAB review",
    },
    "ACT-DNS-FAILOVER": {
        "fault_pattern_id": "FP-DNS-RESOLVER",
        "action": "Flush resolver cache and shift 50% of queries to the peer resolver",
        "risk": "Low", "type": "workaround",
        "fail_back": "Return resolver load share to 100% once CPU is below 70% for 30 minutes",
    },
}

# Tools whose execution must be approved by a human in application code.
REQUIRES_APPROVAL = {"execute_approved_action"}


class ApprovalDecision:
    def __init__(self, approved: bool, approver: str, note: str = "",
                 role: str = "Incident Manager") -> None:
        self.approved = approved
        self.approver = approver
        self.note = note
        self.role = role


def _load_alarms() -> list[dict[str, Any]]:
    with (TELEMETRY_DIR / "alarms.csv").open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    for row in rows:
        row["minutes_ago"] = int(row["minutes_ago"])
        row["count"] = int(row["count"])
    return rows


def _load_kpi_timeline() -> list[dict[str, int]]:
    with (TELEMETRY_DIR / "kpi_timeline.csv").open(encoding="utf-8") as fh:
        return [{k: int(v) for k, v in row.items()} for row in csv.DictReader(fh)]


def _load_json(name: str) -> dict[str, Any]:
    return json.loads((TELEMETRY_DIR / name).read_text(encoding="utf-8"))


TRANSPORT_ALARMS = {"LINK_UTIL_HIGH", "QUEUE_DROP"}


class NocToolbox:
    def __init__(self, state: DemoState) -> None:
        self.state = state
        self._impls: dict[str, Callable[..., dict[str, Any]]] = {
            "get_active_alarms": self.get_active_alarms,
            "open_incident": self.open_incident,
            "run_diagnostic_check": self.run_diagnostic_check,
            "propose_network_action": self.propose_network_action,
            "execute_approved_action": self.execute_approved_action,
            "get_kpi_snapshot": self.get_kpi_snapshot,
            "verify_service_restore": self.verify_service_restore,
            "publish_care_advisory": self.publish_care_advisory,
            "create_problem_record": self.create_problem_record,
            "get_incident_status": self.get_incident_status,
        }

    @property
    def names(self) -> list[str]:
        return list(self._impls)

    def call(self, name: str, arguments: dict[str, Any],
             approval: ApprovalDecision | None = None) -> dict[str, Any]:
        """Run a tool and always return a JSON-safe dict (errors included)."""
        if name not in self._impls:
            return {"error": f"Unknown tool '{name}'"}
        try:
            if name in REQUIRES_APPROVAL:
                return self._impls[name](**arguments, approval=approval)
            return self._impls[name](**arguments)
        except (KeyError, ValueError, TypeError) as exc:
            self.state.audit("tool_error", tool=name, error=str(exc))
            return {"error": str(exc)}

    # ------------------------------------------------------------- alarms
    def get_active_alarms(self, window_minutes: int) -> dict[str, Any]:
        if window_minutes <= 0 or window_minutes > 120:
            raise ValueError("window_minutes must be between 1 and 120")
        rows = [r for r in _load_alarms() if r["minutes_ago"] <= window_minutes]
        groups: dict[tuple, dict[str, Any]] = {}
        for r in rows:
            key = (r["transport_ring"], r["region"], r["node"], r["alarm_type"])
            g = groups.setdefault(key, {
                "transport_ring": r["transport_ring"], "region": r["region"],
                "node": r["node"], "alarm_type": r["alarm_type"],
                "alarm_class": "transport (probable cause)" if r["alarm_type"] in TRANSPORT_ALARMS
                               else "service (symptom)",
                "count": 0, "first_seen_minutes_ago": r["minutes_ago"],
                "enterprise_apn_impact": r["enterprise_apn_impact"] == "yes",
            })
            g["count"] += r["count"]
            g["first_seen_minutes_ago"] = max(g["first_seen_minutes_ago"], r["minutes_ago"])
        totals: dict[str, int] = defaultdict(int)
        by_ring: dict[str, int] = defaultdict(int)
        for g in groups.values():
            totals[g["alarm_type"]] += g["count"]
            by_ring[g["transport_ring"]] += g["count"]
        return {
            "window_minutes": window_minutes,
            "total_alarms": sum(totals.values()),
            "totals_by_ring": dict(by_ring),
            "totals_by_type": dict(totals),
            "groups": sorted(groups.values(), key=lambda g: (g["transport_ring"], -g["count"])),
            "source": "NOC fault management feed (synthetic sample)",
        }

    # ----------------------------------------------------------- incident
    def open_incident(self, transport_ring: str, regions: list[str], symptoms: list[str],
                      enterprise_apn_impact: bool, summary: str) -> dict[str, Any]:
        existing = self.state.open_incident_for_ring(transport_ring)
        if existing:
            return {"note": "An open incident already exists for this ring; reuse it.",
                    "incident": existing}
        impact = _load_json("impact.json").get(transport_ring, {})
        sla_accounts = impact.get("enterprise_sla_accounts_affected", 0)
        if enterprise_apn_impact and (len(set(regions)) > 1 or sla_accounts > 10):
            severity = "SEV1"
        elif enterprise_apn_impact or len(set(regions)) > 1:
            severity = "SEV2"
        else:
            severity = "SEV3"
        incident_id = self.state.next_incident_id()
        inc = {
            "incident_id": incident_id, "opened_at_utc": utc_now(), "status": "INVESTIGATING",
            "severity": severity, "transport_ring": transport_ring, "regions": sorted(set(regions)),
            "symptoms": symptoms, "enterprise_apn_impact": enterprise_apn_impact,
            "summary": summary, "impact": impact, "diagnostics_run": [], "proposals": [],
            "actions_executed": [], "action_executed": None, "minutes_since_action": 0,
            "care_advisories": [], "problem_record": None,
        }
        self.state.incidents[incident_id] = inc
        self.state.audit("incident_opened", incident_id=incident_id, severity=severity)
        required = []
        if severity in ("SEV1", "SEV2"):
            required = ["Assign an Incident Manager within 5 minutes and open the bridge (Runbook §2)"]
        if severity == "SEV1":
            required += ["Bridge status update every 30 minutes (Runbook §6)",
                         "Notify key account management for enterprise SLA accounts within 30 minutes (Runbook §6)"]
        return {"incident": inc, "severity_rule": "Runbook §2", "required_now": required}

    # -------------------------------------------------------- diagnostics
    def run_diagnostic_check(self, incident_id: str, check: str) -> dict[str, Any]:
        inc = self.state.get_incident(incident_id)
        if check not in DIAGNOSTIC_CHECKS:
            raise ValueError(f"check must be one of {DIAGNOSTIC_CHECKS}")
        result = _load_json("diagnostics.json")[check]
        if check not in inc["diagnostics_run"]:
            inc["diagnostics_run"].append(check)
        self.state.audit("diagnostic_run", incident_id=incident_id, check=check)
        return {"incident_id": incident_id, "check": check, "result": result,
                "checks_completed": inc["diagnostics_run"],
                "checks_remaining": [c for c in DIAGNOSTIC_CHECKS if c not in inc["diagnostics_run"]]}

    # ------------------------------------------------------------- action
    def propose_network_action(self, incident_id: str, action_id: str, fault_pattern_id: str,
                               confidence: float, evidence_summary: str) -> dict[str, Any]:
        inc = self.state.get_incident(incident_id)
        if not 0 <= confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        if action_id not in ACTION_CATALOG:
            raise ValueError(f"action_id must be one of {sorted(ACTION_CATALOG)}")
        entry = ACTION_CATALOG[action_id]
        missing = REQUIRED_BEFORE_ACTION - set(inc["diagnostics_run"])
        if missing:
            return {"status": "BLOCKED",
                    "reason": f"Runbook §3 requires these checks first: {sorted(missing)}"}
        if confidence < MIN_CONFIDENCE:
            return {"status": "INSUFFICIENT_CONFIDENCE",
                    "reason": f"Confidence {confidence:.2f} is below {MIN_CONFIDENCE:.2f}. "
                              "Continue diagnostics; do not propose an action yet (Runbook §3)."}
        if entry["fault_pattern_id"] != fault_pattern_id:
            return {"status": "BLOCKED",
                    "reason": f"{action_id} is approved only for {entry['fault_pattern_id']}, "
                              f"not {fault_pattern_id} (Action Catalog)."}
        if any(p["status"] == "PENDING_APPROVAL" for p in inc["proposals"]):
            return {"status": "BLOCKED",
                    "reason": "Another action is pending approval. One change at a time (Runbook §4)."}
        last = inc.get("action_executed")
        if last and inc.get("minutes_since_action", 0) < CHANGE_SETTLE_MIN:
            return {"status": "BLOCKED",
                    "reason": f"{last['action_id']} was executed {inc.get('minutes_since_action', 0)} min ago. "
                              f"Wait {CHANGE_SETTLE_MIN} minutes to measure its effect (Runbook §4)."}
        if action_id == "ACT-GW-RESTART":
            rerouted = any(a["action_id"] == "ACT-REROUTE-TR5" for a in inc["actions_executed"])
            if not rerouted:
                return {"status": "BLOCKED",
                        "reason": "Precondition: ACT-REROUTE-TR5 must be executed first (Action Catalog)."}
            if inc["status"] in ("SERVICE_RESTORED", "RESOLVED"):
                return {"status": "BLOCKED", "reason": "Service is restored; a restart is not justified."}
        proposal = {
            "action_id": action_id, "action": entry["action"], "risk": entry["risk"],
            "action_type": entry["type"], "fail_back_plan": entry["fail_back"],
            "fault_pattern_id": fault_pattern_id, "confidence": round(confidence, 2),
            "evidence_summary": evidence_summary, "status": "PENDING_APPROVAL",
            "proposed_at_utc": utc_now(),
        }
        inc["proposals"].append(proposal)
        inc["status"] = "AWAITING_APPROVAL"
        self.state.audit("action_proposed", incident_id=incident_id, action_id=action_id)
        return {"incident_id": incident_id, "proposal": proposal,
                "change_type": "Emergency change (Runbook §4)",
                "next_step": "Call execute_approved_action; the Incident Manager will be asked to approve."}

    def execute_approved_action(self, incident_id: str, action_id: str,
                                approval: ApprovalDecision | None = None) -> dict[str, Any]:
        inc = self.state.get_incident(incident_id)
        pending = [p for p in inc["proposals"]
                   if p["action_id"] == action_id and p["status"] == "PENDING_APPROVAL"]
        if not pending:
            return {"status": "NOT_EXECUTED",
                    "reason": f"No pending proposal {action_id} for {incident_id}. "
                              "Call propose_network_action first."}
        proposal = pending[-1]
        if approval is None or not approval.approved:
            proposal["status"] = "REJECTED"
            inc["status"] = "INVESTIGATING"
            who = approval.approver if approval else "no approver"
            note = approval.note if approval else ""
            self.state.audit("action_rejected", incident_id=incident_id,
                             action_id=action_id, approver=who, note=note)
            return {"status": "REJECTED_BY_INCIDENT_MANAGER", "approver": who, "note": note,
                    "instruction": "Do not execute. Ask the Incident Manager how to proceed."}
        self.state.data["change_seq"] = self.state.data.get("change_seq", 0) + 1
        change_id = f"ECHG-{self.state.data['change_seq']:05d}"
        record = {"action_id": action_id, "change_record": change_id,
                  "executed_at_utc": utc_now(), "approved_by": approval.approver,
                  "approver_role": approval.role}
        proposal["status"] = "EXECUTED"
        proposal["change_record"] = change_id
        inc["actions_executed"].append(record)
        inc["action_executed"] = record
        inc["minutes_since_action"] = 0
        inc["status"] = "MITIGATING"
        self.state.audit("action_executed", incident_id=incident_id, action_id=action_id,
                         change_record=change_id, approver=approval.approver, role=approval.role)
        return {"status": "EXECUTED", "action_id": action_id, "change_record": change_id,
                "approved_by": f"{approval.approver} ({approval.role})",
                "fail_back_plan": proposal["fail_back_plan"],
                "cab_review": "Retrospective CAB review within 2 working days (Runbook §4)",
                "note": "Simulated execution. Post-action KPIs appear as the demo clock advances."}

    # --------------------------------------------------------- KPIs/verify
    def _kpis_so_far(self, inc: dict[str, Any]) -> list[dict[str, int]]:
        timeline = _load_kpi_timeline()
        if not inc.get("action_executed"):
            return [timeline[0]]
        elapsed = inc.get("minutes_since_action", 0)
        return [r for r in timeline if r["minutes_after_action"] <= elapsed]

    def get_kpi_snapshot(self, incident_id: str) -> dict[str, Any]:
        inc = self.state.get_incident(incident_id)
        rows = self._kpis_so_far(inc)
        peak = _load_kpi_timeline()[0]
        return {
            "incident_id": incident_id,
            "action_executed": bool(inc.get("action_executed")),
            "minutes_since_action": inc.get("minutes_since_action", 0) if inc.get("action_executed") else None,
            "peak": peak, "current": rows[-1], "history": rows,
            "source": "Performance management KPI feed (synthetic sample)",
        }

    def verify_service_restore(self, incident_id: str) -> dict[str, Any]:
        inc = self.state.get_incident(incident_id)
        peak = _load_kpi_timeline()[0]
        if not inc.get("action_executed"):
            return {"incident_id": incident_id, "restore_verdict": "NOT_RESTORED",
                    "reason": "No approved recovery action has been executed yet.",
                    "checked_at_utc": utc_now()}
        rows = self._kpis_so_far(inc)
        elapsed = inc.get("minutes_since_action", 0)
        current = rows[-1]

        improvement = (peak["user_plane_latency_ms"] - current["user_plane_latency_ms"]) \
            / peak["user_plane_latency_ms"] * 100
        c1 = "PASS" if improvement >= LATENCY_IMPROVEMENT_PCT else "PENDING"

        limit = peak["packet_loss_alarms"] * PACKET_LOSS_PCT_OF_PEAK / 100
        in_deadline = [r for r in rows if 0 < r["minutes_after_action"] <= PACKET_LOSS_DEADLINE_MIN]
        if any(r["packet_loss_alarms"] < limit for r in in_deadline):
            c2 = "PASS"
        elif elapsed < PACKET_LOSS_DEADLINE_MIN:
            c2 = "PENDING"
        else:
            c2 = "FAIL"

        streak = 0
        for r in rows:
            if r["minutes_after_action"] == 0:
                continue
            streak = streak + 1 if r["dns_timeout_bursts"] == 0 else 0
        c3 = "PASS" if streak >= CLEAN_DNS_WINDOWS else "PENDING"

        criteria = {
            "C1_latency_improvement": {"result": c1, "value_pct": round(improvement, 1),
                                       "threshold_pct": LATENCY_IMPROVEMENT_PCT,
                                       "current_ms": current["user_plane_latency_ms"],
                                       "peak_ms": peak["user_plane_latency_ms"]},
            "C2_packet_loss_below_20pct_of_peak_in_10min": {
                "result": c2, "current_alarms": current["packet_loss_alarms"],
                "limit": limit, "peak": peak["packet_loss_alarms"]},
            "C3_two_clean_dns_windows": {"result": c3, "consecutive_clean_windows": streak,
                                         "required": CLEAN_DNS_WINDOWS},
        }
        results = [c1, c2, c3]
        next_steps: list[str] = []
        if "FAIL" in results:
            verdict = "NOT_RESTORED"
            inc["status"] = "ESCALATE"
            next_steps = ["Escalate per Action Catalog (consider ACT-GW-RESTART if queues have not drained)"]
        elif all(r == "PASS" for r in results):
            verdict = "SERVICE_RESTORED"
            if inc["status"] != "RESOLVED":
                inc["status"] = "SERVICE_RESTORED"
            last = inc["action_executed"]
            workaround = ACTION_CATALOG[last["action_id"]]["type"] == "workaround"
            next_steps = [f"Keep the incident open for a {SOAK_MINUTES}-minute soak period (Runbook §5)",
                          "Update the care advisory to say service is restored (Runbook §6)"]
            if workaround:
                next_steps += ["Restoration was a WORKAROUND: raise a problem record before closure (Runbook §7)",
                               f"Fail-back plan: {ACTION_CATALOG[last['action_id']]['fail_back']}"]
            if inc["severity"] == "SEV1":
                next_steps.append("Schedule the post-incident review within 5 working days (Runbook §7)")
        else:
            verdict = "MONITORING"
            inc["status"] = "MONITORING"
            next_steps = ["Recheck after the next 5-minute window"]
        self.state.audit("restore_verified", incident_id=incident_id, verdict=verdict,
                         minutes_since_action=elapsed)
        return {"incident_id": incident_id, "restore_verdict": verdict,
                "minutes_since_action": elapsed, "criteria": criteria,
                "rule": "Runbook §5 (all three criteria must pass)",
                "next_steps": next_steps, "checked_at_utc": utc_now()}

    # ------------------------------------------------------- care hand-off
    def publish_care_advisory(self, incident_id: str, customer_message: str,
                              workaround_for_customers: str, eta_minutes: int) -> dict[str, Any]:
        inc = self.state.get_incident(incident_id)
        banned = [w for w in ("TR-", "SGW", "PGW", "PE-", "DNS-", "VRF", "APN")
                  if w.lower() in customer_message.lower()]
        if banned:
            return {"status": "REJECTED",
                    "reason": f"Customer wording contains internal terms {banned}. Rewrite in plain language (Runbook §6)."}
        impact = inc.get("impact", {})
        areas = impact.get("consumer_areas_affected", []) + impact.get("enterprise_areas_affected", [])
        version = len(inc["care_advisories"]) + 1
        outbox = self.state.path.parent / "outbox"
        outbox.mkdir(parents=True, exist_ok=True)
        path = outbox / f"care_advisory_{incident_id}_v{version}.md"
        path.write_text(
            f"## Care advisory {incident_id} (update {version})\n"
            f"- Network status: {inc['status']}\n"
            f"- Severity: {inc['severity']}\n"
            f"- Affected areas: {', '.join(areas) or ', '.join(inc['regions'])}\n"
            f"- Affected customers: enterprise mobile data users and consumer mobile data users in the areas above\n"
            f"- What to tell customers: {customer_message}\n"
            f"- Customer workaround: {workaround_for_customers}\n"
            f"- Estimated time to stabilise: {eta_minutes} minutes\n"
            f"- Retention guidance: do not offer compensation for this incident until the Incident Manager confirms impact duration\n"
            f"- External wording owner: Incident Manager\n"
            f"- Published (UTC): {utc_now()}\n",
            encoding="utf-8",
        )
        inc["care_advisories"].append({"version": version, "file": path.name, "at_utc": utc_now()})
        self.state.audit("care_advisory_published", incident_id=incident_id, version=version)
        return {"status": "PUBLISHED", "file": path.name, "version": version,
                "consumer": "Front-office care agents (current incidents feed)"}

    # -------------------------------------------------- problem management
    def create_problem_record(self, incident_id: str, root_cause: str,
                              contributing_factors: list[str], permanent_fix_proposal: str) -> dict[str, Any]:
        inc = self.state.get_incident(incident_id)
        if inc["status"] not in ("SERVICE_RESTORED", "RESOLVED"):
            return {"status": "BLOCKED",
                    "reason": "Service is not yet verified as restored. Run verify_service_restore first."}
        if inc.get("problem_record"):
            return {"status": "EXISTS", "problem_record": inc["problem_record"]}
        self.state.data["problem_seq"] = self.state.data.get("problem_seq", 0) + 1
        prb = {
            "problem_id": f"PRB-{self.state.data['problem_seq']:05d}",
            "linked_incident": incident_id, "root_cause": root_cause,
            "contributing_factors": contributing_factors,
            "permanent_fix_proposal": permanent_fix_proposal,
            "workarounds_in_place": [a["action_id"] for a in inc["actions_executed"]
                                     if ACTION_CATALOG[a["action_id"]]["type"] == "workaround"],
            "pir_due": "Within 5 working days" if inc["severity"] == "SEV1" else "Not required",
            "created_at_utc": utc_now(),
        }
        inc["problem_record"] = prb
        inc["status"] = "RESOLVED"
        self.state.audit("problem_record_created", incident_id=incident_id, problem_id=prb["problem_id"])
        return {"status": "CREATED", "problem_record": prb,
                "incident_status": "RESOLVED (close after the soak period and PIR scheduling)"}

    def get_incident_status(self, incident_id: str) -> dict[str, Any]:
        return {"incident": self.state.get_incident(incident_id)}
