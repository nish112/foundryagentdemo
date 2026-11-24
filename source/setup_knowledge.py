"""One-time setup: upload the runbook knowledge to a Foundry vector store and save its ID.

Run once (or again after you change files in data/knowledge):
  python setup_knowledge.py
"""
from __future__ import annotations

import re

from noc.foundry import load_settings, project_client
from noc.state import ROOT

KNOWLEDGE_DIR = ROOT / "data" / "knowledge"
ENV_FILE = ROOT / ".env"
ENV_KEY = "FOUNDRY_NOC_VECTOR_STORE_ID"


def save_env(value: str) -> None:
    text = ENV_FILE.read_text(encoding="utf-8") if ENV_FILE.exists() else ""
    line = f"{ENV_KEY}={value}"
    if re.search(rf"^{ENV_KEY}=.*$", text, flags=re.M):
        text = re.sub(rf"^{ENV_KEY}=.*$", line, text, flags=re.M)
    else:
        text = text.rstrip("\n") + ("\n" if text else "") + line + "\n"
    ENV_FILE.write_text(text, encoding="utf-8")


def main() -> None:
    settings = load_settings(require_vector_store=False)
    files = sorted(p for p in KNOWLEDGE_DIR.glob("*.md"))
    if not files:
        raise SystemExit(f"No knowledge files found in {KNOWLEDGE_DIR}")
    with project_client(settings) as project:
        client = project.get_openai_client()
        store = client.vector_stores.create(name="asterwave-noc-knowledge-v04")
        print(f"Vector store created: {store.id}")
        for path in files:
            with path.open("rb") as fh:
                result = client.vector_stores.files.upload_and_poll(vector_store_id=store.id, file=fh)
            status = getattr(result, "status", "unknown")
            print(f"  {path.name}: {status}")
            if status != "completed":
                raise SystemExit(f"Indexing failed for {path.name}: {getattr(result, 'last_error', '')}")
    save_env(store.id)
    print(f"Saved {ENV_KEY} to .env. You can now run: python noc_agent.py")


if __name__ == "__main__":
    main()
