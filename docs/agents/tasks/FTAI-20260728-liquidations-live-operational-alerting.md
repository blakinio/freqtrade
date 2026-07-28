---
task_id: FTAI-20260728-liquidations-live-operational-alerting
status: validating
branch: fix/liquidations-live-health-status-20260728
base_branch: develop
created: 2026-07-28
updated: 2026-07-28
related_pr: 594
required_reads:
  - docs/agents/tasks/FTAI-20260727-liquidations-live-stream-repair.md
  - docs/agents/tasks/FTAI-20260727-liquidations-live-portal-synology-proof.md
  - deploy/synology/liquid20/LIVE_STREAM.md
search_first:
  - .github/workflows/liquidations-live-health.yml
  - ai_platform/scripts/liquidation_live_health.py
  - ai_platform/scripts/liquidation_portal_health.py
  - tests/ai_platform_integration/test_liquidation_live_health.py
  - tests/ai_platform_integration/test_liquidation_portal_health.py
---

# FTAI-20260728-liquidations-live-operational-alerting

Provide autonomous fail-closed monitoring for both the completed Synology Liquid20 collector and the production portal read path without modifying collector data, accepted historical evidence, production authentication or trading state.

## Context checkpoint

```yaml
checkpoint_version: 2
updated_at: 2026-07-28T11:10:00Z
head: pending
branch: fix/liquidations-live-health-status-20260728
pr: 594
status: validating
context_routes:
  - docs/agents/tasks/FTAI-20260728-liquidations-live-operational-alerting.md
  - .github/workflows/liquidations-live-health.yml
  - ai_platform/scripts/liquidation_live_health.py
  - ai_platform/scripts/liquidation_portal_health.py
  - deploy/synology/liquid20/LIVE_STREAM.md
  - tests/ai_platform_integration/test_liquidation_live_health.py
  - tests/ai_platform_integration/test_liquidation_portal_health.py
owned_paths:
  - .github/workflows/liquidations-live-health.yml
  - ai_platform/scripts/liquidation_portal_health.py
  - deploy/synology/liquid20/LIVE_STREAM.md
  - tests/ai_platform_integration/test_liquidation_live_health.py
  - tests/ai_platform_integration/test_liquidation_portal_health.py
  - docs/agents/tasks/FTAI-20260728-liquidations-live-operational-alerting.md
proven:
  - "PR #578 merged the recurring five-minute collector monitor, deduplicated GitHub Issue lifecycle and failure-only evidence retention."
  - "The collector monitor evaluates container state, live-state contract, active run, collector/source heartbeat freshness, configured connected subscriptions, data-only safety and disk capacity."
  - "PR #594 publishes pending/final liquidations-live-health commit statuses with minimal statuses: write permission."
  - "The extension keeps production authentication fail-closed: the public page must return 200 and the protected production health API must return exact 401 SESSION_MISSING with no-store."
  - "Protected health/list/summary reads reuse the existing terminally proven portal proof script and its isolated candidate created from the exact production image and image ID."
  - "The candidate uses the real Liquid20 root read-only, non-root identity, read-only root filesystem, bounded tmpfs, cap-drop ALL, no-new-privileges, 768 MiB memory, no restart and no Docker socket."
  - "Fixture identity and its ephemeral cookies remain confined to the existing candidate-local proof process and are never written to JSON, issue bodies or artifacts."
  - "The combined monitor records and alerts on portal LIVE, STALE, OFFLINE or unexpected HISTORICAL state and validates Bybit/Binance connectivity, subscriptions, event counts and no-store API behavior."
  - "Collector and portal failures reconcile through the same exact-title deduplicated GitHub Issue."
derived:
  - "A real unattended production session is neither required nor fabricated; the production auth boundary is checked directly while protected read behavior is exercised in an isolated exact-image candidate."
  - "Using the exact deployed image and real read-only data detects deployed bundle/read-model regressions without restarting or modifying the production portal."
  - "Failure-only artifact retention prevents five-minute healthy runs from consuming unnecessary Actions storage."
unknown:
  - "Whether exact-head repository CI and zizmor accept the extended workflow, wrapper and tests."
  - "Whether the first trusted develop run reports portal mode LIVE and closes any pre-existing deduplicated health issue."
conflicts: []
first_failure:
  marker: PORTAL_OPERATIONAL_MONITORING_GAP
  evidence: "The merged monitor covered the collector and data root but did not execute the deployed portal read model or alert on LIVE/STALE/OFFLINE transitions."
rejected_hypotheses:
  - "Store or fabricate a real production portal session."
  - "Enable fixture identity in the production portal."
  - "Bypass or weaken SESSION_MISSING."
  - "Mount Liquid20 writable or mount the Docker socket inside the portal candidate."
  - "Restart or replace the production portal as part of monitoring."
  - "Upload artifacts for healthy five-minute checks."
changed_paths:
  - .github/workflows/liquidations-live-health.yml
  - ai_platform/scripts/liquidation_portal_health.py
  - deploy/synology/liquid20/LIVE_STREAM.md
  - tests/ai_platform_integration/test_liquidation_live_health.py
  - tests/ai_platform_integration/test_liquidation_portal_health.py
  - docs/agents/tasks/FTAI-20260728-liquidations-live-operational-alerting.md
validation:
  - command: "bash -n deploy/synology/portal/prove-liquidations-live.sh"
    result: PASS
    evidence: "The existing trusted portal proof script remains unchanged and passed shell syntax validation in its terminal proof task."
  - command: "pytest -q tests/ai_platform_integration/test_liquidation_portal_health.py"
    result: PASS
    evidence: "Six isolated contract tests passed against the combined wrapper, workflow and existing proof-script contract."
  - command: "python -m py_compile ai_platform/scripts/liquidation_portal_health.py"
    result: PASS
    evidence: "The combined monitoring wrapper compiled successfully."
  - command: "exact-head PR #594 CI and zizmor"
    result: NOT_RUN
    evidence: "Awaiting the updated exact head."
  - command: "first trusted develop Liquidations Live Health workflow"
    result: NOT_RUN
    evidence: "Runs after reviewed merge."
blockers: []
next_action: "Require green exact-head PR #594 CI/security and zero review threads, merge, then verify one terminal trusted five-minute collector-and-portal health run."
```
