---
task_id: FTAI-20260728-liquidations-live-operational-alerting
status: validating
branch: develop
base_branch: develop
created: 2026-07-28
updated: 2026-07-29
related_pr: 689
required_reads:
  - docs/agents/tasks/FTAI-20260727-liquidations-live-stream-repair.md
  - docs/agents/tasks/FTAI-20260727-liquidations-live-portal-synology-proof.md
  - deploy/synology/liquid20/LIVE_STREAM.md
search_first:
  - .github/workflows/liquidations-live-operational-health.yml
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
updated_at: 2026-07-29T14:03:00Z
head: 79e4897263a0e9a8f938500d5743b11e808d4525
branch: develop
pr: 689
status: validating
context_routes:
  - docs/agents/tasks/FTAI-20260728-liquidations-live-operational-alerting.md
  - .github/workflows/liquidations-live-operational-health.yml
  - ai_platform/scripts/liquidation_live_health.py
  - ai_platform/scripts/liquidation_portal_health.py
  - deploy/synology/liquid20/LIVE_STREAM.md
  - tests/ai_platform_integration/test_liquidation_live_health.py
  - tests/ai_platform_integration/test_liquidation_portal_health.py
owned_paths:
  - .github/workflows/liquidations-live-operational-health.yml
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
  - "PR #657 forced a reviewed matching develop push and passed Freqtrade CI 30392306931 and zizmor 30392307058."
  - "PR #689 recreated the workflow under .github/workflows/liquidations-live-operational-health.yml, quoted the top-level on key and updated the self-path trigger while preserving runner, permissions, health checks and fail-closed behavior."
  - "PR #693 synchronized current develop into the registration branch without overlapping Liquidations Live paths."
  - "Exact synchronized head 18390cedfef2c233f3b7e6c435e448d3c98a56ae passed Freqtrade CI 30458032085 including CI Gate and zizmor 30458035956."
  - "PR #689 merged with expected-head protection as current develop commit 79e4897263a0e9a8f938500d5743b11e808d4525."
  - "The newly named workflow is present on the default develop branch with push, five-minute schedule and workflow_dispatch triggers and runs on freqtrade-staging."
derived:
  - "No unattended production session is required; production auth is checked directly while protected reads run only in the isolated candidate."
  - "Failure-only artifacts avoid persistent storage growth from healthy five-minute checks."
  - "The connector workflow-run lookup is limited to pull_request-triggered runs, so an empty result cannot prove that a push or schedule run was not created."
  - "Because the pending commit status is published inside the freqtrade-staging job, absence of that status is also consistent with a created run waiting for an unavailable or mismatched self-hosted runner."
unknown:
  - "Whether the newly registered workflow is visible and enabled in the GitHub Actions control plane."
  - "Whether its push or scheduled run is queued for freqtrade-staging."
  - "Whether the first trusted execution reports healthy collector and portal LIVE state."
conflicts: []
first_failure:
  marker: TRUSTED_HEALTH_TERMINAL_EVIDENCE_MISSING
  evidence: "No liquidations-live-health classic commit status was published on current develop commit 79e4897263a0e9a8f938500d5743b11e808d4525 through the post-16:00 Europe/Warsaw schedule check; the available connector cannot list push/schedule runs or inspect self-hosted runners."
rejected_hypotheses:
  - "Store or fabricate a real production portal session."
  - "Enable fixture identity in the production portal or weaken SESSION_MISSING."
  - "Mount Liquid20 writable, mount the Docker socket or restart production as part of monitoring."
  - "Upload artifacts for healthy five-minute checks."
  - "Treat an empty pull-request-only workflow lookup as proof that no push or scheduled run exists."
changed_paths:
  - .github/workflows/liquidations-live-operational-health.yml
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
  - command: "PR #689 exact synchronized head validation"
    result: PASS
    evidence: "Freqtrade CI 30458032085 including CI Gate and zizmor 30458035956 succeeded on 18390cedfef2c233f3b7e6c435e448d3c98a56ae."
  - command: "PR #689 merge"
    result: PASS
    evidence: "Merged exact synchronized head with expected-head protection as develop commit 79e4897263a0e9a8f938500d5743b11e808d4525."
  - command: "Liquidations Live Health terminal status for 79e4897263a0e9a8f938500d5743b11e808d4525"
    result: NOT_OBSERVED
    evidence: "No liquidations-live-health classic commit status was visible through the post-16:00 Europe/Warsaw schedule check."
blockers:
  - marker: SELF_HOSTED_HEALTH_EXECUTION_UNOBSERVED
    evidence: "The implementation and workflow registration repair are merged, but terminal production health proof requires a push, scheduled or manually dispatched run to start on freqtrade-staging; current connector permissions expose neither push/schedule run listing nor runner state."
next_action: "In GitHub Actions, open Liquidations Live Health and dispatch it on develop; if the run remains queued, restore or relabel the freqtrade-staging runner, then record the run ID and terminal collector-and-portal outcome."
```
