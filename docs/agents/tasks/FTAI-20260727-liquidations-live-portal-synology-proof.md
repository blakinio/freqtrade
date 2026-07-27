---
task_id: FTAI-20260727-liquidations-live-portal-synology-proof
status: implementation-complete-ci-pending
branch: test/liquidations-live-portal-synology-proof-20260727
base_branch: develop
created: 2026-07-27
updated: 2026-07-27
related_pr: pending
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
updated_at: 2026-07-27T20:25:00Z
head: 7325cfecf65f31f3a3a497fb6fbaf41c4ec9df63
branch: test/liquidations-live-portal-synology-proof-20260727
pr: pending
status: implementation-complete-ci-pending
context_routes:
  - docs/agents/tasks/FTAI-20260727-liquidations-live-stream-repair.md
  - docs/ai_platform/portal/LIQUIDATIONS_LIVE_STREAM_ARCHITECTURE.md
owned_paths:
  - .github/workflows/liquidations-live-portal-synology-proof.yml
  - deploy/synology/portal/prove-liquidations-live.sh
  - tests/ai_platform/portal/deployment/test_liquidations_live_portal_synology_proof.py
  - docs/agents/tasks/FTAI-20260727-liquidations-live-portal-synology-proof.md
proven:
  - Production portal authentication must remain enabled and unauthenticated Liquid20 APIs return 401 SESSION_MISSING.
  - Full live API proof can be performed without weakening production by using the exact running portal image in an isolated candidate with explicit test-only fixture identity.
  - The candidate receives the real Synology Liquid20 root read-only and no Docker socket.
  - Two observations prove collector heartbeat and portal read time advance in the same portal process.
  - The proof requires LIVE active state, Bybit and Binance connections, dynamic subscriptions, no-store APIs and no trading authority.
  - A quiet exchange window is labelled honestly instead of fabricating a real event.
derived:
  - Repository E2E remains the authoritative 390 px layout proof; Synology proof validates the deployed image bundle contains all three truthful timestamp labels.
unknown:
  - Real operational result until the reviewed workflow reaches develop after the collector is live.
conflicts: []
first_failure:
  marker: OPERATIONAL_PROOF_NOT_YET_RUN
  evidence: The package is repository-only until merged after successful collector deployment.
rejected_hypotheses:
  - Disable or bypass production authentication.
  - Mount the Docker socket into the portal candidate.
  - Make the portal data mount writable.
  - Treat the portal request timestamp as event freshness.
changed_paths:
  - .github/workflows/liquidations-live-portal-synology-proof.yml
  - deploy/synology/portal/prove-liquidations-live.sh
  - tests/ai_platform/portal/deployment/test_liquidations_live_portal_synology_proof.py
  - docs/agents/tasks/FTAI-20260727-liquidations-live-portal-synology-proof.md
validation:
  - command: exact-head repository CI and security analysis
    result: PENDING
    evidence: Required before merge.
blockers:
  - Continuous collector deployment must succeed first.
  - Exact-head CI and review are pending.
next_action: After the collector deployment is proven, synchronize this branch with develop, pass exact-head CI, merge and collect the uploaded Synology proof artifact.
```
