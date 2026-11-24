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
| Python | 3.10 to 3.13, **64-bit (x64)**. On Windows, use x64 Python 3.13 (see section 2). Avoid 32-bit Python and very new releases, which can make the install fail with a `cryptography` build error |
| Azure CLI | Installed and signed in with `az login` (the code uses `DefaultAzureCredential`) |
| Network | Outbound HTTPS to `*.services.ai.azure.com` and `login.microsoftonline.com` |
| Terminal | Windows Terminal / PowerShell (commands below), or bash on macOS/Linux. Use a large font: participants read the tool lines. |
| Optional: Application Insights | Connected to the project if you want to show agent traces in the portal (not required to run the demo) |

> Foundry RBAC roles were recently renamed (Foundry User = Azure AI User). Either name is fine.

## 2. Install

Open a terminal in the `source` folder. Follow **2A on Windows** (recommended for everyone, it avoids the
`cryptography` error described below) or **2B on macOS/Linux**.

### 2A. Windows (PowerShell): x64 Python 3.13, prebuilt packages only

```powershell
cd Foundry\noc-incident-coordinator\source

# 1. See which Python you have now (version and platform)
python -c "import sys, sysconfig; print(sys.version.split()[0], sysconfig.get_platform())"
#    Good: 3.13.x win-amd64     Problem: win32 (32-bit), win-arm64, or 3.14+

# 2. Install x64 Python 3.13 and confirm its tag
py install 3.13-64
py list                           # 3.13-64 must appear in the list

# 3. Create the environment with the x64 Python
#    (if an earlier attempt failed, delete the old one first: Remove-Item -Recurse -Force .venv)
py -V:3.13-64 -m venv .venv
.\.venv\Scripts\Activate.ps1
# If PowerShell blocks activation: Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# 4. Confirm the environment is x64 Python 3.13
python -c "import sys, sysconfig; print(sys.version.split()[0], sysconfig.get_platform())"
#    Expected: 3.13.x win-amd64

# 5. Install packages, refusing to compile anything
python -m pip install --upgrade pip
python -m pip install --only-binary=:all: -r requirements.txt
```

**Why these steps (the `cryptography` error)**

The sign-in package (`azure-identity`) depends on a security library called `cryptography`. Normally pip
downloads a ready-made (prebuilt) copy of it. If no prebuilt copy exists for your Python, for example
32-bit Python, Windows on Arm Python, or a Python release newer than the library supports, pip tries to
**compile it from source**. That needs a Rust compiler and C++ build tools, which most laptops do not have,
so the install fails with messages such as:

```text
error: can't find Rust compiler
Failed building wheel for cryptography
Microsoft Visual C++ 14.0 or greater is required
```

The fix is to use a Python that has prebuilt copies (x64 Python 3.13), and tell pip never to compile
(`--only-binary=:all:`). If a prebuilt copy is still missing, pip now stops with a short, clear
"No matching distribution" message instead of a long compiler error.

> **`py install` not recognised?** That command comes from the Python install manager. Either install the
> Python install manager from python.org (or the Microsoft Store), or download the **Windows installer
> (64-bit)** for Python 3.13 from python.org, then use `py -3.13 -m venv .venv` in step 3 instead.
>
> **Windows on Arm laptop (for example Surface Pro with Snapdragon)?** Still use `3.13-64`. The x64 Python
> runs under Windows emulation and gets the prebuilt packages.

### 2B. macOS / Linux

```bash
cd Foundry/noc-incident-coordinator/source
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install --only-binary=:all: -r requirements.txt
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

## 6. Set up complete

Go to README.md==>8. Demo steps (presenter walkthrough)==>Step 1 - The alarm storm: what is going on?   , here you will find steps on how to execute the demo.

