"""AsterWave NOC incident coordinator - Foundry Agent Service demo (v0.4).

Usage:
  python noc_agent.py                       # interactive, new conversation
  python noc_agent.py --resume              # continue the last conversation and incident
  python noc_agent.py --auto-approve        # rehearsal: approve actions automatically
  python noc_agent.py --cleanup             # delete the agent version, conversation and local state

In-session commands:  /advance <minutes>   /status   /reset   /help   /exit
"""
from __future__ import annotations

import argparse
import json
import sys

from noc.approval import console_approver, fixed_approver
from noc.foundry import (AGENT_CACHE, agent_openai_client, ensure_agent, load_settings,
                         project_client)
from noc.runner import run_turn
from noc.state import DemoState
from noc.tools import NocToolbox

OPENING_PROMPT = (
    "AsterWave NOC, 19:05: alarm storm in the last 15 minutes across Manila and Cebu. Enterprise "
    "APN customers report severe mobile data degradation and consumers in Makati are complaining. "
    "Correlate the alarms into one incident, tell me the impact and severity, and what we must do now."
)

HELP = """Commands:
  /advance <minutes>  move the post-action demo clock forward (e.g. /advance 5)
  /status             show local incident state
  /reset              clear the incident and start a new conversation (keeps the agent)
  /exit               quit (the conversation is kept; use --resume to continue)"""


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="AsterWave NOC incident coordinator")
    p.add_argument("--prompt", default="", help="First message (otherwise asked interactively)")
    p.add_argument("--resume", action="store_true", help="Continue the last conversation")
    p.add_argument("--vector-store-id", default="", help="Override FOUNDRY_NOC_VECTOR_STORE_ID")
    p.add_argument("--new-version", action="store_true", help="Force a new agent version")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--auto-approve", action="store_true", help="Rehearsal: approve automatically")
    g.add_argument("--auto-reject", action="store_true", help="Rehearsal: reject automatically")
    p.add_argument("--cleanup", action="store_true", help="Delete agent version, conversation, state")
    return p.parse_args()


def cleanup(project, openai_client, state: DemoState) -> None:
    conv = state.data.get("conversation_id")
    if conv:
        try:
            openai_client.conversations.delete(conversation_id=conv)
            print(f"Deleted conversation {conv}")
        except Exception as exc:  # noqa: BLE001
            print(f"Could not delete conversation: {exc}")
    if AGENT_CACHE.exists():
        info = json.loads(AGENT_CACHE.read_text(encoding="utf-8"))
        try:
            project.agents.delete_version(agent_name=info["name"], agent_version=info["version"])
            print(f"Deleted agent {info['name']} v{info['version']}")
        except Exception as exc:  # noqa: BLE001
            print(f"Could not delete agent version: {exc}")
        AGENT_CACHE.unlink()
    state.reset()
    print("Local state cleared. The vector store is kept; delete it in the portal if no longer needed.")


def main() -> None:
    args = parse_args()
    settings = load_settings(args.vector_store_id, require_vector_store=not args.cleanup)
    state = DemoState()
    toolbox = NocToolbox(state)
    approver = (fixed_approver(True) if args.auto_approve
                else fixed_approver(False) if args.auto_reject else console_approver)

    with project_client(settings) as project:
        if args.cleanup:
            client = project.get_openai_client()
            cleanup(project, client, state)
            return

        agent = ensure_agent(project, settings, force_new=args.new_version)
        openai_client, request_kwargs = agent_openai_client(project, agent["name"])

        if args.resume and state.data.get("conversation_id"):
            conversation_id = state.data["conversation_id"]
            print(f"Resuming conversation {conversation_id}")
        else:
            conversation_id = openai_client.conversations.create().id
            state.data["conversation_id"] = conversation_id
            state.save()
            print(f"Started conversation {conversation_id}")
        print(HELP)

        first = args.prompt.strip()
        while True:
            if first:
                text, first = first, ""
                print(f"\n> {text}")
            else:
                try:
                    text = input("\n> ").strip()
                except (EOFError, KeyboardInterrupt):
                    print()
                    break
                if not text and not state.incidents:
                    text = OPENING_PROMPT
                    print(f"(using default scenario) {text}")
            if not text:
                continue
            if text in ("/exit", "/quit"):
                break
            if text == "/help":
                print(HELP)
                continue
            if text == "/status":
                print(json.dumps(state.incidents, indent=2) or "{}")
                continue
            if text == "/reset":
                # Clear local incidents AND start a new conversation, so the agent does not
                # remember an incident that the tools no longer know about.
                state.reset()
                conversation_id = openai_client.conversations.create().id
                state.data["conversation_id"] = conversation_id
                state.save()
                print(f"Incident state cleared. New conversation {conversation_id}")
                continue
            if text.startswith("/advance"):
                parts = text.split()
                minutes = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 5
                print(f"[demo clock] {state.advance_clock(minutes)}")
                continue
            try:
                run_turn(openai_client, request_kwargs, conversation_id, text, toolbox, approver)
            except Exception as exc:  # noqa: BLE001 - keep the live demo alive
                print(f"\n[error] {exc}\nThe conversation is intact; try again or rephrase.")

    print("Session ended. Run with --resume to continue this incident.")


if __name__ == "__main__":
    sys.exit(main())
