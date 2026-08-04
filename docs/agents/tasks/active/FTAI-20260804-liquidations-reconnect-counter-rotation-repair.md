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
branch: fix/liquidations-health-watchdog-payload-20260804
base: develop@fcc5091a3ff9b9dae5a1a2b953170ca9baa8e4bf
tracking_issue: 1168
incident_issue: 1167
followup_incident_issue: 1179
previous_pull_request: 1170
pull_request: 1187
invocation_started_at: 2026-08-04T17:43:00+02:00
last_progress_at: 2026-08-04T17:58:00+02:00
ci_checks_for_current_head: 0
unchanged_state_checks: 0
identical_failure_retries: 0
repair_cycles_for_current_gate: 0
context_reconstruction_attempts: 1
stall_warnings: 0
```

## Objective

Complete the Liquidations Live recovery without suppressing real outages: keep reconnect counters aligned with their measurement epoch, preserve truthful Telegram diagnosis, and make the runner-assignment watchdog reliable for large GitHub API responses.

## Proven state

- PR #1170 merged the reconnect-counter and Telegram-diagnosis repair as `416223a803c6eb803e09429b3368488276a112e9`.
- Synology deployment run `30897664385` completed successfully.
- In run `30898065128`, the real `Check Synology collector and portal` job passed and reported the live collector and portal healthy.
- The parallel `Watch freqtrade-staging assignment` job failed after 128 seconds with `/usr/bin/python: Argument list too long`.
- The watchdog passed the full jobs API response through `JOBS_JSON` and the full open-Issues response through `ISSUES_JSON`; either response could exceed the operating-system environment/argument limit.
- The repair on PR #1187 writes both API responses to bounded runner-temp files and parses them by path.
- Regression coverage forbids reintroducing unbounded GitHub JSON transport through environment variables.
- The secondary synthetic incident #1179 recovered and is closed.

## Acceptance inventory

- Reconnect counters reset when their daily measurement epoch resets.
- An open operational issue remains the authoritative Telegram diagnosis.
- Monitor staleness does not claim a Synology runner outage without runner-specific evidence.
- The runner watchdog never transports unbounded GitHub jobs or Issues JSON through environment variables or command-line arguments.
- Regression coverage prevents reintroduction of unbounded environment transport.
- Focused tests, workflow/security validation and required exact-head CI pass.
- Post-merge `Liquidations Live Health` runs on the real Synology runner with both the health job and runner watchdog successful.
- No new open `[liquidations-live] operational health alert` remains after recovery.
- The active task is archived and ownership is released.

## Safety

No exchange credentials, collector data, trading configuration, model state, orders, execution authority or live-capital setting may be changed. The watchdog must continue to fail closed when the trusted Synology health job genuinely does not start.

## Recovery checkpoint

```yaml
recovery:
  policy_version: 1
  generation: 2
  session_id: liquidations-watchdog-20260804T1743+0200
  session_started_at: 2026-08-04T17:43:00+02:00
  checkpointed_at: 2026-08-04T17:58:00+02:00
  last_progress_at: 2026-08-04T17:58:00+02:00
  phase: exact-head validation and final audit
  exact_head: f6a32588de874160e7b05df9599b0444d36ea4dc
  pull_request: 1187
  active_operation: GitHub Actions exact-head validation
  external_run_ids: [30897664385, 30898065128]
  operation_started_at: 2026-08-04T17:56:21+02:00
  wait_deadline_at: 2026-08-04T18:41:21+02:00
  check_generation: pr-1187-initial
  checks_used: 0
  status: active
  safe_to_resume: true
  resume_condition: required checks for PR #1187 reach a terminal state
  next_action: Inspect the aggregate exact-head CI result and repair only the first proven failure, or audit and merge if all gates pass.
```

## Next action

Inspect the aggregate exact-head CI result and repair only the first proven failure, or audit and merge if all gates pass.
