---
task_id: FTAI-20260727-liquidations-live-portal-synology-proof
status: completed
branch: develop
base_branch: develop
created: 2026-07-27
updated: 2026-07-28
related_pr: 603
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

The continuous Liquid20 collector and the portal live read path are deployed and terminally proven on Synology. Production authentication remains fail-closed, the Liquid20 mount remains read-only, and the proof uses an isolated candidate created from the exact running portal image.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-28T10:41:42Z
source_head: e58c64b5a4267dbb0749838f18c06e4ac379f40d
branch: develop
pr: 603
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
  - "PR #529 merged the develop-only portal proof workflow, isolated candidate and bounded evidence contract as 9ff7717cde0127c12a9cb9da576599f4bbdf6954."
  - "Portal proof run 30340869760 failed closed because this Synology kernel does not expose a usable Docker PID cgroup limit."
  - "PR #590 merged the strict PID capability repair as 60f84d1302c8cf8907deff13008da2f120939a4f; unsupported PID cgroups are omitted while the 768 MiB memory limit remains mandatory."
  - "Portal proof run 30346476760 then failed closed with 401 SESSION_MISSING because fixture mode enables the identity provider but does not create a session automatically."
  - "PR #598 merged as cf2f4233921f11435ba14b43c2d31183a7a376cb and uses the existing fixture login contract: require 303, both fixture cookies and a tenant-demo session before authenticated API reads."
  - "PR #603 merged the complete evidence contract as e58c64b5a4267dbb0749838f18c06e4ac379f40d."
  - "Final trusted develop workflow run 30351520306, job 90249872929, completed successfully for exact merge SHA e58c64b5a4267dbb0749838f18c06e4ac379f40d."
  - "Artifact 8685112651 has digest sha256:602d9d0ae9ea7ac479efc37886fcef563f9d834020d58612c3989e0ce6043525 and contains only the bounded JSON report and log."
  - "The final report result is success with rejection_reason null and uses the exact running image local/freqtrade-portal-web:sha-da114a27228e590e8cd348cba60beda4a1331f12 with image ID sha256:57bd9b2a9a40e770b0fca1e16177d3ad2f2e8448b7d08827762c80173cfca4ff."
  - "Production portal remained running as uid 1000 with groups 1000 and 0, restart unless-stopped, /volume1/docker/freqtrade-liquidations/data mounted read-only, and no Docker socket."
  - "Production page returned 200 while unauthenticated health returned exactly 401 SESSION_MISSING with Cache-Control no-store."
  - "The isolated candidate ran as uid 1000 with groups 1000 and 0, exact production image and image ID, restart no, read-only root filesystem, only /tmp and /app/.next/cache tmpfs, cap-drop ALL, no-new-privileges, 768 MiB memory limit, read-only real-data mount and no Docker socket."
  - "The candidate first proved unauthenticated Liquid20 API access is rejected with 401 SESSION_MISSING, then validated the fixture-only session without weakening production authentication."
  - "Collector heartbeat advanced from 1785235192468 to 1785235208372 and portal_checked_at_ms advanced from 1785235200621 to 1785235215092 in the same candidate process."
  - "Health remained LIVE and active with no failed gates and stale=false."
  - "Bybit remained connected with 660 subscriptions and event count advanced from 671 to 672."
  - "Binance remained connected with 526 subscriptions and event count advanced from 2201 to 2209."
  - "Combined source event count advanced from 2872 to 2881; real_exchange_event_present and event_count_advanced_during_observation are true, with eleven new real event identifiers in the bounded window."
  - "Health, list and summary APIs returned 200 with Cache-Control no-store, the page returned 200, and the deployed bundle contained all three truthful timestamp labels."
  - "research_preview remained true and trading_authorized remained false."
  - "Credential audit found no cookie, token, authorization header or session-payload pattern in the JSON report or bounded log."
  - "Collector deployment run 30336184269 and artifact 8679367850 remain authoritative for the continuous non-root collector at exact SHA b6f4589ff4da88a9cbd91342c657de6b57def142."
  - "Collector checkpoint PR #572 remains merged as 9ceb684a5114faac44c45081e45d0627f85d9512."
  - "The accepted historical digest remains unchanged at e13709197391082710047088733fc695ac9b99347848f7cc7ce4c8fafb6a8829."
derived:
  - "Fixture identity mode is a test-only identity provider, not an authentication bypass; the official login and session contract is required."
  - "Docker inspect compatibility must use JSON semantics because an unlimited PID value may be null or zero depending on Docker and kernel support."
  - "Portal polling is independently proven to read the continuous live stream without restarting or modifying the production portal."
  - "Exchange event time, collector receive/heartbeat time and portal observation time remain distinct and are represented by truthful deployed-bundle labels."
unknown:
  - "Future exchange availability, symbol-universe changes and upstream WebSocket protocol changes remain operational monitoring concerns, not completion blockers."
conflicts: []
first_failure:
  marker: PORTAL_PROOF_CHAIN_RESOLVED
  evidence: "The unsupported PID cgroup, missing fixture session and incomplete artifact-evidence failures were isolated, repaired through PRs #590, #598 and #603, and superseded by successful exact-merge run 30351520306."
rejected_hypotheses:
  - "Disable or bypass production authentication."
  - "Treat fixture mode as an implicit authenticated session."
  - "Mount the Docker socket into the portal candidate."
  - "Make the Liquid20 data mount writable."
  - "Force unsupported PID cgroup controls."
  - "Treat portal request time as market-event freshness."
  - "Mark the task complete from a successful workflow whose artifact omits required runtime evidence."
changed_paths:
  - .github/workflows/liquidations-live-portal-synology-proof.yml
  - deploy/synology/portal/prove-liquidations-live.sh
  - tests/ai_platform/portal/deployment/test_liquidations_live_portal_synology_proof.py
  - docs/agents/tasks/FTAI-20260727-liquidations-live-portal-synology-proof.md
validation:
  - command: "bash -n deploy/synology/portal/prove-liquidations-live.sh"
    result: PASS
    evidence: "The final proof script passed shell syntax validation before PR #603 merge."
  - command: "Focused pytest tests/ai_platform/portal/deployment/test_liquidations_live_portal_synology_proof.py"
    result: PASS
    evidence: "Seven focused deployment-contract tests passed before PR #603 merge."
  - command: "PR #603 exact-head AI Platform CI run 30350345442"
    result: PASS
    evidence: "AI Platform tests, Ruff check, Ruff format and contract validation completed successfully."
  - command: "PR #603 exact-head Freqtrade CI run 30350345487"
    result: PASS
    evidence: "CI scope, repository pre-commit, Python 3.11-3.14 matrix, full Python 3.12 coverage and distribution build completed successfully."
  - command: "PR #603 exact-head zizmor run 30350345645"
    result: PASS
    evidence: "GitHub Actions security analysis completed successfully."
  - command: "PR #603 changed-path audit"
    result: PASS
    evidence: "The repair PR changed only deploy/synology/portal/prove-liquidations-live.sh and tests/ai_platform/portal/deployment/test_liquidations_live_portal_synology_proof.py."
  - command: "PR #603 review-thread audit"
    result: PASS
    evidence: "Zero review threads were returned before merge."
  - command: "Trusted develop portal proof run 30351520306"
    result: PASS
    evidence: "Job 90249872929 and artifact 8685112651 are bound to e58c64b5a4267dbb0749838f18c06e4ac379f40d and prove complete production, candidate, heartbeat, source, event, cache-control and deployed-bundle evidence."
blockers: []
next_action: "Continue standard operational monitoring of Liquid20 heartbeat freshness, exchange connectivity and portal LIVE/STALE/OFFLINE transitions."
```
