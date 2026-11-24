# AsterWave NOC Runbook - Incident Correlation, Restoration and Service Assurance (RB-NOC-014, v3.0)

## 1. Correlation logic
1. Transport alarms on a ring (LINK_UTIL_HIGH, QUEUE_DROP) are probable-cause alarms.
2. SGW latency and packet-loss alarms that co-occur within 15 minutes on the same ring are symptom alarms of the
   SAME parent incident.
3. DNS timeout alarms overlapping the same window are downstream symptoms; do not open a separate incident.
4. Alarms on a different ring are NOT part of the parent incident unless they share the same gateway.
5. Prioritise enterprise APN impact in the severity score.

## 2. Severity
- SEV1: enterprise APN impacted AND more than one region affected (or more than 10 enterprise SLA accounts).
- SEV2: enterprise APN impacted in one region, OR consumer impact in more than one region.
- SEV3: everything else.
- SEV1/SEV2 require an Incident Manager to be assigned within 5 minutes and a bridge to be opened.

## 3. Diagnostics sequence (run in this order)
1. queue_depth - transport queue depth and interface drops on the affected path.
2. gateway_restarts - gateway process restart history in the last 30 minutes.
3. change_log - route-policy / QoS / software changes on the affected path in the last 2 hours.
   Any change on the affected path is suspect until it is explained.
4. kpi_baseline - current KPIs against the 24-hour and same-day-last-week baselines.
5. standby_capacity - projected utilisation of the standby path BEFORE any reroute.
A fault pattern may only be declared after checks 1, 3 and 5 support it. State confidence 0-1.
Below 0.60 confidence, do not propose a network action; continue diagnostics.

## 4. Restoration actions and change control
- Only actions in the Approved Action Catalog may be proposed.
- ONE change at a time: do not propose a new action while another is pending approval, or within 10 minutes of the
  last executed action (its effect must be measurable first).
- Every action during an incident is an EMERGENCY CHANGE. It needs Incident Manager approval (SEV1/SEV2) and an
  emergency change record (ECHG). Emergency changes are reviewed retrospectively by the CAB within 2 working days.
- Workarounds (for example a reroute) must have a fail-back plan, executed later as a planned change off-peak.

## 5. Recovery criteria (ALL three must pass)
- C1: User-plane latency improves by >= 35% versus the incident peak.
- C2: Packet-loss alarms drop below 20% of peak within 10 minutes of the action.
- C3: No DNS timeout bursts in two consecutive 5-minute windows.
If C1 and C2 pass but C3 does not yet, the status is MONITORING.
When all pass, the status is SERVICE RESTORED. The incident stays open for a 30-minute soak period before closure.

## 6. Communications
- SEV1: bridge status update every 30 minutes (impact, actions, next update time).
- Enterprise SLA accounts: notify key account management within 30 minutes of SEV1 declaration.
- Care advisory: publish for front-office care once impact is confirmed, and update it at restoration.
  Customer wording must not contain internal node or ring names. The Incident Manager owns external wording.

## 7. Problem management
- If the restoration was a workaround or the root cause is not permanently fixed, raise a problem record (PRB)
  before closing the incident, including root cause, contributing factors and the permanent fix proposal.
- A post-incident review (PIR) is required for every SEV1 within 5 working days.
