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
checkpoint_version: 1
updated_at: 2026-07-28T17:52:00Z
head: 8191bf14e5024d876533d6e236648b934c768255
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
  - "PR #594 extends the same monitor to the production portal page, fail-closed production auth boundary and isolated exact-image protected API proof."
  - "The candidate keeps Liquid20 read-only, runs non-root with read-only rootfs, bounded tmpfs, cap-drop ALL, no-new-privileges, 768 MiB and no Docker socket."
  - "Collector and portal failures reconcile through one exact-title GitHub Issue and publish liquidations-live-health commit status."
  - "Implementation head f9c1b74bf30002efa090668d95467fecd6b32f1b passed AI Platform CI 30360553463, Freqtrade CI 30360553340 and zizmor 30360551180."
  - "PR #594 is synchronized with develop 31c61fdab351521c275687e4751682ef935407f9, mergeable, draft, has six changed paths and zero review threads."
derived:
  - "No unattended production session is required; production auth is checked directly while protected reads run only in the isolated candidate."
  - "Failure-only artifacts avoid persistent storage growth from healthy five-minute checks."
unknown:
  - "Whether AI Platform CI 30384713787 and Freqtrade CI 30384710124 finish green on checkpoint head 8191bf14e5024d876533d6e236648b934c768255."
  - "Whether the first trusted develop Liquidations Live Health run reports healthy collector and portal LIVE state."
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
  - command: "AI Platform CI 30360553463 and Freqtrade CI 30360553340 on f9c1b74bf30002efa090668d95467fecd6b32f1b"
    result: PASS
    evidence: "Platform tests, Ruff, formatting, codespell, Python 3.11-3.14, coverage, pre-commit, distributions and CI Gate succeeded."
  - command: "zizmor 30384709951 on 8191bf14e5024d876533d6e236648b934c768255"
    result: PASS
    evidence: "Exact-head workflow security analysis succeeded."
  - command: "AI Platform CI 30384713787 and Freqtrade CI 30384710124 on 8191bf14e5024d876533d6e236648b934c768255"
    result: NOT_RUN
    evidence: "Both exact-head workflows are in progress."
  - command: "first trusted develop Liquidations Live Health workflow"
    result: NOT_RUN
    evidence: "Requires reviewed merge."
blockers: []
next_action: "Require green exact-head AI Platform and Freqtrade CI, recheck mergeability and zero review threads, mark PR #594 ready, merge with expected-head protection, then verify one terminal trusted five-minute collector-and-portal health run."
```
