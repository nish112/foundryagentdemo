"""Foundry project connection, agent versioning and the agent-bound OpenAI client."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

from .agent_definition import AGENT_DESCRIPTION, build_definition, definition_fingerprint
from .state import ROOT, RUNS_DIR

AGENT_CACHE = RUNS_DIR / "agent_version.json"


@dataclass
class Settings:
    endpoint: str
    model: str
    agent_name: str
    vector_store_id: str


def load_settings(vector_store_override: str = "", require_vector_store: bool = True) -> Settings:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
    endpoint = os.getenv("FOUNDRY_PROJECT_ENDPOINT", "").strip()
    model = os.getenv("FOUNDRY_MODEL_NAME", "").strip()
    agent_name = os.getenv("FOUNDRY_NOC_AGENT_NAME", "asterwave-noc-coordinator").strip()
    vs = (vector_store_override or os.getenv("FOUNDRY_NOC_VECTOR_STORE_ID", "")).strip()
    missing = [n for n, v in (("FOUNDRY_PROJECT_ENDPOINT", endpoint),
                              ("FOUNDRY_MODEL_NAME", model)) if not v]
    if require_vector_store and not vs:
        missing.append("FOUNDRY_NOC_VECTOR_STORE_ID (run: python setup_knowledge.py)")
    if missing:
        raise SystemExit(f"Missing settings in {ROOT / '.env'}: {', '.join(missing)}")
    return Settings(endpoint, model, agent_name, vs)


def project_client(settings: Settings):
    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential

    return AIProjectClient(endpoint=settings.endpoint, credential=DefaultAzureCredential())


def ensure_agent(project: Any, settings: Settings, force_new: bool = False) -> dict[str, str]:
    """Create a new agent version only when the definition changed (keeps the project tidy)."""
    fingerprint = definition_fingerprint(settings.model, settings.vector_store_id)
    if AGENT_CACHE.exists() and not force_new:
        cached = json.loads(AGENT_CACHE.read_text(encoding="utf-8"))
        if cached.get("name") == settings.agent_name and cached.get("fingerprint") == fingerprint:
            print(f"Using agent {cached['name']} v{cached['version']} (definition unchanged)")
            return cached
    agent = project.agents.create_version(
        agent_name=settings.agent_name,
        definition=build_definition(settings.model, settings.vector_store_id),
        description=AGENT_DESCRIPTION,
    )
    info = {"name": agent.name, "version": str(agent.version), "fingerprint": fingerprint}
    AGENT_CACHE.parent.mkdir(parents=True, exist_ok=True)
    AGENT_CACHE.write_text(json.dumps(info, indent=2), encoding="utf-8")
    print(f"Created agent {agent.name} v{agent.version} in Foundry")
    return info


def agent_openai_client(project: Any, agent_name: str) -> tuple[Any, dict[str, Any]]:
    """Return (openai_client, extra request kwargs) bound to the Foundry agent.

    Newer azure-ai-projects releases bind the agent on the client; older 2.x releases
    need the agent reference in the request body.
    """
    try:
        return project.get_openai_client(agent_name=agent_name), {}
    except TypeError:
        client = project.get_openai_client()
        return client, {"extra_body": {"agent": {"name": agent_name, "type": "agent_reference"}}}
