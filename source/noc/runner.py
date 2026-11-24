"""Streams one user turn through the Foundry agent and runs the client-side tool loop.

Design notes: the agent (instructions + tools) lives in Foundry, so nothing is lost
between tool rounds; every round continues the same conversation; tool errors are
returned to the model instead of crashing the demo; approval is enforced in code.
"""
from __future__ import annotations

import json
from typing import Any

from .approval import Approver
from .tools import REQUIRES_APPROVAL, NocToolbox

MAX_TOOL_ROUNDS = 15


def _stream(openai_client: Any, request_kwargs: dict[str, Any], **kwargs: Any) -> Any:
    """Create a streamed response, print text deltas, return the final response object."""
    final = None
    printed = False
    stream = openai_client.responses.create(stream=True, **request_kwargs, **kwargs)
    for event in stream:
        etype = getattr(event, "type", "")
        if etype == "response.output_text.delta":
            print(event.delta, end="", flush=True)
            printed = True
        elif etype == "response.output_item.done":
            item = getattr(event, "item", None)
            if getattr(item, "type", "") == "file_search_call":
                queries = getattr(item, "queries", None) or []
                print(f"\n  [file_search] {'; '.join(queries)}", flush=True)
        elif etype in ("response.completed", "response.incomplete"):
            final = event.response
        elif etype in ("response.failed", "error"):
            resp = getattr(event, "response", None)
            err = getattr(resp, "error", None) or getattr(event, "message", None) or event
            raise RuntimeError(f"Agent response failed: {err}")
    if printed:
        print()
    if final is None:
        raise RuntimeError("Stream ended without a completed response.")
    return final


def _approval_context(toolbox: NocToolbox, args: dict[str, Any]) -> dict[str, Any]:
    try:
        inc = toolbox.state.get_incident(args.get("incident_id", ""))
    except KeyError:
        return {}
    for p in reversed(inc["proposals"]):
        if p["action_id"] == args.get("action_id"):
            return {"proposal": p}
    return {}


def run_turn(openai_client: Any, request_kwargs: dict[str, Any], conversation_id: str,
             user_text: str, toolbox: NocToolbox, approver: Approver) -> str:
    response = _stream(openai_client, request_kwargs, conversation=conversation_id, input=user_text)

    for _ in range(MAX_TOOL_ROUNDS):
        calls = [item for item in response.output if getattr(item, "type", "") == "function_call"]
        if not calls:
            return response.output_text or ""
        outputs = []
        for call in calls:
            try:
                args = json.loads(call.arguments or "{}")
            except json.JSONDecodeError as exc:
                result: dict[str, Any] = {"error": f"Arguments were not valid JSON: {exc}"}
            else:
                decision = None
                if call.name in REQUIRES_APPROVAL:
                    decision = approver(call.name, args, _approval_context(toolbox, args))
                result = toolbox.call(call.name, args, approval=decision)
            print(f"  [tool] {call.name}({call.arguments}) -> {_short(result)}", flush=True)
            outputs.append({"type": "function_call_output", "call_id": call.call_id,
                            "output": json.dumps(result)})
        response = _stream(openai_client, request_kwargs, conversation=conversation_id, input=outputs)
    return response.output_text or "(stopped: too many tool rounds)"


def _short(result: dict[str, Any], limit: int = 160) -> str:
    text = json.dumps(result)
    return text if len(text) <= limit else text[: limit - 3] + "..."
