---
task_id: FTAI-20260727-liquidations-live-portal-synology-proof
status: completed
branch: develop
base_branch: develop
created: 2026-07-27
updated: 2026-07-28
related_pr: 598
owned_paths:
  - .github/workflows/liquidations-live-portal-synology-proof.yml
  - deploy/synology/portal/prove-liquidations-live.sh
  - tests/ai_platform/portal/deployment/test_liquidations_live_portal_synology_proof.py
  - docs/agents/tasks/FTAI-20260727-liquidations-live-portal-synology-proof.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260727-liquidations-live-stream-repair.md
  - docs/ai_platform/portal/LIQUIDATIONS_LIVE_STREAM_ARCHITECTURE.md
---

# Liquidations live portal Synology proof

The continuous Liquid20 collector and the portal live read path are deployed and proven on Synology. Production authentication remains fail-closed, the Liquid20 mount remains read-only, and the proof uses an isolated candidate created from the exact running portal image.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-28T10:04:00Z
source_head: cf2f4233921f11435ba14b43c2d31183a7a376cb
branch: develop
pr: 598
status: completed
context_routes:
  - docs/agents/tasks/FTAI-20260727-liquidations-live-stream-repair.md
  - docs/ai_platform/portal/LIQUIDATIONS_LIVE_STREAM_ARCHITECTURE.md
owned_paths:
  - .github/workflows/liquidations-live-portal-synology-proof.yml
  - deploy/synology/portal/prove-liquidations-live.sh
  - tests/ai_platform/portal/deployment/test_liquidations_live_portal_synology_proof.py
  - docs/agents/tasks/FTAI-20260727-liquidations-live-portal-synology-proof.md
proven:
  - "PR #529 merged the develop-only portal proof workflow, isolated candidate and bounded evidence contract."
  - "Portal proof run 30340869760 failed closed because this Synology Docker reports an omitted PID limit as JSON null rather than numeric zero."
  - "PR #590 merged the strict PID capability repair as 60f84d1302c8cf8907deff13008da2f120939a4f; unsupported PID cgroups are omitted while the 768 MiB memory limit remains mandatory."
  - "Portal proof run 30346476760 then failed closed with 401 SESSION_MISSING because fixture mode enables the identity provider but does not create a session automatically."
  - "PR #598 merged as cf2f4233921f11435ba14b43c2d31183a7a376cb and uses the existing fixture login contract: require 303, both fixture cookies and a tenant-demo session before authenticated API reads."
  - "The isolated candidate first proves unauthenticated Liquid20 API access is rejected with 401 SESSION_MISSING; production middleware is never bypassed or disabled."
  - "Final trusted develop run 30349018766 completed successfully and uploaded artifact 8684149653 with digest sha256:d075530cd5f70bfcb65db26a1b5531888f6f56d1f7e97313db7001361b52df27."
  - "The final report is bound to commit cf2f4233921f11435ba14b43c2d31183a7a376cb and uses the exact running image local/freqtrade-portal-web:sha-da114a27228e590e8cd348cba60beda4a1331f12."
  - "Production portal remained running as uid 1000 with groups 1000 and 0, restart unless-stopped, /volume1/docker/freqtrade-liquidations/data mounted read-only, and no Docker socket."
  - "Production page returned 200 while unauthenticated health returned 401 SESSION_MISSING with Cache-Control no-store."
  - "The candidate proved fixture_session_validated=true, unauthenticated_api_rejected=true, a read-only real data mount, no Docker socket and PID limit null on the unsupported kernel."
  - "Collector heartbeat advanced from 1785232976071 to 1785232989184 and portal_checked_at_ms advanced from 1785232982881 to 1785232996335 in the same portal process."
  - "Health remained LIVE and active with no failed gates, stale=false, Bybit connected with 660 subscriptions and Binance connected with 526 subscriptions."
  - "The bounded window observed six new real exchange event identifiers; no synthetic event or freshness timestamp was fabricated."
  - "Health, list and summary APIs all returned no-store, the page returned 200, and the deployed bundle contained all three truthful timestamp labels."
  - "research_preview remained true and trading_authorized remained false."
  - "Collector deployment run 30336184269 and artifact 8679367850 already proved the continuous non-root collector, advancing production heartbeat, real events and unchanged accepted historical digest e13709197391082710047088733fc695ac9b99347848f7cc7ce4c8fafb6a8829."
derived:
  - "Fixture identity mode is a test-only identity provider, not an authentication bypass; the official login and session contract is required."
  - "Docker inspect compatibility must use JSON semantics because an unlimited PID value may be null or zero depending on Docker and kernel support."
  - "Portal polling is now independently proven to read the live stream without a portal restart; portal read time remains distinct from collector heartbeat and exchange event time."
  - "Repository E2E remains the authoritative 390 px layout proof; Synology evidence proves the deployed bundle and live data path."
unknown:
  - "Future exchange availability, symbol-universe changes and upstream WebSocket protocol changes remain operational monitoring concerns, not completion blockers."
conflicts: []
first_failure:
  marker: PORTAL_PROOF_CHAIN_RESOLVED
  evidence: "The PID null representation and missing fixture session failures were isolated, repaired through PRs #590 and #598, and superseded by successful trusted develop run 30349018766."
rejected_hypotheses:
  - "Disable or bypass production authentication."
  - "Treat fixture mode as an implicit authenticated session."
  - "Mount the Docker socket into the portal candidate."
  - "Make the Liquid20 data mount writable."
  - "Force unsupported PID cgroup controls."
  - "Treat portal request time as market-event freshness."
changed_paths:
  - .github/workflows/liquidations-live-portal-synology-proof.yml
  - deploy/synology/portal/prove-liquidations-live.sh
  - tests/ai_platform/portal/deployment/test_liquidations_live_portal_synology_proof.py
  - docs/agents/tasks/FTAI-20260727-liquidations-live-portal-synology-proof.md
validation:
  - command: "Collector Synology deployment run 30336184269"
    result: PASS
    evidence: "Artifact 8679367850 proves candidate and production collector readiness, source connectivity, heartbeat advancement, real events and historical digest immutability."
  - command: "PR #598 exact-head AI Platform CI run 30347792790"
    result: PASS
    evidence: "AI platform tests, lint, formatting and contract validation completed successfully."
  - command: "PR #598 exact-head Freqtrade CI run 30347792786"
    result: PASS
    evidence: "Pre-commit, Python 3.11-3.14 matrix, full Python 3.12 coverage, distributions and CI Gate completed successfully."
  - command: "PR #598 exact-head zizmor run 30347792815"
    result: PASS
    evidence: "GitHub Actions security analysis completed successfully."
  - command: "Isolated pre-merge Synology proof run 30347857431"
    result: PASS
    evidence: "Artifact 8683683106 proved the official fixture-session path before merge."
  - command: "Trusted develop portal proof run 30349018766"
    result: PASS
    evidence: "Artifact 8684149653 is bound to cf2f4233921f11435ba14b43c2d31183a7a376cb and proves production boundaries, live reads, heartbeat advancement, truthful timestamps and real events."
  - command: "PR #598 review-thread query"
    result: PASS
    evidence: "No review threads were returned before merge."
blockers: []
next_action: "Continue normal monitoring of collector heartbeat freshness, source connectivity, portal LIVE/STALE/OFFLINE transitions and the existing Liquid20 operational alerts."
```
