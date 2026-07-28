---
task_id: FTAI-20260728-liquidations-live-operational-alerting
status: validating
branch: feat/liquidations-live-operational-alerting-20260728
base_branch: develop
created: 2026-07-28
updated: 2026-07-28
related_pr: 578
required_reads:
  - docs/agents/tasks/FTAI-20260727-liquidations-live-stream-repair.md
  - deploy/synology/liquid20/LIVE_STREAM.md
search_first:
  - .github/workflows/liquidations-live-health.yml
  - ai_platform/scripts/liquidation_live_health.py
  - tests/ai_platform_integration/test_liquidation_live_health.py
---

# FTAI-20260728-liquidations-live-operational-alerting

Add autonomous operational alerting for the completed Synology liquidation live collector without modifying collector data, accepted historical evidence or trading state.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-28T07:55:00Z
head: c54c085e6633c3317df4956932f893b2a3119cfc
branch: feat/liquidations-live-operational-alerting-20260728
pr: 578
status: validating
context_routes:
  - docs/agents/tasks/FTAI-20260728-liquidations-live-operational-alerting.md
  - .github/workflows/liquidations-live-health.yml
  - ai_platform/scripts/liquidation_live_health.py
  - deploy/synology/liquid20/LIVE_STREAM.md
  - tests/ai_platform_integration/test_liquidation_live_health.py
owned_paths:
  - .github/workflows/liquidations-live-health.yml
  - ai_platform/scripts/liquidation_live_health.py
  - deploy/synology/liquid20/LIVE_STREAM.md
  - tests/ai_platform_integration/test_liquidation_live_health.py
  - docs/agents/tasks/FTAI-20260728-liquidations-live-operational-alerting.md
proven:
  - The production collector deployment is complete and healthy under task FTAI-20260727-liquidations-live-stream-repair.
  - The monitor evaluates container running/restarting/OOM state, live-state contract, active run, collector and source heartbeat freshness, configured connected subscriptions, data-only safety and disk capacity.
  - Default thresholds are 60 seconds for collector and source heartbeat freshness, below 90 percent disk use and at least 20 GiB free.
  - Unhealthy state creates or updates one exact-title GitHub Issue; healthy recovery comments and closes the issue.
  - Healthy scheduled checks do not upload artifacts; unhealthy checks retain a JSON report for 14 days.
  - Focused local validation passed 6 tests covering healthy, stale, disconnected, disk, safety and alert lifecycle paths.
derived:
  - GitHub Issue deduplication prevents a new alert issue every five minutes while preserving current evidence in the issue body.
  - A failing workflow also activates normal GitHub Actions failure notifications independently of Issue delivery.
  - Push-to-develop triggering provides immediate first validation after merge before the recurring schedule.
unknown:
  - Whether exact-head repository CI and zizmor accept the new workflow and module.
  - Whether the first trusted Synology health run reports healthy with the configured disk thresholds.
conflicts: []
first_failure:
  marker: LIQUID20_OPERATIONAL_ALERTING_MISSING
  evidence: The collector was deployed successfully but had no automated stale-heartbeat, source-connectivity or disk-capacity alert lifecycle.
rejected_hypotheses:
  - Upload an artifact on every five-minute healthy run; this would consume Actions storage unnecessarily.
  - Create a new issue for every failed check; the alert must remain deduplicated.
  - Add trading credentials or collector write access to the monitor; it needs only host read checks, Docker inspect and GitHub Issue permission.
changed_paths:
  - .github/workflows/liquidations-live-health.yml
  - ai_platform/scripts/liquidation_live_health.py
  - deploy/synology/liquid20/LIVE_STREAM.md
  - tests/ai_platform_integration/test_liquidation_live_health.py
  - docs/agents/tasks/FTAI-20260728-liquidations-live-operational-alerting.md
validation:
  - command: pytest -q tests/ai_platform_integration/test_liquidation_live_health.py
    result: PASS
    evidence: 6 focused tests passed locally.
  - command: exact-head PR 578 CI and zizmor
    result: NOT_RUN
    evidence: Awaiting the final checkpoint commit.
  - command: first develop Liquidations Live Health workflow
    result: NOT_RUN
    evidence: Runs only after the reviewed workflow reaches develop.
blockers: []
next_action: Validate exact-head PR 578 with CI, zizmor and review-thread checks, merge only if green, then inspect the first trusted Synology health run and record terminal evidence.
```
