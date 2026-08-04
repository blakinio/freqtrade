# FTAI-20260804 Liquidations reconnect counter rotation repair

```yaml
policy_version: 2
prompting_standard_version: 2.1
task_id: FTAI-20260804-liquidations-reconnect-counter-rotation-repair
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
branch: fix/liquidations-reconnect-counter-rotation-20260804
base: develop@c4db1297ccc2f9664b755be983b1ef790ab968ff
tracking_issue: 1168
incident_issue: 1167
pull_request: 1170
invocation_started_at: 2026-08-04T07:52:00+02:00
last_progress_at: 2026-08-04T08:36:00+02:00
```

## Objective

Repair the active Liquidations Live incident without suppressing a real outage: align reconnect counters with their measurement epoch across daily rotation, preserve the authoritative health diagnosis in Telegram, and verify recovery on the real Synology runner.

## Proven root cause

- The live manager starts a new daily run and resets `collector_started_at_ms`.
- It then restores the previous run's cumulative `reconnect_count` into the new run.
- Operational health divides that carried count by the new run's short uptime.
- Issue #1167 therefore reported `105.1/h` even though the source, collector, portal and disk were healthy.
- Telegram replaces the open issue's concrete diagnosis with `LIQUIDATIONS_HEALTH_MONITOR_STALE` whenever the latest scheduled run is older than ten minutes, and incorrectly labels that condition as an unavailable Synology runner.

## Acceptance inventory

- Reconnect counters reset when their daily measurement epoch resets.
- A regression test proves daily rotation cannot inflate reconnect rate.
- An open operational issue remains the authoritative Telegram diagnosis; scheduler staleness does not erase it.
- `MONITOR_STALE` no longer claims the Synology runner is unavailable without runner-specific evidence.
- Focused tests and exact-head CI pass.
- Post-merge Synology health check reports zero alerts and closes Issue #1167 automatically.
- Telegram persisted state becomes healthy after verified recovery.

## Safety

No exchange credentials, collector data, trading configuration, model state, orders, execution authority or live-capital setting may be changed. Do not close Issue #1167 manually before a fresh healthy operational run.

## Implementation checkpoint

- Reset run-scoped reconnect counters when daily rotation creates a new measurement epoch.
- Preserve open operational issue evidence ahead of synthetic scheduler-staleness diagnosis.
- Widen scheduler freshness tolerance from 10 to 60 minutes.
- Stop mapping monitor staleness to a proven Synology runner outage.
- Add focused regression coverage for rotation and notification diagnosis.

## Validation checkpoint

- PASS: AI platform test suite on the implementation heads — `1188 passed, 71 skipped`.
- PASS: Ruff lint and Ruff format on the repaired implementation.
- REPAIRED: exact formatter layouts were committed for the notification module and focused tests.
- REPAIRED: full pre-commit mypy required explicit timestamp narrowing for both stale-run and queued-run age comparisons.
- PASS: all temporary repair workflows self-deleted and are absent from the final PR diff.
- PENDING: exact final-head AI Platform CI, Freqtrade CI, security analysis and Portal Completeness Audit.
- PENDING: post-merge Synology deployment and operational health recovery for Issue #1167.

## Next action

Wait for exact final-head CI, audit the final diff and review state, merge only after all required gates pass, then verify Issue #1167 recovery on the real Synology runner.
