# FTAI-20260803 Liquidations Live health recovery

```yaml
policy_version: 2
prompting_standard_version: 2.1
task_id: FTAI-20260803-liquidations-live-health-recovery
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
branch: fix/liquidations-live-health-recovery-20260803
base: develop@1c7044e9699727732928dcdf71e0fe4e1a159108
pull_request: 1164
issue: 1162
incident_issue: 900
invocation_started_at: 2026-08-03T23:08:00+02:00
last_progress_at: 2026-08-03T23:29:00+02:00
ci_checks_for_current_head: 0
unchanged_state_checks: 0
identical_failure_retries: 0
repair_cycles_for_current_gate: 1
context_reconstruction_attempts: 0
stall_warnings: 0
```

## Objective

Restore reliable five-minute Liquidations Live operational monitoring and recover the existing portal container when its local bounded health boundary is unresponsive, without changing collector data, trading state, credentials, or model state.

## Acceptance inventory

- The scheduled health run no longer launches the heavyweight isolated portal proof.
- Every portal and Docker probe has a hard timeout and always emits a structured report.
- The existing stateless read-only portal container is restarted at most once by the repair workflow after a failed local probe, then re-probed.
- Reconnect alerts use a runtime-normalized hourly budget rather than an ever-growing lifetime count.
- Collector, disk, source and portal health remain fail-closed.
- Focused tests and exact-head CI pass.
- A post-merge Synology run verifies the real collector/portal path, closes Issue #900 automatically, and emits one recovery notification.

## Validation checkpoint

- PASS: initial PR generation compiled the AI platform and ran `1188 passed, 71 skipped`; Ruff lint passed.
- REPAIRED: initial Ruff format gate found one deterministic wrapping difference; exact formatter output was committed and the temporary formatter workflow was deleted.
- PASS: initial GitHub Actions security analysis and Portal Completeness Audit completed successfully.
- PENDING: exact final-head AI Platform CI, Freqtrade CI, security analysis and Portal Completeness Audit.
- PENDING: post-merge real Synology repair/health E2E and recovery notification evidence.

## Independent audit checkpoint

- Scope audit: seven changed paths, all within declared ownership; no trading configuration, collector data, exchange credentials, model state or live-capital paths changed.
- Safety audit: the operational probe validates non-root execution, read-only Liquid20 mount, absence of Docker-socket mount, protected health boundary and `restart=always`.
- Boundedness audit: Docker preflight calls use ten-second bounds; HTTP fetches use `AbortSignal.timeout`; the containing Docker exec has an outer timeout; recovery allows one restart and finite retries.
- Diagnostic audit: structured failure evidence includes the failed probe stage; operational source results are derived from the already trusted collector pointer instead of being fabricated from a missing portal report.
- Alert-policy audit: cumulative reconnect counts are normalized by collector uptime, while invalid state and rates above the configured hourly budget remain fail-closed.
- Review hygiene: zero review submissions and zero inline review threads at this checkpoint.
- Open material findings: none.

## Context checkpoint

- PROVEN: workflow run `30848823552` used runner `freqtrade-synology-staging`; collector, disk and all three exchange sources were healthy, but the heavyweight portal proof exceeded its 240-second subprocess budget and left an orphan Docker process.
- PROVEN: a later run `30854111170` proved the production portal and all three portal sources healthy; Issue #900 remained open solely because lifetime OKX reconnect count `447` exceeded fixed threshold `100`.
- PROVEN: the current incident is therefore an alert-policy defect, with a prior transient heavyweight-proof timeout as a reliability defect; it is not a current exchange-source, disk, collector or portal outage.
- DERIVED: a lightweight bounded production-boundary probe is the correct five-minute operational check; the isolated candidate proof remains deployment evidence, not a recurring liveness probe.
- PROVEN: the repair workflow will not restart a healthy portal; it restarts the existing stateless container once only after the bounded probe fails.
- owned_paths: `.github/workflows/liquidations-live-operational-health.yml`, `.github/workflows/repair-synology-autostart.yml`, `ai_platform/scripts/liquidation_operational_health.py`, `deploy/synology/portal/probe-liquidations-live-operational.sh`, focused tests, this task record.
- next_action: wait for exact final-head CI, merge PR #1164 only if all required gates pass, then verify real Synology recovery and archive the task.
