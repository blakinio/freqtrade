# FTAI-20260803 Liquidations Live health recovery

```yaml
policy_version: 2
prompting_standard_version: 2.1
task_id: FTAI-20260803-liquidations-live-health-recovery
project_lane: freqtrade-operations
phase: implement
status: implementing
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
branch: fix/liquidations-live-health-recovery-20260803
base: develop@1c7044e9699727732928dcdf71e0fe4e1a159108
issue: 1162
incident_issue: 900
invocation_started_at: 2026-08-03T23:08:00+02:00
last_progress_at: 2026-08-03T23:15:00+02:00
ci_checks_for_current_head: 0
unchanged_state_checks: 0
identical_failure_retries: 0
repair_cycles_for_current_gate: 0
context_reconstruction_attempts: 0
stall_warnings: 0
```

## Objective

Restore reliable five-minute Liquidations Live operational monitoring and recover the existing portal container when its local bounded health boundary is unresponsive, without changing collector data, trading state, credentials, or model state.

## Acceptance inventory

- The scheduled health run no longer launches the heavyweight isolated portal proof.
- Every portal probe has a hard timeout and always emits a structured report.
- The existing stateless read-only portal container is restarted at most once by the repair workflow after a failed local probe, then re-probed.
- Reconnect alerts use a runtime-normalized hourly budget rather than an ever-growing lifetime count.
- Collector, disk, source and portal health remain fail-closed.
- Focused tests and exact-head CI pass.
- A post-merge Synology run verifies the real collector/portal path, closes Issue #900 automatically, and emits one recovery notification.

## Context checkpoint

- PROVEN: workflow run `30848823552` used runner `freqtrade-synology-staging`; collector, disk and all three exchange sources were healthy.
- PROVEN: the portal proof exceeded its 240-second subprocess budget after the production preflight and created no portal report; the run left an orphan Docker process.
- PROVEN: Issue #900 therefore reported `PORTAL_LIQUIDATIONS_HEALTH_UNAVAILABLE` and a cumulative OKX reconnect count of 445, while Telegram later replaced the diagnosis with a stale-monitor synthetic code.
- DERIVED: a lightweight production-boundary probe is the correct five-minute operational check; the isolated candidate proof remains deployment evidence, not a recurring liveness probe.
- UNKNOWN: whether the production portal process is currently responsive; the repair workflow will prove or restart it after merge.
- CONFLICT: `repair-synology-autostart.yml` enforces `restart=always`, while the legacy full proof still records `unless-stopped`; this task does not rely on that legacy proof for recurring health.
- owned_paths: `.github/workflows/liquidations-live-operational-health.yml`, `.github/workflows/repair-synology-autostart.yml`, `ai_platform/scripts/liquidation_operational_health.py`, `deploy/synology/portal/probe-liquidations-live-operational.sh`, focused tests, this task record.
- next_action: implement the bounded probe, recovery workflow, runtime-normalized reconnect policy and focused tests.
