# FTAI-20260808 — WickHunter Unified Runtime Mode

```yaml
task_id: FTAI-20260808-wickhunter-unified-runtime-mode
project_lane: freqtrade-wickhunter
programme: WickHunter
policy_version: 2
prompting_standard_version: 2.1
task_kind: implementation
feature_scope:
  type: full_stack
  user_facing: true
  backend_required: true
  frontend_required: true
  integration_required: true
  e2e_required: true
  completion_claim: complete_feature
execution_mode: chat_github_actions
run_scope: autonomous_program
continuation_policy: continue_until_real_stop
task_completion_policy: finalize_archive_and_continue
implementation_authorized: true
status: investigating
base_branch: develop
trusted_base_sha: 5a19ae32f1f71b112130ea66cb8d56d9a3e44049
branch: fix/wickhunter-1396-synology-recovery-v2
related_issue: 1396
producer_pr: 1397
runtime_generation_pr: 1388
portal_adoption_pr: 1436
live_capital_authorized: false
trading_credentials_authorized: false
real_order_adapter_authorized: false
real_exchange_execution_authorized: false
wh09_redeploy_authorized: false
```

## Objective

Terminally close Issue #1396 by proving the already-merged unified WickHunter runtime-mode implementation through the real Synology Portal adoption path, without replacing or restarting WH09 and without expanding trading authority.

## Frozen runtime identity and safety

```yaml
candidate: H900
mode: SHADOW
no_trade_confidence: "0.60"
container_id: ebb3bc5151c6041cc557395f77b3001230f881bc39c2e9a5c4789fcd920e3b37
image: sha256:38b88958a873af21cca80455a27e14163bce85da6641a2688913e8772b7d2e88
deployment_revision: 90cfc5ded10b0c6cb6406d00042817aca611e900
paper_activation_authorized: false
trading_credentials_present: false
order_adapter_present: false
execution_enabled: false
orders_submitted: 0
live_capital_authorized: false
automatic_promotion_enabled: false
```

Do not create a second runtime, activate PAPER, authorize LIVE, add credentials or a real order adapter, submit exchange orders, weaken fail-closed behavior, perform broad Docker cleanup, or restart/recreate/redeploy WH09 unless a proven cause and trusted repository authority explicitly require that exact operation.

## Acceptance inventory

- `A1`: canonical `BotMode` is reused; no competing mode enum or runtime authority exists.
- `A2`: SHADOW and PAPER are capabilities of one WickHunter runtime product, not separate installations.
- `A3`: mode and PAPER eligibility are immutable digest/generation material.
- `A4`: PAPER requires explicit eligibility and fails closed when absent, false or malformed.
- `A5`: LIVE remains blocked and non-executable.
- `A6`: desired and observed generation/mode truth converge only after exact reconciliation.
- `A7`: start/restart/rollback semantics remain generation-exact.
- `A8`: focused tests cover SHADOW, PAPER eligible/ineligible, LIVE rejection, save-without-rollout, rollout and rollback/restart.
- `A9`: authenticated browser/API integration consumes canonical runtime truth.
- `A10`: real Synology post-merge E2E proves one unchanged WH09 runtime, H900/SHADOW, healthy fresh evidence, desired==observed generation and zero trading authority.

## Delivered repository state

- PR #1397 merged at `f46d10e30302b7310fe2a6e235c2ca05a0281a0a`.
- PR #1388 merged at `4e947ccd20e87d2a9f6a334509208a4845efc0a5`.
- PR #1436 merged at `978621fb358885dbf3c85d1bf837af9270678241`.
- PR #1443 is closed/unmerged and remains obsolete because its broad cleanup path is not an accepted recovery.
- Issue #1396 remains open because the required real post-merge Synology adoption E2E has not passed.

## Post-merge runtime evidence

```yaml
portal_adoption:
  run: 31386104997
  attempt_1:
    result: FAILURE
    first_failure: Docker runtime preflight could not start a disposable container
    wh09_changed: false
  attempt_2:
    result: FAILURE
    preflight: PASS
    wh09_health_at_that_time: healthy
    first_failure: Portal control-plane BuildKit context processing
    portal_deployed: false
    adoption_started: false
    wh09_changed: false
recovery_1:
  run: 31420369456
  result: FAILURE_BEFORE_MUTATION
recovery_2:
  run: 31420701120
  result: FAILURE_BEFORE_MUTATION_WH09_UNHEALTHY
diagnostic_3:
  run: 31422691173
  job: 93566990872
  result: FAILURE_AFTER_PRIMARY_WH09_EVIDENCE_DUE_TO_DIAGNOSTIC_HEREDOC_DEFECT
  wh09_matching_count: 1
  wh09_running: true
  wh09_restart_count: 0
  wh09_health: unhealthy
  manual_healthcheck_rc: 1
  manual_healthcheck_output: research operator is fail-closed
  generation: 645
  last_observation_age_seconds: 8023.462
  telemetry_age_seconds: 8023.462
  process_alive: true
  zero_authority: true
  wh09_mutation: false
```

The diagnostic-3 failure did not prove BuildKit is still the active cause. It proved that WH09's supervisor remains alive and refreshes fail-closed health while no successful runtime observation/telemetry has advanced for over two hours. The exact exception was not included in that run's safe health projection and the Liquid20 portion never executed because its shell heredoc terminator was malformed.

Repository code at accepted deployment revision proves `run_forever()` catches each cycle exception, publishes `error_code`/`error_message` into `/runtime/operator/health.json`, sleeps and retries. Therefore a fresh health file with stale generation/telemetry is consistent with repeated per-cycle failures rather than a dead main process.

## Current bounded root-cause diagnostic

Workflow `.github/workflows/portal-wickhunter-buildkit-cache-recovery.yml` was repaired at exact diagnostic head `f42e909c5a87ae89a627eaeae7b1b7e3cd613c3c`. It is read-only and collects:

- exact WH09 identity/image/revision/running/health and Docker health history;
- safe health fields including `error_code`, `error_message`, breaker reasons and zero-authority fields;
- telemetry freshness, bounded journal metadata and bounded error-oriented WH09 logs;
- WH09 process state and read-only Liquid20 mount readability;
- Liquid20 pointer schema/contract/active run/run_state/heartbeat/authority/source freshness;
- equality of the live pointer state and persisted `run-state-v1.json`;
- whether the active run is the newest regular run;
- an exact `load_liquid20_snapshot()` read using the production 300-second freshness contract;
- a public Binance USD-M read-only market probe only if the Liquid20 snapshot is valid;
- `liquid20-live` container running/health/restart/process/log state;
- one 70-second WH09 supervisor interval to prove whether health timestamps and generation advance;
- final proof that WH09 identity/image/revision/running state was not mutated.

No prune, build, stop, restart, remove, recreate, deployment, credential access, PAPER activation or LIVE action is performed.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-10T21:41:00+02:00
status: investigating
branch: fix/wickhunter-1396-synology-recovery-v2
diagnostic_head: f42e909c5a87ae89a627eaeae7b1b7e3cd613c3c
issue: 1396
related_prs:
  - 1397: merged
  - 1388: merged
  - 1436: merged
  - 1443: closed_unmerged_obsolete_broad_cleanup
proven:
  - all three implementation/consumer PRs are merged
  - exactly one expected WH09 existed at diagnostic-3 and was running without restart
  - WH09 was fail-closed with generation 645 and stale successful observation/telemetry
  - WH09 zero-authority invariants remained intact
  - diagnostic-3 mutated no WH09 runtime state
  - the supervisor process remained alive
  - accepted operator code publishes the exact caught exception to health error_code/error_message each failed cycle
unknown:
  - first exact current WH09 cycle exception
  - whether liquid20-live is currently running and fresh
  - whether pointer and persisted active run state agree
  - whether source freshness, mount access, public market access, model binding, journal state or another exact cause is responsible
  - whether WH09 will naturally recover after any upstream repair
  - whether the Portal BuildKit failure remains after WH09 recovery
  - terminal post-merge Portal adoption/API/browser result
conflicts: []
validation:
  - run: 31422691173
    result: FAILURE_WITH_USEFUL_WH09_EVIDENCE_AND_NO_MUTATION
  - run: 31425261462
    head: f42e909c5a87ae89a627eaeae7b1b7e3cd613c3c
    workflow: Portal WickHunter WH09 Root Cause Diagnostic
    result: QUEUED_AT_CHECKPOINT
counters:
  repair_cycles_for_current_gate: 2
  identical_failure_retries: 0
  unchanged_state_checks: 0
blockers:
  - root cause remains UNKNOWN until diagnostic run 31425261462 is terminal and its primary evidence is classified
next_action: Inspect terminal run 31425261462 once, classify the first proven cause, and perform only the smallest authorized repair that addresses that cause.
```

## Recovery checkpoint

```yaml
recovery:
  policy_version: 1
  generation: 4
  session_id: 2026-08-10T21:37+02:00
  session_started_at: 2026-08-10T21:37:00+02:00
  checkpointed_at: 2026-08-10T21:41:00+02:00
  last_progress_at: 2026-08-10T21:40:35+02:00
  phase: wh09_liquid20_root_cause_diagnostic
  exact_head: f42e909c5a87ae89a627eaeae7b1b7e3cd613c3c
  pull_request: none
  active_operation: Portal WickHunter WH09 Root Cause Diagnostic
  external_run_ids:
    - 31425261462
  operation_started_at: 2026-08-10T21:40:35+02:00
  wait_deadline_at: 2026-08-10T21:50:35+02:00
  check_generation: wh09-root-cause-diagnostic-v4
  checks_used: 1
  status: active
  safe_to_resume: true
  resume_condition: workflow run 31425261462 is terminal
  next_action: Inspect run 31425261462 once when terminal and classify the first proven root cause without mutating WH09.
```

## Terminal closeout requirements

Do not set `status: completed` until all are true:

```yaml
closeout:
  wh09_recovered:
    matching_containers: 1
    running: true
    docker_health: healthy
    mode: shadow
    candidate: H900
    no_trade_confidence: "0.60"
    fresh_health: true
    fresh_telemetry: true
    consecutive_successful_generation_advances: 2
    zero_authority: true
  e2e:
    result: PASS
    required_real_synology_adoption: true
    runtime_container_unchanged: true
    adoption_provenance: EXTERNAL_RUNTIME_ADOPTED
    desired_equals_observed_generation: true
  audit:
    result: PASS_ZERO_MATERIAL_FINDINGS
    material_findings_open: 0
  final_ci:
    result: PASS
    exact_head_required: true
  pull_requests:
    open_related_prs: 0
    unresolved_review_threads: 0
  temporary_recovery_workflow_removed: true
  issue_1396: closed_completed
  task_archived: true
  ownership_released: true
  stale_recovery_branch_reconciled: true
```
