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
updated_at: 2026-07-28T19:35:00Z
head: b450fa0f297858b01c02fa1d0a18da40950fd059
branch: develop
pr: 657
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
  - "The merged monitor covers the production portal page, exact fail-closed production auth boundary and isolated exact-image protected API proof while retaining the collector monitor."
  - "The candidate keeps Liquid20 read-only, runs non-root with read-only rootfs, bounded tmpfs, cap-drop ALL, no-new-privileges, 768 MiB and no Docker socket."
  - "Collector and portal failures reconcile through one exact-title GitHub Issue and publish liquidations-live-health commit status."
  - "PR #657 added only a comment to the workflow to force a matching reviewed develop push; exact head 242ed7286824467e13609586804bd2d39e7fde49 passed Freqtrade CI 30392306931 and zizmor 30392307058 with zero review threads."
  - "PR #657 merged with expected-head protection as b450fa0f297858b01c02fa1d0a18da40950fd059, and that merge commit changes .github/workflows/liquidations-live-health.yml."
derived:
  - "No unattended production session is required; production auth is checked directly while protected reads run only in the isolated candidate."
  - "Failure-only artifacts avoid persistent storage growth from healthy five-minute checks."
  - "Because a matching develop push produced no workflow-run record, failure occurs before any job can be assigned to freqtrade-staging; runner health is not yet the first observable gate."
unknown:
  - "Whether the first trusted develop Liquidations Live Health execution reports healthy collector and portal LIVE state."
  - "Whether the workflow is disabled manually, disabled by fork/default settings, or rejected before run creation for another GitHub Actions control-plane reason."
conflicts: []
first_failure:
  marker: TRUSTED_HEALTH_WORKFLOW_NOT_CREATED
  evidence: "GitHub created no Liquidations Live Health workflow run and no liquidations-live-health commit status for the exact matching develop push b450fa0f297858b01c02fa1d0a18da40950fd059."
rejected_hypotheses:
  - "Store or fabricate a real production portal session."
  - "Enable fixture identity in the production portal or weaken SESSION_MISSING."
  - "Mount Liquid20 writable, mount the Docker socket or restart production as part of monitoring."
  - "Upload artifacts for healthy five-minute checks."
  - "Wait only for another cron opportunity; an exact path-matching develop push also created no run."
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
  - command: "AI Platform CI 30385606203, Freqtrade CI 30385606041 and zizmor 30385606274 on 04a01018b9e0b21a3ef5b2746544204c10acbaf0"
    result: PASS
    evidence: "Exact-head platform, repository, Python 3.11-3.14, coverage, formatting, distributions, CI Gate and workflow-security checks succeeded."
  - command: "PR #594 merge"
    result: PASS
    evidence: "Merged exact feature head as develop commit 6179566a37a80d2f8c389b46854d2afb90371587."
  - command: "PR #657 controlled workflow trigger"
    result: PASS
    evidence: "Comment-only workflow change passed Freqtrade CI 30392306931 and zizmor 30392307058, then merged as b450fa0f297858b01c02fa1d0a18da40950fd059."
  - command: "Liquidations Live Health run/status for b450fa0f297858b01c02fa1d0a18da40950fd059"
    result: NOT_RUN
    evidence: "GitHub returned no workflow run and no liquidations-live-health commit status after the exact path-matching develop push."
blockers:
  - marker: GITHUB_ACTIONS_WORKFLOW_STATE_UNAVAILABLE
    evidence: "The available GitHub connector can read jobs and rerun existing jobs but cannot inspect, enable or dispatch this workflow, and no run exists to rerun."
next_action: "In GitHub Actions, inspect and enable Liquidations Live Health if disabled, dispatch it on develop, then record the run ID and terminal collector-and-portal outcome; only if the run queues should freqtrade-staging runner availability be investigated."
```
