"""Human-in-the-loop approval gate. The decision is made here, in code, by a person."""
from __future__ import annotations

import getpass
from typing import Any, Callable

from .tools import ApprovalDecision

Approver = Callable[[str, dict[str, Any], dict[str, Any]], ApprovalDecision]


def console_approver(tool_name: str, args: dict[str, Any], context: dict[str, Any]) -> ApprovalDecision:
    proposal = context.get("proposal") or {}
    print("\n" + "=" * 70)
    print(" EMERGENCY CHANGE - Incident Manager approval required (Runbook §4)")
    print("=" * 70)
    print(f" Incident : {args.get('incident_id')}")
    print(f" Action   : {args.get('action_id')}")
    if proposal:
        print(f" Detail   : {proposal.get('action')}")
        print(f" Pattern  : {proposal.get('fault_pattern_id')}  confidence={proposal.get('confidence')}"
              f"  risk={proposal.get('risk')}")
        print(f" Evidence : {proposal.get('evidence_summary')}")
        print(f" Fail-back: {proposal.get('fail_back_plan')}")
    print("=" * 70)
    try:
        default_who = getpass.getuser()
    except Exception:  # pragma: no cover
        default_who = "incident-manager"
    who = input(f" Approver name [{default_who}]: ").strip() or default_who
    answer = input(" Approve this emergency change? [y/N]: ").strip().lower()
    note = input(" Reason / note for the change record (optional): ").strip()
    return ApprovalDecision(approved=answer in {"y", "yes"}, approver=who, note=note,
                            role="Incident Manager")


def fixed_approver(approved: bool, approver: str = "rehearsal-mode") -> Approver:
    def _decide(tool_name: str, args: dict[str, Any], context: dict[str, Any]) -> ApprovalDecision:
        verdict = "APPROVED" if approved else "REJECTED"
        print(f"\n[approval] {verdict} automatically ({approver}) for {args.get('action_id')}")
        return ApprovalDecision(approved=approved, approver=approver, note="automatic (rehearsal)",
                                role="Incident Manager (rehearsal)")
    return _decide
