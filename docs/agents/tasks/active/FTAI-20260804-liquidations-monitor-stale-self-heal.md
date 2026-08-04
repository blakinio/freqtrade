# FTAI-20260804 Liquidations monitor stale self-heal

```yaml
policy_version: 2
prompting_standard_version: 2.1
task_id: FTAI-20260804-liquidations-monitor-stale-self-heal
project_lane: freqtrade-operations
phase: validate
status: validating
execution_mode: github
run_scope: single_task
continuation_policy: continue_until_real_stop
task_completion_policy: finalize_archive_and_continue
user_communication: terminal_only
feature_scope:
  type: infrastructure
  user_facing: false
  backend_required: true
  frontend_required: false
  integration_required: true
  e2e_required: true
  completion_claim: internal_only
branch: fix/liquidations-monitor-stale-self-heal-20260804
base: develop@2cd22f389060683919fa373c34e73fd2a9ca1dba
pull_request: 1200
incident_issue: 1198
previous_repairs: [1170, 1187]
invocation_started_at: 2026-08-04T22:41:00+02:00
last_progress_at: 2026-08-04T23:04:00+02:00
ci_checks_for_current_head: 0
unchanged_state_checks: 0
identical_failure_retries: 0
repair_cycles_for_current_gate: 0
context_reconstruction_attempts: 1
stall_warnings: 0
```

## Objective

Stop false production-outage Telegram alerts caused only by delayed GitHub scheduled events, while preserving immediate alerts for a real collector, portal, source, disk or runner failure.

## Proven recurrence

- Issue #1198 opened at `2026-08-04T20:19:22Z` with `LIQUIDATIONS_HEALTH_MONITOR_STALE`.
- The referenced health run `30942268319` had actually completed successfully on the real Synology runner.
- Its health job ran at approximately `2026-08-04T19:13Z` and reported `alerts: []`, healthy collector, healthy portal, connected Binance/Bybit/OKX and acceptable disk capacity.
- The Telegram schedule ran at `2026-08-04T20:19Z`, saw that the latest health run was more than 60 minutes old and created a production `AWARIA` alert.
- The open synthetic stale-monitor Issue then remains authoritative to the existing notifier until another health run closes it, so hourly reminders can continue even though no production component failure was proven.

## Root cause

GitHub scheduled workflows are not a reliable five-minute timer. The notification watchdog correctly observed stale scheduling but incorrectly escalated the first scheduler gap as a production outage instead of first requesting a fresh bounded health probe.

## Acceptance inventory

- A stale completed or missing health run causes one bounded `workflow_dispatch` of `Liquidations Live Health` before Telegram escalation.
- A successful dispatch does not create or remind a production outage Issue.
- A fresh queued or in-progress recovery probe suppresses stale-monitor reminders while remaining bounded.
- A fresh successful probe closes an existing synthetic stale-monitor Issue and allows the existing recovery notification path to run.
- A real operational Issue containing a structured health report remains authoritative and is never masked by self-heal.
- The notification workflow receives only the minimal additional `actions: write` permission required for dispatch.
- Focused tests, security analysis and exact-head required CI pass.
- Post-merge schedule execution dispatches a fresh real Synology health run, closes Issue #1198 and produces no new stale-monitor outage alert.

## Safety

No exchange credential, collector data, trading configuration, model state, order authority, execution authority, production secret or live-capital setting may be changed. The self-heal action may only dispatch the existing bounded read-only health workflow on `develop`.

## Recovery checkpoint

```yaml
recovery:
  policy_version: 1
  generation: 1
  session_id: liquidations-monitor-self-heal-20260804T2241+0200
  session_started_at: 2026-08-04T22:41:00+02:00
  checkpointed_at: 2026-08-04T23:04:00+02:00
  last_progress_at: 2026-08-04T23:04:00+02:00
  phase: exact-head validation and audit
  exact_head: pending-after-checkpoint
  pull_request: 1200
  active_operation: GitHub Actions exact-head validation
  external_run_ids: [30949862938, 30949863273]
  operation_started_at: 2026-08-04T22:52:41+02:00
  wait_deadline_at: 2026-08-04T23:37:41+02:00
  check_generation: pr-1200-initial
  checks_used: 0
  status: active
  safe_to_resume: true
  resume_condition: required checks for PR #1200 reach a terminal state
  next_action: Inspect aggregate exact-head CI, repair only the first proven failure, or audit and merge if all gates pass.
```

## Context checkpoint

- PROVEN: the previous watchdog payload transport repair remains valid; run `30942268319` completed all three jobs successfully.
- PROVEN: the new incident is a scheduler-gap escalation defect, not a collector/portal outage.
- IMPLEMENTED: `liquidation_alert_watchdog.py` dispatches a fresh health probe before stale escalation and reconciles stale synthetic Issues.
- IMPLEMENTED: focused regression tests cover dispatch, in-progress suppression, successful recovery and real-incident authority.
- IMPLEMENTED: Telegram workflow uses the self-heal wrapper and grants bounded `actions: write`.
- owned_paths: `.github/workflows/liquidations-live-telegram-notifications.yml`, `ai_platform/scripts/liquidation_alert_watchdog.py`, `tests/ai_platform_integration/test_liquidation_alert_watchdog.py`, this task record.
- next_action: inspect exact-head CI for PR #1200 and repair only the first proven failure, or audit and merge if all gates pass.
