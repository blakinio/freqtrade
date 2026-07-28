---
task_id: FTAI-20260727-liquidations-live-portal-synology-proof
status: collector-prerequisite-proven-ci-pending
branch: test/liquidations-live-portal-synology-proof-20260727
base_branch: develop
created: 2026-07-27
updated: 2026-07-28
related_pr: 529
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

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-28T07:34:00Z
head_before_checkpoint_refresh: 8b0a20814b25e98955c92a86f9fc6b0521ffa455
branch: test/liquidations-live-portal-synology-proof-20260727
pr: 529
status: collector-prerequisite-proven-ci-pending
context_routes:
  - docs/agents/tasks/FTAI-20260727-liquidations-live-stream-repair.md
  - docs/ai_platform/portal/LIQUIDATIONS_LIVE_STREAM_ARCHITECTURE.md
owned_paths:
  - .github/workflows/liquidations-live-portal-synology-proof.yml
  - deploy/synology/portal/prove-liquidations-live.sh
  - tests/ai_platform/portal/deployment/test_liquidations_live_portal_synology_proof.py
  - docs/agents/tasks/FTAI-20260727-liquidations-live-portal-synology-proof.md
proven:
  - Collector deployment commit b6f4589ff4da88a9cbd91342c657de6b57def142 completed successfully in Actions run 30336184269.
  - Collector operational artifact 8679367850 proves LIVE active state, advancing heartbeat and real public liquidation events.
  - Bybit and Binance are connected with 655 and 526 dynamic subscriptions respectively.
  - Accepted historical evidence digest remained unchanged across deployment.
  - Collector and portal proof retain research-preview mode with trading_authorized false.
  - Production portal authentication must remain enabled and unauthenticated Liquid20 APIs return 401 SESSION_MISSING.
  - Full live API proof can be performed without weakening production by using the exact running portal image in an isolated candidate with explicit test-only fixture identity.
  - The candidate receives the real Synology Liquid20 root read-only and no Docker socket.
  - Two observations prove collector heartbeat and portal read time advance in the same portal process.
  - The proof requires LIVE active state, Bybit and Binance connections, dynamic subscriptions and no-store APIs.
  - A quiet exchange window is labelled honestly instead of fabricating a real event.
  - Synology does not support the PID cgroup limit used by the original proof candidate; the script now probes capability strictly, omits only the unsupported PID argument and retains the 768 MiB memory limit.
derived:
  - Repository E2E remains the authoritative 390 px layout proof; Synology proof validates the deployed image bundle contains all three truthful timestamp labels.
unknown:
  - Final portal operational result until the reviewed workflow reaches develop.
conflicts: []
first_failure:
  marker: OPERATIONAL_PROOF_NOT_YET_RUN
  evidence: The portal proof package is repository-only until merged after exact-head CI.
rejected_hypotheses:
  - Disable or bypass production authentication.
  - Mount the Docker socket into the portal candidate.
  - Make the portal data mount writable.
  - Treat the portal request timestamp as event freshness.
  - Force an unsupported PID cgroup limit on the Synology candidate.
changed_paths:
  - .github/workflows/liquidations-live-portal-synology-proof.yml
  - deploy/synology/portal/prove-liquidations-live.sh
  - tests/ai_platform/portal/deployment/test_liquidations_live_portal_synology_proof.py
  - docs/agents/tasks/FTAI-20260727-liquidations-live-portal-synology-proof.md
validation:
  - command: collector Synology deployment run 30336184269
    result: PASS
    evidence: artifact 8679367850
  - command: bash -n deploy/synology/portal/prove-liquidations-live.sh
    result: PASS
    evidence: self-removing PID capability repair workflow
  - command: exact-head repository CI and security analysis
    result: PENDING
    evidence: Required before merge.
blockers:
  - Exact-head CI and review are pending.
next_action: Pass exact-head CI, merge PR 529 and collect the uploaded Synology portal proof artifact.
```
