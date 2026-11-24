# AsterWave NOC Approved Action Catalog (ACT-CAT, v3.0)

| Action ID | Fault pattern | Action | Risk | Precondition | Approval |
| --- | --- | --- | --- | --- | --- |
| ACT-REROUTE-TR5 | FP-TR7-2026 | Move enterprise APN VRF traffic from TR-7 to TR-5 by traffic-engineering policy (no session drop) | Medium | standby_capacity check shows TR-5 stays below 70% | Incident Manager (emergency change) |
| ACT-GW-RESTART | FP-TR7-2026 | Controlled restart of the affected gateway user-plane process (drops active sessions on that process) | High | ACT-REROUTE-TR5 executed and service NOT restored 10 minutes later | Incident Manager (emergency change) |
| ACT-QOS-ROLLBACK | FP-QOS-DRIFT | Roll back the most recent QoS / shaping profile change on the affected ring | Low | change_log check identifies the change | Incident Manager (emergency change) |
| ACT-DNS-FAILOVER | FP-DNS-RESOLVER | Flush resolver cache and shift 50% of queries to the peer resolver | Low | No transport congestion on the path | Incident Manager (emergency change) |

Every action needs human approval before execution. Each workaround needs a fail-back plan.
