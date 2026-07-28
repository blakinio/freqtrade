---
task_id: FTAI-20260728-liquidations-live-operational-alerting
status: validating
branch: develop
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
checkpoint_version: 1
updated_at: 2026-07-28T18:46:59Z
head: 6179566a37a80d2f8c389b46854d2afb90371587
branch: develop
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
  - "PR #594 merged exact validated feature head 04a01018b9e0b21a3ef5b2746544204c10acbaf0 into develop as 6179566a37a80d2f8c389b46854d2afb90371587."
  - "Exact feature head 04a01018b9e0b21a3ef5b2746544204c10acbaf0 passed AI Platform CI 30385606203, Freqtrade CI 30385606041 and zizmor 30385606274."
  - "PR #594 had the expected six changed paths and zero review threads before merge."
  - "The merged monitor covers the production portal page, exact fail-closed production auth boundary and isolated exact-image protected API proof while retaining the collector monitor."
  - "The candidate keeps Liquid20 read-only, runs non-root with read-only rootfs, bounded tmpfs, cap-drop ALL, no-new-privileges, 768 MiB and no Docker socket."
  - "Collector and portal failures reconcile through one exact-title GitHub Issue and publish liquidations-live-health commit status."
  - "Current develop f2431821f29878f3308469e035cba0f70d933b05 contains merge commit 6179566a37a80d2f8c389b46854d2afb90371587."
derived:
  - "No unattended production session is required; production auth is checked directly while protected reads run only in the isolated candidate."
  - "Failure-only artifacts avoid persistent storage growth from healthy five-minute checks."
unknown:
  - "Whether the first trusted develop Liquidations Live Health execution reports healthy collector and portal LIVE state."
  - "Why no pending liquidations-live-health status was published during the observed 18:30, 18:35 or 18:45 UTC scheduling opportunities."
conflicts: []
first_failure:
  marker: PORTAL_OPERATIONAL_MONITORING_GAP
  evidence: "The merged monitor covered the collector and data root but did not execute the deployed portal read model or alert on LIVE/STALE/OFFLINE transitions."
rejected_hypotheses:
  - "Store or fabricate a real production portal session."
  - "Enable fixture identity in the production portal or weaken SESSION_MISSING."
  - "Mount Liquid20 writable, mount the Docker socket or restart production as part of monitoring."
  - "Upload artifacts for healthy five-minute checks."
changed_paths:
  - .github/workflows/liquidations-live-health.yml
  - ai_platform/scripts/liquidation_portal_health.py
  - deploy/synology/liquid20/LIVE_STREAM.md
  - tests/ai_platform_integration/test_liquidation_live_health.py
  - tests/ai_platform_integration/test_liquidation_portal_health.py
  - docs/agents/tasks/FTAI-20260728-liquidations-live-operational-alerting.md
validation:
  - command: "python -m py_compile ai_platform/scripts/liquidation_portal_health.py"
    result: PASS
    evidence: "Portal monitoring wrapper compiled successfully."
  - command: "pytest -q tests/ai_platform_integration/test_liquidation_portal_health.py"
    result: PASS
    evidence: "Six isolated portal-monitor contract tests passed."
  - command: "AI Platform CI 30385606203 on 04a01018b9e0b21a3ef5b2746544204c10acbaf0"
    result: PASS
    evidence: "Exact-head platform tests, Ruff, formatting, codespell and JSON validation succeeded."
  - command: "Freqtrade CI 30385606041 on 04a01018b9e0b21a3ef5b2746544204c10acbaf0"
    result: PASS
    evidence: "Python 3.11-3.14, coverage, pre-commit, documentation, distributions and CI Gate succeeded."
  - command: "zizmor 30385606274 on 04a01018b9e0b21a3ef5b2746544204c10acbaf0"
    result: PASS
    evidence: "Exact-head workflow security analysis succeeded."
  - command: "PR #594 merge"
    result: PASS
    evidence: "Merged exact feature head 04a01018b9e0b21a3ef5b2746544204c10acbaf0 as develop commit 6179566a37a80d2f8c389b46854d2afb90371587."
  - command: "trusted develop liquidations-live-health status through 2026-07-28T18:46:59Z"
    result: NOT_RUN
    evidence: "GitHub returned no pending or terminal liquidations-live-health status on merge commit 6179566a37a80d2f8c389b46854d2afb90371587 or current develop f2431821f29878f3308469e035cba0f70d933b05 after the observed 18:30, 18:35 and 18:45 UTC scheduling opportunities."
blockers:
  - marker: TRUSTED_HEALTH_RUN_NOT_PUBLISHED
    evidence: "No pending or terminal liquidations-live-health commit status was observable, so collector and portal production health cannot be concluded."
next_action: "Obtain one terminal trusted Liquidations Live Health execution on current develop; if no pending status appears, inspect the freqtrade-staging runner and workflow queue first, then record the run ID and terminal collector-and-portal outcome."
```
