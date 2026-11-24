"""JSON schemas for the function tools (strict mode: every property required)."""
from __future__ import annotations

from typing import Any


def _obj(properties: dict[str, Any]) -> dict[str, Any]:
    return {"type": "object", "properties": properties,
            "required": list(properties), "additionalProperties": False}


FUNCTION_SCHEMAS: list[dict[str, Any]] = [
    {
        "name": "get_active_alarms",
        "description": "Read the live NOC alarm feed for the last N minutes, grouped by transport ring, "
                       "region, node and alarm type. Use this instead of trusting numbers typed by the user.",
        "parameters": _obj({"window_minutes": {"type": "integer",
                                               "description": "Look-back window, 1-120. Runbook correlation uses 15."}}),
    },
    {
        "name": "open_incident",
        "description": "Open ONE parent incident for correlated alarms on a transport ring (or return the "
                       "existing open incident for that ring). Severity is computed by the runbook rules.",
        "parameters": _obj({
            "transport_ring": {"type": "string", "description": "For example TR-7"},
            "regions": {"type": "array", "items": {"type": "string"}},
            "symptoms": {"type": "array", "items": {"type": "string"},
                         "description": "Alarm types correlated into this incident"},
            "enterprise_apn_impact": {"type": "boolean"},
            "summary": {"type": "string", "description": "One-sentence incident summary"},
        }),
    },
    {
        "name": "run_diagnostic_check",
        "description": "Run one runbook diagnostic check for an incident and return the evidence.",
        "parameters": _obj({
            "incident_id": {"type": "string"},
            "check": {"type": "string",
                      "enum": ["queue_depth", "gateway_restarts", "change_log", "kpi_baseline",
                               "standby_capacity"]},
        }),
    },
    {
        "name": "propose_network_action",
        "description": "Propose ONE approved catalog action for a diagnosed fault pattern as an emergency change. "
                       "Refuses if required diagnostics are missing, confidence is below 0.60, the action does not "
                       "match the pattern or its precondition, or another change is pending or still settling. "
                       "Does NOT execute anything.",
        "parameters": _obj({
            "incident_id": {"type": "string"},
            "action_id": {"type": "string",
                          "enum": ["ACT-REROUTE-TR5", "ACT-GW-RESTART", "ACT-QOS-ROLLBACK", "ACT-DNS-FAILOVER"]},
            "fault_pattern_id": {"type": "string",
                                 "enum": ["FP-TR7-2026", "FP-QOS-DRIFT", "FP-DNS-RESOLVER"]},
            "confidence": {"type": "number", "description": "0 to 1"},
            "evidence_summary": {"type": "string",
                                 "description": "Which diagnostic results and runbook passages support this"},
        }),
    },
    {
        "name": "execute_approved_action",
        "description": "Ask the human Incident Manager to approve a PENDING proposal as an emergency change and, only "
                       "if approved, execute it. Returns the emergency change record. The decision is made by a person, not by you.",
        "parameters": _obj({"incident_id": {"type": "string"}, "action_id": {"type": "string"}}),
    },
    {
        "name": "get_kpi_snapshot",
        "description": "Read current user-plane KPIs for an incident, with the peak and post-action history.",
        "parameters": _obj({"incident_id": {"type": "string"}}),
    },
    {
        "name": "verify_service_restore",
        "description": "Apply the three runbook recovery criteria to live KPIs and return SERVICE_RESTORED, "
                       "MONITORING or NOT_RESTORED with per-criterion evidence and next steps.",
        "parameters": _obj({"incident_id": {"type": "string"}}),
    },
    {
        "name": "publish_care_advisory",
        "description": "Publish (or update) the advisory for front-office care agents. customer_message must be plain "
                       "language with no internal node, ring or APN names. Call again at restoration to update it.",
        "parameters": _obj({
            "incident_id": {"type": "string"},
            "customer_message": {"type": "string"},
            "workaround_for_customers": {"type": "string",
                                         "description": "For example: switch to Wi-Fi where available, retry later"},
            "eta_minutes": {"type": "integer"},
        }),
    },
    {
        "name": "create_problem_record",
        "description": "After service is verified restored, raise the problem record (root cause, contributing factors, "
                       "permanent fix) required when the restoration was a workaround. Marks the incident RESOLVED.",
        "parameters": _obj({
            "incident_id": {"type": "string"},
            "root_cause": {"type": "string"},
            "contributing_factors": {"type": "array", "items": {"type": "string"}},
            "permanent_fix_proposal": {"type": "string"},
        }),
    },
    {
        "name": "get_incident_status",
        "description": "Return the stored record of an incident: status, diagnostics run, proposals, actions.",
        "parameters": _obj({"incident_id": {"type": "string"}}),
    },
]
