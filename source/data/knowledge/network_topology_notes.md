# AsterWave Mobile - Packet Core and Transport Notes (NET-ARCH-007, v3.0)

## Core sites
- Manila Core (primary), Cebu Core (regional), Davao Core (regional).
- 4G EPC with CUPS. 5G is non-standalone (NSA), so 5G user-plane traffic also runs through the EPC gateways.

## Enterprise APN design
- All enterprise (corporate) APNs are anchored on the centralised enterprise gateway PGW-MNL-ENT-01 in Manila Core.
- Manila enterprise users attach via SGW-MNL-02. Cebu enterprise users attach via SGW-CEB-01, and their
  S5 user-plane traffic is carried over the inter-island backbone to PGW-MNL-ENT-01.
- Enterprise traffic leaves Manila Core towards enterprise VPN / internet peering over the Metro Manila core ring.

## Transport rings
- TR-7: Metro Manila core IP/MPLS ring (PE-MNL-TR7-01/02). Carries enterprise APN egress from PGW-MNL-ENT-01
  AND consumer traffic for Makati CBD and Ortigas cell sites. A TR-7 problem therefore affects Manila AND Cebu
  enterprise users (via the anchored PGW) plus Manila consumer areas.
- TR-5: diverse standby core ring (PE-MNL-TR5-01/02). Normal evening utilisation 35-45%.
  Enterprise APN VRF traffic can be moved to TR-5 by traffic-engineering policy without session drop.
- TR-2: Davao regional ring. Independent of TR-7.
- Capacity planning threshold: a ring must stay below 70% utilisation after any reroute.

## DNS
- Resolvers DNS-MNL-01 (Manila) and DNS-CEB-01 (Cebu). DNS timeouts seen by users are commonly a side effect of
  user-plane congestion upstream; they are a symptom, not a cause, when transport alarms are present.

## Known fault patterns
### FP-TR7-2026 - Evening queue saturation on TR-7
- Trigger: evening peak traffic (typically 18:00-22:00 local) exceeding the TR-7 enterprise queue capacity.
- Evidence: TR-7 egress queue > 85%, interface drops > 1%, LINK_UTIL_HIGH / QUEUE_DROP alarms on PE-MNL-TR7.
- Symptoms: SGW latency alarms, packet-loss bursts, DNS timeouts as side effects.
- First-line workaround: reroute enterprise APN VRF from TR-7 to TR-5 (if TR-5 stays below 70%).
- Escalation: controlled restart of the gateway user-plane process ONLY if queues do not drain 10 minutes after the reroute.
- Expected restoration after reroute: alarm decline within 5-12 minutes.
- Permanent fix belongs in problem management (TR-7 capacity upgrade and QoS profile review).

### FP-QOS-DRIFT - QoS profile change starves enterprise traffic
- Trigger: a QoS / shaping profile change on a ring that reduces the effective share of enterprise traffic.
- Evidence: change in the last 2 hours on the affected ring; degradation starts soon after the change.
- First-line action: roll back the QoS change.

### FP-DNS-RESOLVER - Resolver overload
- Trigger: DNS resolver CPU > 90% with NO upstream transport congestion.
- Symptoms: DNS timeouts only; user-plane latency normal.
- First-line action: flush resolver cache and shift load to the peer resolver.
