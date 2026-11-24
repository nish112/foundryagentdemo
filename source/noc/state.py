"""Local demo state: incidents, demo clock and audit trail.

Everything is stored in runs/state.json so an incident survives across turns
and across restarts of the script (the "ongoing" part of the coordinator).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
RUNS_DIR = ROOT / "runs"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _empty_state() -> dict[str, Any]:
    return {
        "incident_seq": 0,
        "incidents": {},
        "conversation_id": None,
        "audit": [],
    }


class DemoState:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or (RUNS_DIR / "state.json")
        self.data = _empty_state()
        if self.path.exists():
            self.data = json.loads(self.path.read_text(encoding="utf-8"))

    # ------------------------------------------------------------------ io
    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, indent=2), encoding="utf-8")

    def reset(self) -> None:
        self.data = _empty_state()
        self.save()

    # ----------------------------------------------------------- incidents
    @property
    def incidents(self) -> dict[str, dict[str, Any]]:
        return self.data["incidents"]

    def next_incident_id(self) -> str:
        self.data["incident_seq"] += 1
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
        return f"INC-NOC-{stamp}-{self.data['incident_seq']:03d}"

    def get_incident(self, incident_id: str) -> dict[str, Any]:
        if incident_id not in self.incidents:
            known = ", ".join(self.incidents) or "none"
            raise KeyError(f"Unknown incident_id '{incident_id}'. Known incidents: {known}")
        return self.incidents[incident_id]

    def open_incident_for_ring(self, ring: str) -> dict[str, Any] | None:
        for inc in self.incidents.values():
            if inc["transport_ring"] == ring and inc["status"] != "RESOLVED":
                return inc
        return None

    # ---------------------------------------------------------- demo clock
    def advance_clock(self, minutes: int) -> str:
        """Move the demo clock forward for every incident with an executed action."""
        moved = []
        for inc in self.incidents.values():
            if inc.get("action_executed"):
                inc["minutes_since_action"] = inc.get("minutes_since_action", 0) + minutes
                moved.append(f"{inc['incident_id']} now T+{inc['minutes_since_action']} min")
        self.save()
        if not moved:
            return "No executed recovery action yet, so the post-action clock has not started."
        return "; ".join(moved)

    # --------------------------------------------------------------- audit
    def audit(self, event: str, **details: Any) -> None:
        self.data["audit"].append({"at_utc": utc_now(), "event": event, **details})
        self.save()
