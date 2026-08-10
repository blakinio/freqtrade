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
status: waiting
base_branch: develop
trusted_base_sha: 2a9bee4895981f0a2b7f7f08e0e1d2d2e2ad646a
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

## Canonical semantics

- `SHADOW`: real/current market observation, inference and evidence only; zero exchange-order authority.
- `PAPER`: simulator/paper lifecycle only and only with explicit immutable eligibility/authorization evidence.
- `LIVE_BLOCKED`: non-executable under current authority.
- Mode is immutable RuntimeGeneration/config material; transitions require explicit generation rollout/reconciliation.
- The accepted WH09 H900 runtime remains SHADOW with `no_trade_confidence=0.60` until a separate PAPER eligibility gate exists.
- ADR-022, merged after this invocation's trusted base, makes PAPER the normal operational target and SHADOW optional/purpose-bound; it does not invalidate this bounded SHADOW runtime/integration-validation closeout and does not authorize changing WH09 mode in this task.

## Acceptance inventory

- `A1`: canonical `BotMode` is reused; no competing mode enum or runtime authority exists.
- `A2`: SHADOW and PAPER are capabilities of one WickHunter runtime product, not separate bot installations.
- `A3`: mode and PAPER eligibility are immutable digest/generation material.
- `A4`: PAPER requires explicit eligibility and fails closed when absent, false or malformed.
- `A5`: LIVE remains blocked and cannot become executable under this task.
- `A6`: desired and observed RuntimeGeneration/mode truth do not converge before exact reconciliation.
- `A7`: start/restart/rollback semantics remain generation-exact.
- `A8`: focused tests cover SHADOW, PAPER eligible/ineligible, LIVE rejection, save-without-rollout, rollout and rollback/restart.
- `A9`: authenticated browser/API integration proves the existing Bots surface consumes canonical runtime truth.
- `A10`: real Synology post-merge E2E proves exactly one unchanged WH09 runtime, H900/SHADOW, healthy evidence, desired==observed generation, zero credentials, zero order adapter, execution disabled, orders submitted zero and live capital false.

## Delivered repository state

- PR #1397 merged at `f46d10e30302b7310fe2a6e235c2ca05a0281a0a`: canonical WickHunter SHADOW/PAPER/LIVE_BLOCKED producer contract.
- PR #1388 merged at `4e947ccd20e87d2a9f6a334509208a4845efc0a5`: canonical RuntimeGeneration/rollout authority.
- PR #1436 merged at `978621fb358885dbf3c85d1bf837af9270678241`: Portal adoption, runtime evidence API and Bots-page consumer.
- PR #1436 exact-head CI and authenticated browser/API-mode E2E passed before merge; fresh audit had zero material findings and unresolved review threads were zero.
- Issue #1396 was deliberately reopened after merge because required real post-merge Synology adoption evidence had not reached PASS.

## Post-merge failure evidence

```yaml
adoption_attempt_1:
  workflow_run: 31386104997
  job: 93446771029
  result: FAILURE
  first_failure: Docker runtime preflight could not start a disposable container
  wh09_changed: false
adoption_attempt_2:
  workflow_run: 31386104997
  job: 93455371701
  result: FAILURE
  preflight: PASS
  wh09_identity: ebb3bc5151c6041cc557395f77b3001230f881bc39c2e9a5c4789fcd920e3b37
  wh09_health: healthy
  first_failure: BuildKit failed while loading/copying Portal control-plane build context
  portal_deployed: false
  adoption_started: false
  wh09_changed: false
recovery_1:
  run: 31420369456
  result: FAILURE_BEFORE_MUTATION
recovery_2:
  run: 31420701120
  result: FAILURE_BEFORE_MUTATION_WH09_UNHEALTHY
  wh09_matching_count: 1
  wh09_identity: ebb3bc5151c6041cc557395f77b3001230f881bc39c2e9a5c4789fcd920e3b37
  wh09_revision: 90cfc5ded10b0c6cb6406d00042817aca611e900
  wh09_running: true
  wh09_health: unhealthy
  docker_mutation: false
```

The BuildKit hypothesis cannot be acted on while WH09 is unhealthy. The accepted healthcheck validates immutable SHADOW/zero-authority identity plus freshness of `/runtime/operator/health.json` and `/runtime/journal/telemetry.json` with `HEALTH_MAX_AGE_SECONDS=600`. Broad cleanup, restart, replacement and redeploy remain forbidden.

## Current recovery

Recovery generation 3 is read-only only. Workflow run `31422691173` at diagnostic head `c2a4d5cee3bb6f3225d0d2cd13de63b2ca7878c0` captures the configured healthcheck, bounded Docker health logs, one manual read-only healthcheck execution, safe health/telemetry fields and ages, process snapshot, and safe Liquid20 source state. It performs no prune, build, restart, stop, removal or deployment.

Only after this run yields a concrete causal hypothesis may the third and final bounded repair cycle be attempted. Acceptance may not be weakened from `healthy` to `degraded` or `unhealthy`.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-10T21:12:00+02:00
status: waiting
branch: fix/wickhunter-1396-synology-recovery-v2
issue: 1396
related_prs:
  - 1397: merged
  - 1388: merged
  - 1436: merged
  - 1443: closed_unmerged_obsolete_broad_cleanup
proven:
  - producer PR 1397 merged
  - canonical RuntimeGeneration PR 1388 merged
  - Portal adoption PR 1436 merged
  - premerge exact-head CI and authenticated browser E2E passed
  - current WH09 is exactly one container with unchanged ID and accepted revision
  - current WH09 is running but Docker health was unhealthy through the last bounded observation
  - recovery runs 31420369456 and 31420701120 performed no Docker mutation
  - accepted healthcheck requires <=600 second freshness for health and telemetry and exact zero-authority SHADOW identity
unknown:
  - exact current healthcheck failure message
  - runtime process progress and health/telemetry ages
  - whether Liquid20 source freshness is the upstream cause
  - whether BuildKit cache recovery remains necessary after WH09 health is restored
  - terminal postmerge Portal deployment/adoption/API persistence result
conflicts: []
validation:
  - run: 31420369456
    result: FAILURE_BEFORE_MUTATION
  - run: 31420701120
    result: FAILURE_BEFORE_MUTATION_WH09_UNHEALTHY
  - run: 31422691173
    head: c2a4d5cee3bb6f3225d0d2cd13de63b2ca7878c0
    workflow: Portal WickHunter WH09 Readonly Health Diagnostic
    result: IN_PROGRESS_AT_SECOND_ALLOWED_OBSERVATION
counters:
  repair_cycles_for_current_gate: 2
  identical_failure_retries: 0
  unchanged_state_checks: 2
blockers:
  - read-only health diagnostic run 31422691173 remained in progress at the second allowed ordinary state observation
next_action: On the next invocation inspect run 31422691173 once; if terminal, use its exact health evidence for the one remaining third-cycle repair hypothesis without restarting or redeploying WH09.
```

## Recovery checkpoint

```yaml
recovery:
  policy_version: 1
  generation: 3
  session_id: 2026-08-10T21:04+02:00
  session_started_at: 2026-08-10T21:04:00+02:00
  checkpointed_at: 2026-08-10T21:12:00+02:00
  last_progress_at: 2026-08-10T21:09:23+02:00
  phase: wh09_readonly_health_diagnostic
  exact_head: c2a4d5cee3bb6f3225d0d2cd13de63b2ca7878c0
  pull_request: none
  active_operation: Portal WickHunter WH09 Readonly Health Diagnostic
  external_run_ids:
    - 31422691173
  operation_started_at: 2026-08-10T21:09:23+02:00
  wait_deadline_at: 2026-08-10T21:19:23+02:00
  check_generation: wh09-health-diagnostic-v3
  checks_used: 2
  status: waiting
  safe_to_resume: true
  resume_condition: workflow run 31422691173 is terminal
  next_action: Inspect run 31422691173 once on the next invocation and form exactly one third-cycle repair hypothesis from its primary evidence.
```

## Terminal closeout requirements

Do not set `status: completed` until all are true:

```yaml
closeout:
  implementation_complete: true
  vertical_slice_complete: true
  audit:
    result: PASS
    material_findings_open: 0
  e2e:
    result: PASS
    required_real_synology_adoption: true
  final_ci:
    result: PASS
    exact_head_required: true
  pull_requests:
    open_related_prs: 0
    unresolved_review_threads: 0
  issue_1396: closed_completed
  task_archived: true
  ownership_released: true
  stale_recovery_branch_reconciled: true
```
