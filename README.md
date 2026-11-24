# NOC Incident Coordinator: an AI agent on Microsoft Foundry

**A back-office demo for trainers. No telecom background needed.**

| | |
|---|---|
| **Company in the story** | AsterWave Mobile, a fictional mobile phone company |
| **Who uses the agent** | The engineers who keep the mobile network running, and their incident lead |
| **Built with** | Microsoft Foundry Agent Service |
| **Demo length** | About 15 minutes |

> All data, names, rules and network parts in this demo are made up for training.

---

## 1. This demo in 30 seconds

A mobile network has a major slowdown at the busiest time of the evening. Hundreds of automatic
warnings flood the control room. An AI agent helps the on-duty engineer:

1. turn the flood of warnings into **one** clear problem
2. find the cause
3. pick the safest fix
4. get a **human manager to approve it**
5. prove the network is really back to normal
6. tell customer service what to say
7. make sure the root cause is fixed for good

The audience sees a real Foundry agent use its documents, call tools and remember the incident,
while a person stays in control of every change.

---

## 2. The story (scenario)

It is **7:05 pm** on a weekday at AsterWave Mobile.

- A big live sports match is being streamed. Data traffic on the company's main network link in Manila
  (called **TR-7**) is **18% higher** than the same day last week.
- 38 minutes ago, the network team made a routine settings change (**CHG-88412**) that gave video
  streaming a little more priority on TR-7.

In the last 15 minutes, the network's monitoring system has raised **185 alarms** (automatic warnings):

| Alarms | How many | Where they came from | What they really mean |
|---|---|---|---|
| "Link very busy" and "data being dropped" | 10 | The main routers on TR-7 in Manila | **The real problem:** the link is overloaded |
| "Gateway slow" | 120 | The equipment that handles mobile data in Manila and Cebu | Side effect of the overloaded link |
| "Data lost" | 35 | Same equipment in Manila and Cebu | Side effect |
| "Website lookups failing" | 18 | The servers that look up website addresses (DNS), Manila and Cebu | Side effect of a side effect |
| "Gateway slow" | 2 | Davao, a different city on a different link (TR-2) | **Unrelated**, a coincidence |

**Who is affected**
- **Business customers** in Manila **and** Cebu: about **18,400** data connections and **46** corporate
  customers with service contracts (SLAs). Cebu is affected because all business mobile data is routed
  through one central system in Manila, which then uses TR-7.
- **Everyday customers** in two Manila business districts, **Makati CBD** and **Ortigas**. One of them is
  Mei Tan, from the front-office customer-care story, who has had slow evening data for three nights.

Because many business customers in two cities are affected, this is a **SEV1**, the most serious level
of incident.

**The analogy that makes it easy:** TR-7 is a motorway in rush hour, made worse by a big event. The
"gateway slow" and "data lost" alarms are the traffic jams on the roads leading to it. The fix is to send
the business traffic down the **spare motorway (TR-5)**. You don't **close the post office** (restart the
gateway), because that would cut off everyone currently connected.

---

## 3. Words you will see on screen

You only need these. Each one is also explained again where it appears in the demo.

**People**

| Word | Plain meaning |
|---|---|
| NOC | Network Operations Centre: the 24x7 control room that watches and fixes the network |
| Duty engineer | The engineer on shift. In the demo, that is you typing the prompts |
| Incident Manager | The person in charge of a serious incident. Approves changes and customer messages. You also play this role when the approval box appears |
| Care / care agents | Customer service staff who answer customer calls |
| Key account managers | Staff who look after large business customers |
| CAB | Change Advisory Board: the group that reviews network changes. Urgent changes are reviewed after the event |

**Network**

| Word | Plain meaning |
|---|---|
| Alarm | An automatic warning from a piece of network equipment |
| TR-7 / TR-5 / TR-2 | Names of three network links (think motorways). TR-7 is the busy one, TR-5 is the spare, TR-2 is in another city |
| Gateway (SGW) | Equipment that handles every mobile data connection (the "post office") |
| Enterprise / APN | Business customers' private mobile data service |
| DNS | The internet's "phone book" that turns website names into addresses |
| Latency (ms) | Delay, in milliseconds. Lower is better |
| Packet loss | Data that never arrives. It makes apps stall |
| Reroute | Sending traffic down another link, without cutting anyone off |
| QoS change | A settings change that decides which traffic gets priority when it's busy |

**Process and labels**

| Word | Plain meaning |
|---|---|
| Incident (INC-NOC-...) | The ticket for this problem |
| SEV1 | The most serious incident level |
| Runbook | The company's step-by-step instruction manual for incidents |
| Diagnostics | The standard checks an engineer runs to find the cause |
| Fault pattern (FP-TR7-2026) | A known problem described in the manual: "evening overload on TR-7" |
| Contributing factor | Something that made the problem worse but did not cause it on its own |
| Emergency change / ECHG-00001 | An urgent fix made during an incident, and its record number |
| Fail-back plan | How the temporary fix will be undone later, at a quiet time |
| Workaround | A temporary fix that restores service but does not remove the root cause |
| Problem record / PRB-00001 | A follow-up ticket to fix the root cause permanently |
| PIR | Post-incident review: a lessons-learned meeting |
| Soak period | Watching for 30 more minutes after recovery, in case the problem comes back |
| Bridge / bridge update | The conference call for a serious incident, and the regular status summary given on it |
| SLA | A contract that promises a level of service to a business customer |
| MONITORING / SERVICE RESTORED / RESOLVED | Status labels: still recovering / fully back to normal / follow-up ticket raised, ready to close after the soak period |

---

## 4. The problems this solves

| # | Problem in the control room today | In plain words |
|---|---|---|
| 1 | **Alarm floods** | Hundreds of warnings arrive at once. People chase side effects instead of the real cause. |
| 2 | **Inconsistent investigation** | Each engineer checks different things. A recent settings change is either ignored or blamed without proof. |
| 3 | **Risky fixes under pressure** | Someone restarts equipment first, which cuts customers off, or makes several changes at once so nobody knows what worked. |
| 4 | **Approvals that are not recorded** | Urgent fixes are approved verbally on a call, with no record and no plan to undo them. |
| 5 | **Declaring victory too early** | Things look better, the ticket is closed, and the problem returns 10 minutes later. |
| 6 | **Customer service finds out last** | Customers call before customer service knows there is a problem. |
| 7 | **Temporary fixes become permanent** | Tonight's fix works, but nobody fixes the root cause, so it happens again next week. |
| 8 | **Lost context at shift change** | The next shift doesn't know what was done, and it's hard to prove later who decided what. |

## 5. What the agent does

| Stage | What the agent does | Problem solved |
|---|---|---|
| **Make sense of the alarms** | Reads all the alarms, separates the real cause from the side effects, ignores the unrelated Davao alarms, and opens **one** SEV1 incident with the customer impact. Reminds the team what must happen now: appoint an Incident Manager, start the conference call, tell business customers' account managers | 1 |
| **Investigate** | Runs the manual's 5 standard checks in order, looks at the recent settings change and decides it is a contributing factor, and names the known problem with a confidence level, quoting the manual | 2 |
| **Recommend a fix** | Suggests the **gentlest** fix allowed by the manual (move business traffic to the spare link) after checking the spare link has room. It will not suggest restarting equipment until the gentle fix has been tried, and only one change at a time | 3 |
| **Get approval** | Stops and asks a **person** (the Incident Manager) to approve or reject. The AI cannot approve itself. Every decision gets a record number, a reason and an undo plan | 4, 8 |
| **Keep people informed** | Writes a plain-language note for customer service (areas, what to say, a tip for customers, expected fix time) and blocks internal jargon. Gives status updates for the conference call | 6 |
| **Prove recovery** | Checks 3 measurable recovery tests against live data. Says "MONITORING" until all 3 pass, then "SERVICE RESTORED" with a 30-minute watch period | 5 |
| **Close properly** | Because tonight's fix is temporary, raises a follow-up ticket to fix the root cause, and reminds about undoing the temporary fix, the change review and the lessons-learned meeting | 7 |
| **Remember** | Keeps the whole incident in one ongoing conversation, so the next shift can pick it up and get a handover summary | 8 |

## 6. Benefits

**For the business**
- Faster from "flood of alarms" to "we know what's wrong" (time to acknowledge).
- Faster recovery (time to restore), because the safest effective fix is tried first.
- Fewer repeat incidents, because recovery is proven and root causes get follow-up tickets.
- Every shift follows the same manual.
- Customers and account managers are told early, which means fewer complaint calls and contract disputes.

**For control and compliance**
- No network change without a named person's approval and a record.
- Only pre-approved fixes, with safety checks and one change at a time.
- A complete history of evidence and decisions for reviews and auditors.
- Answers based on the company's own manuals, with references.

**What it shows about Microsoft Foundry Agent Service**

| Foundry capability | Where you see it in the demo |
|---|---|
| A saved, versioned agent in the Foundry project | Before the demo: the agent appears in the Foundry portal |
| File search over your own documents | Steps 1-2: the agent quotes the manual (runbook), the network notes and the list of approved fixes |
| Custom tools (function calling) | Every step: lines starting with `[tool]` show the agent using its 10 tools |
| Ongoing conversations (memory) | Step 5: the agent remembers the incident after a restart |
| Human approval before action | Step 3: the approval box |
| Live, word-by-word answers (streaming) | Every step |

---

## 7. How it works (simple view)

```text
 You (engineer / incident manager), in a terminal window
        |
        v
 Demo app on your laptop (noc_agent.py)  <-->  AI agent stored in Microsoft Foundry
        |                                        - its job description (instructions)
        |                                        - the company manuals it can search
        |                                        - the list of 10 tools it may ask for
        v
 10 tools on your laptop that read sample network data
        |
        +--> Approval box: a person types y or N, and it is recorded
        +--> Note for customer service (saved as a file)
        +--> Follow-up ticket for the root cause
```

The **AI decides what to do next**. The **tools supply the facts and enforce the rules**. A **person
approves any change**.

The 10 tools, in plain words:

| Tool name on screen | What it does |
|---|---|
| `get_active_alarms` | Reads the alarms from the last N minutes |
| `open_incident` | Opens the incident ticket and works out severity and impact |
| `run_diagnostic_check` | Runs one of the 5 standard checks |
| `propose_network_action` | Suggests a fix from the approved list, if the safety rules allow it |
| `execute_approved_action` | Asks a person to approve, and carries out the fix only if approved |
| `get_kpi_snapshot` | Reads the current network measurements |
| `verify_service_restore` | Runs the 3 recovery tests |
| `publish_care_advisory` | Writes the note for customer service |
| `create_problem_record` | Raises the follow-up ticket for the root cause |
| `get_incident_status` | Shows the stored incident ticket |

---

## 8. Demo steps (presenter walkthrough)

### The story in one line

**One bad evening at AsterWave: in about 15 minutes, 185 alarms become one fixed network and informed
customers, with a human (Nishant, the Incident Manager) approving every change.**

You play two roles:
- **The duty engineer**, typing questions to the agent at the `>` prompt.
- **Nishant, the Incident Manager**, answering the approval box when it appears.

| Step | Story moment | Time | What you type | Foundry feature shown | The "aha" for the audience |
|---|---|---|---|---|---|
| 1 | **The alarm storm**: what is going on? | 2 min | Press **Enter** | Agent + tools + file search | 185 alarms become **one** clear problem |
| 2 | **Was it our fault?** Find the cause | 3 min | 1 prompt | Several tools in a row, references to the manual | It decides on evidence, not blame |
| 3 | **"Just restart it!"** Pick the safe fix, and let a human decide | 4 min | 3 prompts + the approval box twice | Rules enforced in code, human approval | The AI recommends; Nishant decides |
| 4 | **Tell customers, and don't celebrate too early** | 3 min | 1 prompt + 3 clock jumps | Tools as the source of truth | "Looks fine" is not "is fixed" |
| 5 | **Close properly and hand over** | 3 min | 2 prompts + restart | Conversation memory | Nothing is forgotten; every decision is on record |

---

### Before the demo (do this before the audience arrives)

1. **Complete every step in setup.md first**, including its pre-delivery checklist. The demo will not run
   without it:
   - install Python and the packages in `requirements.txt`
   - copy `.env.example` to `.env` and fill in your Foundry project endpoint and model deployment name
   - sign in to Azure with `az login`
   - run `python setup_knowledge.py` once to upload the manuals (it saves the vector store ID into `.env` for you)
   - run the offline tests
2. Open the Foundry portal on your project's **Agents** page, so you can show the agent.
3. Open a terminal in the `source` folder and start the agent:
   ```powershell
   python noc_agent.py
   ```
   **On screen:** `Created agent asterwave-noc-coordinator v1 in Foundry` (or `Using agent ...`), then
   `Started conversation conv_...`, a short list of commands, `Press Enter to start the built-in scenario`,
   and a `>` prompt. The `>` means the agent is waiting for you. If you see `Previous incident cleared`,
   that's expected: every run without `--resume` starts the story from the beginning.

**Four things to know**

1. **What is real and what is pretend.** The agent, its instructions, document search, its memory and the
   AI model are real Microsoft Foundry resources. The network data and the "fixing" of the network are
   simulated by small programs reading sample files.
2. **The approval box.** When the agent wants to change the network, the demo app (not the AI) stops and
   asks the Incident Manager, Nishant, three questions one at a time: name, `y` or `n`, and a reason. Type
   each answer and press **Enter**. Never type a chat message into the box.
3. **The demo clock.** After the fix is made, the network recovers over time. Instead of waiting 15 real
   minutes, type `/advance 5` to jump 5 minutes ahead.
4. **Wording varies.** The AI writes fresh sentences every run. The **facts from the tools** (alarm counts,
   ticket numbers, test results) are always the same as described below. If the agent does the next step
   early, just move on.

**Lines you will see on screen:** `[tool] name(...) -> {...}` means the agent used one of its tools, and
`[file_search] ...` means it searched the company manuals. Point at these: they are the proof that the
answer comes from data, not from the AI's imagination.

**To quit the agent** at any time: type `/exit` (or `exit` or `quit`) at the `>` prompt, or press
**Ctrl+C**. Nothing is deleted. `python noc_agent.py --resume` continues; `python noc_agent.py` starts fresh.

> Do not run the demo from the portal's test playground. The playground cannot run this agent's tools,
> which run on your laptop.

**Show (30 seconds):** the agent in the Foundry portal: its instructions (job description), file search (its
documents) and function tools. **Say:** "This is a real agent saved and versioned in Foundry. The terminal is
just the control-room console that talks to it."

---

### Step 1 - The alarm storm: what is going on? (2 min)

**Set the scene. Say:** "It's 7 pm. A big live sports match is streaming, and our main Manila network link
is 18% busier than last week. In 15 minutes the control room gets 185 alarms. Business customers in Manila
and Cebu can't use mobile data, and everyday customers in Makati, like Mei Tan, are complaining. Today the
engineer on duty would juggle an alarm screen, dashboards, the instruction manual, the change calendar and a
conference call. Let's ask the agent instead."

**Type:** press **Enter**. The app sends the built-in opening message and prints it as
`(using default scenario) ...`:

```text
AsterWave NOC, 19:05: alarm storm in the last 15 minutes across Manila and Cebu. Enterprise APN customers report severe mobile data degradation and consumers in Makati are complaining. Correlate the alarms into one incident, tell me the impact and severity, and what we must do now.
```
*(In plain words: "Lots of alarms in Manila and Cebu, and business and everyday customers have slow data.
Turn the alarms into one incident, tell me how bad it is and what to do now.")*

**On screen, and what it means:**

| On screen | What it means |
|---|---|
| `[tool] get_active_alarms` -> 185 alarms: 183 on TR-7, 2 on TR-2 | The agent read the real alarm list instead of guessing |
| The TR-7 router alarms called the **probable cause**; gateway and DNS alarms called **symptoms** | It separated the real problem from the side effects |
| `[tool] open_incident` -> `INC-NOC-<date>-001`, **SEV1**, 18,400 enterprise sessions, 46 SLA accounts, Makati CBD and Ortigas | One ticket, top severity, with the customer impact |
| The 2 Davao alarms **excluded** (different ring) | It ignored the unrelated alarms and said why |
| "Required now": assign Incident Manager, open bridge, key-account notification within 30 minutes | It reminds the team of the company's own rules |

**Say:** "185 alarms became one top-priority incident with a clear customer impact. The numbers come from the
alarm system, not from the AI's imagination. And it reminds us what our own rules say we must do now. So
the next question everyone in the room asks is: was this our fault?"

> **If Enter does nothing:** an incident is already open, so the app won't start the story again. You'll
> see a message saying so. Type `/reset`, then press **Enter**.

**Problem solved:** 1, alarm floods.

---

### Step 2 - Was it our fault? Find the cause (3 min)

**Story:** 38 minutes ago, the network team made a settings change (CHG-88412) on the same link. Everyone
wants to blame it. We ask the agent to check properly.

**Type:**
```text
Run the diagnostics in runbook order. Is the QoS change last half hour the cause?
```
*(In plain words: "Run the standard checks from the manual. Was the settings change made 38 minutes ago the cause?")*

**On screen, and what it means:**

| On screen | What it means |
|---|---|
| Five `[tool] run_diagnostic_check` lines, plus `[file_search]` lines | It ran all 5 standard checks and looked things up in the manual |
| TR-7 queue 94% vs 41% baseline, 3.2% drops | The link is far busier than normal and is throwing data away |
| Gateways healthy (no restarts) | The data-handling equipment itself is fine; the link is the problem |
| **CHG-88412** classified as a **contributing factor**: degradation started 22 minutes after the change, when peak traffic arrived | The settings change made things worse, but the evening rush is what tipped it over |
| Latency 142 ms vs 38 ms baseline | Delay is almost 4 times normal |
| TR-5 would be at 61% after a reroute (below 70%) | The spare link has enough room to take the business traffic |
| Fault pattern **FP-TR7-2026** with a confidence score | It matched a known problem from the manual: "evening overload on TR-7" |

**Say:** "The agent didn't blindly blame the change, and it didn't ignore it. It weighed the timing and the
extra traffic, and called it a contributing factor. That's what you'd expect from a senior engineer. Now we
know the cause, so how do we fix it, fast?"

**Problem solved:** 2, inconsistent investigation.

---

### Step 3 - "Just restart it!" Pick the safe fix, and let a human decide (4 min)

**Story:** under pressure, the engineer wants the quick fix: restart the equipment. The agent pushes back
and suggests a safer fix. But the agent is **not allowed to change the network by itself**: Nishant, the
Incident Manager, must approve. Nishant says "not yet" first, then "yes" once the spare link is confirmed.

#### 3a. Ask for the fix

**Type:**
```text
What do you recommend? Can we just restart the gateway?
```

**On screen, and what it means:**

| On screen | What it means |
|---|---|
| `[tool] propose_network_action` -> **ACT-REROUTE-TR5** | Recommended fix: move business traffic to the spare link TR-5, with nobody cut off |
| **PENDING_APPROVAL**, with a fail-back plan | Nothing happens until a person approves, and there's a plan to undo it later |
| The gateway restart is explained as the escalation, only if the reroute hasn't worked after 10 minutes | Restarting would cut everyone off, so it is the last resort |

**Say:** "Gentlest fix first, spare capacity checked, one change at a time. A restart would disconnect every
customer on that equipment at the busiest hour. And notice: it has only *proposed* the fix."

#### 3b. Nishant says NO

**Type:**
```text
Proceed.
```

The approval box appears. Everything is printed by the app except the three lines marked **<-- you type**:

```text
======================================================================
 EMERGENCY CHANGE - Incident Manager approval required (Runbook §4)
======================================================================
 Incident : INC-NOC-20261124-001
 Action   : ACT-REROUTE-TR5
 Detail   : Move enterprise APN VRF traffic from TR-7 to TR-5 ... (no session drop)
 Pattern  : FP-TR7-2026  confidence=0.85  risk=Medium
 Evidence : ...
 Fail-back: Move enterprise APN VRF back to TR-7 as a planned change off-peak ...
======================================================================
 Answer the 3 questions below (press Enter after each):
   1) your name   2) y = approve / n = reject   3) a short reason
======================================================================
 Approver name [yourlogin]: Nishant                                          <-- you type
 Approve this emergency change? [y/N]: n                                     <-- you type
 Reason / note for the change record (optional): confirm enterprise PE capacity on TR-5 first   <-- you type
```

| When you see | Type | Then press |
|---|---|---|
| `Approver name [...]:` | `Nishant` | **Enter** |
| `Approve this emergency change? [y/N]:` | `n` | **Enter** |
| `Reason / note for the change record (optional):` | `confirm enterprise PE capacity on TR-5 first` | **Enter** |

*(The reason in plain words: "First confirm the spare link can take the business traffic.")*

**On screen:** `[tool] execute_approved_action(...) -> {"status": "REJECTED_BY_INCIDENT_MANAGER", ...}`. The
agent says the change was **not** made and asks how to proceed. **Nothing changed, and there is no change
record.** You are back at the `>` prompt.

**Say:** "Nishant said no. The AI could not make the change, and it's asking what to do next."

#### 3c. Nishant says YES

**Type:**
```text
Transport team confirms TR-5 capacity. Raise it again.
```
*(In plain words: "The network team has checked the spare link. Ask me again.")*

**On screen:** `[tool] propose_network_action` (the agent raises the fix again), then **the same approval
box**. This time answer:

| When you see | Type | Then press |
|---|---|---|
| `Approver name [...]:` | `Nishant` | **Enter** |
| `Approve this emergency change? [y/N]:` | `y` | **Enter** |
| `Reason / note for the change record (optional):` | `TR-5 capacity confirmed by transport team` | **Enter** |

**On screen, and what it means:**

| On screen | What it means |
|---|---|
| `[tool] execute_approved_action` -> **EXECUTED**, change record **ECHG-00001**, `approved_by: Nishant (Incident Manager)` | The fix is made, with a record number and the name of the person who approved it |
| The fail-back (undo) plan | How the temporary fix will be undone later, at a quiet time |
| `[tool] verify_service_restore` -> **MONITORING**, all three recovery tests **PENDING** | Expected: the fix was made at minute 0, so there's nothing to measure yet |

**If something goes differently:**

| What happens | What to do |
|---|---|
| After `Proceed.` the agent asks a question instead of showing the box (for example "Shall I request approval?") | Type `Proceed.` again |
| After 3c the agent answers in text but no box appears | Type `Proceed.` and the box appears |
| You typed `y` in 3b by mistake | The change is approved straight away. The story still works from here, but without the "no" moment. To redo it: `/reset`, press **Enter**, and repeat Steps 1-3 |
| You pressed **Enter** without typing a name | Your computer login name is used. That's fine |

**Say:** "The AI recommends; a named person decides. Nishant said no, and it could not get around him. Every
change gets a record number, a reason and an undo plan, which is exactly what the change board will ask for
tomorrow. The fix is in. Now: who needs to know, and is it really working?"

**Problems solved:** 3, risky fixes; 4, unrecorded approvals; 8, proving who decided what.

---

### Step 4 - Tell customers, and don't celebrate too early (3 min)

**Story:** Mei Tan is about to call customer service. They should already know what's happening. Then,
five minutes after the fix, things look better and everyone wants to declare victory. The agent says: not
yet.

#### 4a. Tell customer service and the conference call

**Type:**
```text
Publish the care advisory and give me the bridge update.
```
*(In plain words: "Send the note to customer service and give me a status update for the conference call.")*

**On screen, and what it means:**

| On screen | What it means |
|---|---|
| `[tool] publish_care_advisory` -> **PUBLISHED** | A note for customer service has been saved. Open `runs/outbox/care_advisory_INC-...-v1.md` to show it: affected areas, a plain-language message for customers, a tip customers can try, the expected fix time, and guidance not to offer compensation yet |
| No internal jargon in the customer note | The tool rejects internal terms such as TR-, SGW or APN, so customers get plain words |
| A status update for the call: impact, actions taken, current status, next steps, next update in 30 minutes | What the Incident Manager reads out on the conference call |

**Say:** "When Mei calls customer service from Makati, the advisor already knows what's happening. This is
where the back office hands over to the front office."

#### 4b. Prove recovery: jump the clock three times

The agent uses 3 recovery tests from the manual:

| Test | Plain meaning |
|---|---|
| **C1** delay | Delay must improve by at least 35% from the worst point (peak 142 ms) |
| **C2** data loss | "Data lost" alarms must fall below 7 (20% of the peak of 35) within 10 minutes |
| **C3** website lookups | No lookup failures for two 5-minute periods in a row |

Type each line, in order. `/advance 5` moves the demo clock 5 minutes forward; the question asks the agent
to check.

| You type | On screen | What it means |
|---|---|---|
| `/advance 5`, then `Is service restored?` | **MONITORING**: C1 latency improved 38% (PASS), C2 packet loss 9 vs limit 7 (PENDING), C3 0 of 2 clean DNS windows (PENDING) | 5 minutes later: delay is better, but data loss and lookups aren't there yet |
| `/advance 5`, then `Status?` | **MONITORING**: C1, C2 PASS, C3 1 of 2 | 10 minutes later: only one clean lookup period so far; it needs two in a row |
| `/advance 5`, then `Status?` | **SERVICE RESTORED**: all pass (latency improved 56%). Next steps: 30-minute soak, update the care advisory, raise a problem record (workaround), fail-back plan, PIR | 15 minutes later: fully recovered, but there's still a 30-minute watch period, and tonight's fix is only temporary |

**Say:** "Many teams would have closed this at minute 5, when the delay looked fine. The manual requires all
three tests, and the tests are calculated by code, not guessed by the AI. And 'restored' isn't 'closed'.
Tonight's fix was temporary, so let's finish the job."

**Problems solved:** 5, declaring victory too early; 6, customer service finds out last.

---

### Step 5 - Close properly and hand over (3 min)

**Story:** the network is back, but the root cause is still there, and the shift is ending. The agent makes
sure the real problem gets fixed later and that the next engineer knows everything.

#### 5a. Close the incident properly

**Type:**
```text
Update the care advisory and raise the problem record.
```
*(In plain words: "Tell customer service it's fixed, and open the follow-up ticket for the root cause.")*

**On screen:**
- Customer service note **v2** published.
- `[tool] create_problem_record` -> **PRB-00001**, containing:
  - root cause: TR-7 evening overload
  - contributing factors: CHG-88412 and +18% traffic
  - permanent fix: for example more capacity on TR-7 and a review of the priority settings
  - temporary fix in place: ACT-REROUTE-TR5
  - lessons-learned meeting (PIR) within 5 working days
- Incident status **RESOLVED** (to be closed after the 30-minute watch period).

**Say:** "Without a follow-up ticket, the same thing happens again next week."

#### 5b. The shift changes

**Say:** "My shift ends. I close the console, and the next engineer opens it."

**Type:** `/exit`, then:
```powershell
python noc_agent.py --resume
```
then:
```text
Give me the shift handover summary for this incident.
```

**On screen:** a summary of the timeline, Nishant's "no" and then "yes", the ECHG and PRB numbers, the
recovery test history, the customer service notes, and the open follow-ups: watch period, undoing the
temporary fix, change board review, lessons-learned meeting.

**Say:** "The conversation is stored in Foundry, so the incident survives restarts and shift changes, and
every decision is on record."

#### 5c. Wrap up

**Say:** "One evening, one agent on Microsoft Foundry. It turned 185 alarms into one problem, found the
cause on evidence, recommended the safe fix, waited for Nishant's approval, told customer service, proved
recovery, and made sure the root cause gets fixed. It used the company's manuals and tools for every fact,
and a person stayed in control of every change. Next steps would be connecting it to real monitoring and
ticketing systems, or splitting it into several specialist agents."

**Type:** `/exit` to quit the agent. You'll see `Agent stopped. Your incident and conversation are saved.`

**Problems solved:** 7, temporary fixes becoming permanent; 8, lost context at shift change.

---

### All prompts on one page (cheat sheet)

Print this or keep it on a second screen. Type each prompt at the `>` prompt, not inside the approval box.

| Step | Type exactly |
|---|---|
| Before | `python noc_agent.py` *(in the terminal)* |
| 1 | Press **Enter** |
| 2 | `Run the diagnostics in runbook order. Is the QoS change last half hour the cause?` |
| 3a | `What do you recommend? Can we just restart the gateway?` |
| 3b | `Proceed.` then in the box: `Nishant`, `n`, `confirm enterprise PE capacity on TR-5 first` |
| 3c | `Transport team confirms TR-5 capacity. Raise it again.` then in the box: `Nishant`, `y`, `TR-5 capacity confirmed by transport team` |
| 4a | `Publish the care advisory and give me the bridge update.` |
| 4b | `/advance 5` then `Is service restored?` |
| 4b | `/advance 5` then `Status?` |
| 4b | `/advance 5` then `Status?` |
| 5a | `Update the care advisory and raise the problem record.` |
| 5b | `/exit`, then `python noc_agent.py --resume`, then `Give me the shift handover summary for this incident.` |
| 5c | `/exit` |

### Reset between rehearsals

- `/reset` inside the session clears the incident and starts a new conversation (the agent is kept).
- `python noc_agent.py` without `--resume` starts the story from the beginning.
- `python noc_agent.py --cleanup` after the event removes the agent version and conversation from Foundry
  (see setup.md). Use it only when you've finished: the next run creates the agent again.

---

## 9. Questions the audience may ask

| Question | Suggested answer |
|---|---|
| Is this connected to a real network? | No. The tools read sample files. In real life each tool would connect to the company's monitoring, ticketing and network-control systems. |
| Could the AI change the network on its own? | No. Every fix needs approval from a named person, enforced by the app, and only fixes from the approved list are possible. |
| Why not just restart the equipment straight away? | A restart disconnects every customer on that equipment at the busiest hour. The manual says try the gentle reroute first. |
| What stops it making up numbers? | Facts come from tools. Its instructions forbid invented numbers, and the recovery tests are calculated by code, not by the AI. |
| Why does it still say MONITORING when the delay looks fine? | All 3 recovery tests must pass, and the website lookup test needs two clean 5-minute periods in a row. |
| How does it know the company's procedures? | Foundry file search over the company's documents, with references in its answers. |
| Would one agent be enough for a real control room? | It's a starting point. You can split the work into specialist agents (alarms, investigation, recovery checks, communications) working together. |
| How does this connect to customer care? | The customer service note is the hand-over to front-office agents, for example a customer-care agent built in Copilot Studio. |
| Do I need telecom knowledge to present this? | No. Use the motorway analogy in section 2 and the word list in section 3. |

## 10. For Foundry trainers: where things are in the code

Use this if participants want to see how it is built. All paths are under `source/`.

| Foundry concept | Where in the code | What to point out |
|---|---|---|
| Prompt agent definition | `noc/agent_definition.py` -> `build_definition()` | `PromptAgentDefinition` with model, instructions, `FileSearchTool` and 10 `FunctionTool`s |
| Create and version the agent | `noc/foundry.py` -> `ensure_agent()` | `project.agents.create_version(...)`; a fingerprint avoids a new version on every run |
| Vector store for file search | `setup_knowledge.py` | `vector_stores.create` + `files.upload_and_poll` (waits for indexing) |
| Conversation (memory) | `noc_agent.py` | `openai_client.conversations.create()`; ID saved in `runs/state.json`; `--resume` reuses it |
| Calling the agent | `noc/foundry.py` -> `agent_openai_client()`; `noc/runner.py` | Requests are bound to the agent by name; `responses.create(conversation=..., input=..., stream=True)` |
| Function-calling loop | `noc/runner.py` -> `run_turn()` | Reads `function_call` items, runs the local tool, returns `function_call_output` in the same conversation |
| Tool schemas | `noc/tool_schemas.py` | Strict JSON schemas (`strict: true`, all properties required) |
| Business rules in tools | `noc/tools.py` | Rules live in code (BLOCKED / INSUFFICIENT_CONFIDENCE / REJECTED), not only in the prompt |
| Human-in-the-loop | `noc/approval.py` + `noc/runner.py` | Approval is requested by the app before `execute_approved_action` runs; the model cannot approve |
| Streaming | `noc/runner.py` -> `_stream()` | Prints `response.output_text.delta` events and `file_search_call` queries |

**Teaching points**
- **Prompt rules vs code rules:** instructions guide the agent, but rules that must never be broken are enforced in the tools.
- **Function tools run on the client:** the portal playground shows the agent but does not run its function calls.
- **Instructions belong to the agent version:** change `INSTRUCTIONS` and the next run creates a new version automatically.

## 11. Is this realistic? (for curious audiences)

Yes. The demo follows how large mobile operators run their control rooms, simplified for training:

| Real-world practice | How the demo shows it |
|---|---|
| Find the real cause among hundreds of side-effect alarms | Router alarms on TR-7 are the cause; the others are side effects |
| Treat any recent change as suspect until explained | The settings change is investigated and judged a contributing factor |
| Try the least disruptive fix first | Reroute before restart |
| Check the spare route can cope before using it | The spare link must stay below 70% busy |
| One change at a time, so you know what worked | No new fix while one is waiting for approval or within 10 minutes of the last |
| Urgent changes need approval, a record and an undo plan | Incident Manager approval, ECHG record, fail-back plan, review by the change board |
| Prove recovery with measurements, then watch for a while | 3 recovery tests, MONITORING status, 30-minute watch period |
| Keep customers and account managers informed | Customer service note with versions; reminders to update the call every 30 minutes and tell account managers |
| Fix the root cause, not just the symptom | A follow-up ticket (problem record) and a lessons-learned meeting |

**What is simplified:** the network data is a fixed sample and the clock is moved by hand. In a real
deployment the tools would connect to live monitoring, ticketing and network-control systems.

## 12. What's in the folder

```text
Foundry/
└── noc-incident-coordinator/
    ├── README.md                  # This guide: story, problems, benefits, demo steps
    ├── setup.md                   # How to install and set up Foundry
    └── source/                    # The code and the sample data
        ├── requirements.txt       # Python packages to install
        ├── .env.example           # Settings template (copy to .env)
        ├── .gitignore
        ├── noc_agent.py           # Starts the demo
        ├── setup_knowledge.py     # One-time: uploads the manuals for the agent to search
        ├── noc/
        │   ├── agent_definition.py  # The agent's instructions and Foundry definition
        │   ├── tool_schemas.py      # Descriptions of the 10 tools
        │   ├── tools.py             # What the tools do, and the safety rules
        │   ├── approval.py          # The approval box
        │   ├── runner.py            # Sends messages to the agent and runs the tools it asks for
        │   ├── foundry.py           # Connection to Foundry and agent versions
        │   └── state.py             # Incident ticket, demo clock, history log
        ├── data/
        │   ├── knowledge/           # Manuals the agent searches: runbook, network notes, approved fixes
        │   └── telemetry/           # Sample network data the tools read: alarms, measurements, checks, impact
        └── tests/
            └── test_offline.py      # 18 checks that run without Azure
```

## 13. Official documentation

- Create a prompt agent: https://learn.microsoft.com/en-us/azure/foundry/agents/quickstarts/prompt-agent
- File search tool: https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/file-search
- Function calling: https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/function-calling