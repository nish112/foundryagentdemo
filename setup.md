# Setup guide - NOC Incident Coordinator (Foundry Agent Service)

Allow about 20 minutes the first time. Rehearse the full demo at least once after setup (about 15 minutes).
New to telecom? Read section 2 of README.md (telecom primer and glossary) before rehearsing.

**What runs where**

| Runs in Foundry (your project) | Runs on your laptop |
|---|---|
| The prompt agent (instructions, tool definitions, versions) | `noc_agent.py`: the console, the function-calling loop and the approval box |
| The model deployment | The 10 tools, reading sample network data from `data/telemetry/` |
| The vector store for file search (3 knowledge files) | Local incident state, change and problem records, care advisories (`runs/`) |
| Conversations (incident memory) | |

## 1. Prerequisites

| Item | Detail |
|---|---|
| Azure subscription | With permission to create or use a Microsoft Foundry resource and project |
| Foundry project | A Foundry (new) project. Copy its **project endpoint** from the project welcome page. Format: `https://<resource-name>.services.ai.azure.com/api/projects/<project-name>` |
| Model deployment | A chat model deployed in the project that supports **function calling** and **file search** with agents (for example a current GPT-4.1 or GPT-5 family model; check the model and region support pages in the Foundry docs). Note the **deployment name**, not the model name. Reasoning-capable models give the best diagnosis narrative; mini models work but give shorter answers. |
| Roles | **Foundry User** (formerly Azure AI User) on the project, to create and run agents. **Storage Blob Data Contributor** on the project's storage account, to upload the knowledge files. |
| Python | 3.10 or later (`python --version`) |
| Azure CLI | Installed and signed in with `az login` (the code uses `DefaultAzureCredential`) |
| Network | Outbound HTTPS to `*.services.ai.azure.com` and `login.microsoftonline.com` |
| Terminal | Windows Terminal / PowerShell (commands below), or bash on macOS/Linux. Use a large font: participants read the tool lines. |
| Optional: Application Insights | Connected to the project if you want to show agent traces in the portal (not required to run the demo) |

> Foundry RBAC roles were recently renamed (Foundry User = Azure AI User). Either name is fine.

## 2. Install

Open a terminal in the `source` folder.

```powershell
cd Foundry\noc-incident-coordinator\source
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
# If PowerShell blocks activation: Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

`requirements.txt` installs:

| Package | Why |
|---|---|
| `azure-ai-projects>=2.3.0` | Foundry Agent Service SDK (prompt agents, conversations, vector stores). Version 2.x is required; 1.x (classic) is not compatible. |
| `azure-identity>=1.18.0` | Entra ID sign-in via `az login` |
| `openai>=1.99.0` | Responses and conversations client returned by the Foundry project |
| `python-dotenv>=1.0.1` | Reads settings from `.env` |

## 3. Configure

```powershell
copy .env.example .env            # macOS/Linux: cp .env.example .env
```

Edit `.env`:

```text
FOUNDRY_PROJECT_ENDPOINT=https://<resource-name>.services.ai.azure.com/api/projects/<project-name>
FOUNDRY_MODEL_NAME=<your-model-deployment-name>
FOUNDRY_NOC_AGENT_NAME=asterwave-noc-coordinator
FOUNDRY_NOC_VECTOR_STORE_ID=            # filled in by section 5
```

Never share or commit `.env`. It is excluded by `.gitignore`.

## 4. Sign in

```powershell
az login
az account set --subscription "<subscription name or id>"
az account show --query "{user:user.name, subscription:name}" -o table   # confirm the right account
```

Sign in with the same account that has the Foundry User role on the project.

## 5. Index the knowledge (once)

```powershell
python setup_knowledge.py
```

This creates the vector store `asterwave-noc-knowledge-v04`, uploads the 3 knowledge files (runbook, architecture notes, action catalog) in
`data/knowledge/`, **waits until each one is indexed**, and writes `FOUNDRY_NOC_VECTOR_STORE_ID` into `.env`.
Expected output: each file shows `completed`.

Run it again only if you change files in `data/knowledge/`. A new vector store ID also creates a new agent version on the next run.

## 6. Check offline (optional, no Azure)

```powershell
python -m unittest discover -s tests -v
```

Expected: `Ran 18 tests ... OK`. This confirms the tools, operational rules (change control, approval, recovery criteria, problem record) and the agent loop.

## 7. Run

```powershell
python noc_agent.py
```

| Option | Use |
|---|---|
| `--resume` | Continue the last conversation and incident |
| `--auto-approve` / `--auto-reject` | Rehearsal without typing approvals |
| `--prompt "..."` | Send a first message without typing it |
| `--new-version` | Force a new agent version in Foundry |
| `--vector-store-id <id>` | Use a different vector store |
| `--cleanup` | Delete the agent version, the conversation and local state |

In-session commands: `/advance <minutes>`, `/status`, `/reset`, `/help`, `/exit`.

The first run creates the agent in Foundry. Later runs reuse it while the instructions,
tools, model and vector store stay the same. Each agent turn usually takes a few seconds to
tens of seconds, depending on the model and how many tools it calls.

**Check the agent in the portal:** open your project in the Foundry portal and go to **Agents**.
You should see `asterwave-noc-coordinator` with its instructions, file search and function tools.

> **Do not run the demo from the portal playground.** The playground shows the agent but does not execute
> function calls (they run on your laptop). Always run the demo from the terminal.

## 8. Pre-delivery checklist

**The day before**
- [ ] `python -m unittest discover -s tests` shows `OK`
- [ ] `python setup_knowledge.py` completed and `.env` has `FOUNDRY_NOC_VECTOR_STORE_ID`
- [ ] One full rehearsal using README section 7 (with approvals typed by you)
- [ ] Note the model deployment name and region in case someone asks
- [ ] Record a backup screen capture of a full run (in case the venue network fails)

**One hour before**
- [ ] `az login` (tokens expire) and `az account show` shows the right subscription
- [ ] Start fresh: `python noc_agent.py`, then `/reset`, then `/exit` (or delete the `runs` folder)
- [ ] Foundry portal open on the project's Agents page, signed in
- [ ] Terminal font enlarged; `runs/outbox` folder ready to open in an editor
- [ ] README demo steps open on a second screen

**Hands-on option for participants**
- Each participant needs their own Foundry project, model deployment and roles (section 1),
  or a shared project with a unique `FOUNDRY_NOC_AGENT_NAME` per participant (for example `noc-coordinator-<alias>`)
  to avoid overwriting each other's agent versions.
- Each participant runs `setup_knowledge.py` once (one vector store each), or shares one store ID through `.env`.

## 9. Files created at runtime

| Path | Content |
|---|---|
| `source/runs/state.json` | Incidents, emergency change and problem records, demo clock, conversation ID, audit log |
| `source/runs/agent_version.json` | Agent name, version and definition fingerprint |
| `source/runs/outbox/` | Published care advisories (`..._v1.md`, `..._v2.md` per update) |

Delete the `runs` folder for a completely fresh local start.

## 10. Clean up after the event

```powershell
python noc_agent.py --cleanup
```

This deletes the agent version, the conversation and the local state. The vector store is **kept**.
Delete it in the Foundry portal if you no longer need it.

**Cost:** you pay for model tokens per turn plus file search (vector storage and tool calls). A full
demo run is a small number of turns, but delete unused vector stores and agent versions after events.

## 11. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `Missing settings in ...\.env` | `.env` not created or values empty | Complete section 3; run `setup_knowledge.py` |
| `DefaultAzureCredential failed to retrieve a token` | Not signed in | `az login`, then retry |
| 401 / 403 when creating the agent | Missing role | Ask for **Foundry User** on the project |
| 403 during `setup_knowledge.py` | Missing storage role | Ask for **Storage Blob Data Contributor** on the project storage account |
| `ImportError: PromptAgentDefinition` or `FunctionTool` | Old SDK (1.x) installed | `python -m pip install --upgrade "azure-ai-projects>=2.3.0"` |
| Agent replies like a generic assistant, ignoring the NOC role | Agent not bound to the request (older 2.x SDK) | Upgrade `azure-ai-projects` to the latest version; run with `--new-version` |
| Model deployment not found / tools not supported | Wrong deployment name or a model without tool support | Check `FOUNDRY_MODEL_NAME`; use a model that supports function calling |
| No `[file_search]` lines and no citations | Vector store not indexed | Rerun `setup_knowledge.py`; check every file shows `completed` |
| Verify keeps saying MONITORING | Demo clock not advanced | Type `/advance 5` before asking for status (step 7 of the demo) |
| Proposal returns BLOCKED | A runbook rule applied (missing diagnostics, change pending or still settling, precondition not met) | Expected behaviour: follow the reason in the tool result; for the demo, run all 5 checks first |
| Care advisory REJECTED | Customer wording contained internal terms (ring, node, APN names) | Expected behaviour: ask the agent to rewrite in plain language |
| `An open incident already exists` | Previous run state | `/reset` in the session, or delete `runs/` |
| Agent talks about an old incident the tools do not know | Old conversation reused with fresh local state | Use `/reset` (starts a new conversation) or run without `--resume` |
| `python` not found, or the Microsoft Store opens | Python not on PATH (Windows) | Use `py -3 -m venv .venv`, or reinstall Python with "Add to PATH" |
| `az` not found | Azure CLI not installed | Install the Azure CLI, open a new terminal, then `az login` |
| PowerShell: "running scripts is disabled" | Execution policy blocks venv activation | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`, then activate again |
| Agent proposes or executes too early in the demo | The model ran ahead | Fine: skip the matching demo step; the tools still enforce the runbook order |
| Answers are slow | Large model or busy region | Use a faster deployment for live delivery; keep the backup recording ready |
| Function call errors after a long pause | Responses wait at most 10 minutes for tool outputs | Answer the approval prompt promptly; ask again if it expired |

## 12. Official documentation

- Create a prompt agent: https://learn.microsoft.com/en-us/azure/foundry/agents/quickstarts/prompt-agent
- File search tool: https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/file-search
- Function calling: https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/function-calling
