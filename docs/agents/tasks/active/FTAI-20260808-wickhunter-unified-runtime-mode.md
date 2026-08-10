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
status: validating
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

Terminally close Issue #1396 by recovering the existing WH09 runtime from its proven upstream Liquid20 integrity fault, then proving the already-merged unified WickHunter runtime-mode implementation through the real Synology Portal adoption path without replacing or restarting WH09 and without expanding trading authority.

ADR-022 on the current trusted `develop` makes PAPER the only authorized operational trading mode and permits SHADOW only as bounded validation. This task's frozen WH09 SHADOW runtime is an existing validation runtime; it is not a new promotion stage and this recovery does not authorize LIVE.

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

Do not create a second runtime, activate PAPER for WH09, authorize LIVE, add credentials or a real order adapter, submit exchange orders, weaken fail-closed behavior, perform broad Docker cleanup, or restart/recreate/redeploy WH09 unless a proven cause and trusted repository authority explicitly require that exact operation.

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

## Runtime failure evidence

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
  generation: 645
  last_observation_age_seconds: 8023.462
  telemetry_age_seconds: 8023.462
  process_alive: true
  zero_authority: true
  wh09_mutation: false
root_cause_diagnostic:
  run: 31425261462
  job: 93575331867
  result: PASS_READ_ONLY
  wh09_error_code: CandidatePaperRuntimeOperatorError
  wh09_error_message: Liquid20 source events binance-usdm contradicts events_written
  liquid20_container_running: true
  liquid20_restart_count: 0
  liquid20_revision: 416223a803c6eb803e09429b3368488276a112e9
  liquid20_pointer_fresh: true
  active_run: liquid20-20260810T000000Z-3
  active_run_state: active
  pointer_persisted_state_equal: true
  current_sources_connected_and_fresh: true
  zero_authority: true
  wh09_supervisor_advancing_health_timestamp: true
  wh09_generation_still_blocked: 645
  wh09_mutation: false
integrity_isolation:
  run: 31425883292
  job: 93577345378
  result: PASS_READ_ONLY
  corrupt_completed_run: liquid20-20260810T000000Z-1
  completion_reason: collector-restart
  binance_usdm:
    events_written: 7878
    durable_rows: 7883
    uncommitted_suffix_rows: 5
  bybit_linear:
    events_written: 3513
    durable_rows: 3514
    uncommitted_suffix_rows: 1
  okx_swap:
    events_written: 3068
    durable_rows: 3068
    uncommitted_suffix_rows: 0
  all_other_relevant_runs_exact: true
  active_run_exact: true
  loader_reproduced_same_error: true
  wh09_mutation: false
```

## Proven root cause

`FACT`: `liquid20-20260810T000000Z-1` was finalized as `completed` with `completion_reason=collector-restart` while Binance and Bybit NDJSON contained a small durable suffix beyond the last committed `events_written` boundary. WH09 intentionally requires an exact row count for completed historical runs and therefore correctly fails closed.

`FACT`: production Liquid20 revision `416223a803c6eb803e09429b3368488276a112e9` writes NDJSON independently from state persistence and `_complete_previous_active_run()` previously changed an old `active` run to `completed` without sealing its files to the persisted commit boundary. This permits a process interruption after NDJSON flush but before the next state commit to turn an uncommitted suffix into an apparently committed historical file.

`FACT`: the current active Liquid20 run is healthy, fresh and exact. The fault is historical restart durability, not source freshness, mount access, pointer/run-state inconsistency, model binding, WH09 process death, or the previously observed Portal BuildKit failure.

## Permanent repair

Working branch was reconciled with trusted `develop@5a19ae32f1f71b112130ea66cb8d56d9a3e44049` by merge commit `bf9927579032538a5b53bb09fde8332207b96d35`; it is no longer behind the trusted base.

Permanent producer repair:

- commit `4fb2b70b609e5d263d4c76489f0f6cf82905e9fe` adds restart sealing to `ai_platform/scripts/liquidation_live_stream.py`;
- the persisted `events_written` value is treated as the committed row boundary;
- on collector restart, each previous active source file is verified to contain at least the committed rows;
- bytes after the committed row boundary are truncated and fsynced before the run can be finalized as historical;
- missing committed rows, malformed state, symlinks or non-regular files fail closed rather than creating a new run;
- no WH09 contract or fail-closed threshold is weakened.

Focused regression coverage:

- commit `0480412ac5c1f59e5ce99fdb95a6a996b49ae27c` adds `tests/ai_platform_integration/test_liquidation_live_restart_durability.py`;
- one test proves only the uncommitted suffix is removed and the old run is then completed;
- one test proves missing committed rows block restart and preserve the old active pointer without creating a new run.

The already-completed historical run `liquid20-20260810T000000Z-1` still requires one separately guarded, exact-data repair after the permanent fix is validated and integrated: verify the exact known counts/run identity, truncate only Binance's 5-row and Bybit's 1-row uncommitted suffix to their persisted commit boundaries, fsync, re-count exact equality, and leave state metadata unchanged. No broad data cleanup is permitted.

## Temporary workflow

`.github/workflows/portal-wickhunter-buildkit-cache-recovery.yml` is temporary recovery instrumentation only. It currently contains the bounded read-only integrity diagnostic used for run `31425883292`. It must be removed before final merge/closeout and cannot serve as exact-head final CI after removal.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-10T22:16:00+02:00
head: 1bb288c9e7f4f8b858b5cdd3054f8d09b27ab61a
branch: fix/wickhunter-1396-synology-recovery-v2
pr: 1450
status: validating
context_routes:
  - docs/agents/PROMPTING_STANDARD.md
  - docs/agents/PROMPTING_HANDOVER.md
  - docs/agents/DELIVERY_COMPLETENESS_AND_CLOSEOUT.md
  - docs/agents/ANTI_STALL_AND_EXECUTION_BUDGET.md
  - ai_platform/scripts/liquidation_live_stream.py
  - tests/ai_platform_integration/test_liquidation_live_restart_durability.py
  - Issue #1396 and PR #1450
owned_paths:
  - ai_platform/scripts/liquidation_live_stream.py
  - tests/ai_platform_integration/test_liquidation_live_restart_durability.py
  - docs/agents/tasks/active/FTAI-20260808-wickhunter-unified-runtime-mode.md
  - .github/workflows/portal-wickhunter-buildkit-cache-recovery.yml
proven:
  - PRs 1397 1388 and 1436 are merged and PR 1443 remains closed unmerged
  - WH09 remains the single expected H900 SHADOW container with zero trading authority
  - WH09 exact cycle failure is Liquid20 source events binance-usdm contradicts events_written
  - current Liquid20 active pointer sources and mount readability are fresh and internally consistent
  - completed restart run liquid20-20260810T000000Z-1 is the only relevant row-count inconsistency isolated by the read-only audit
  - binance-usdm has five durable rows beyond persisted events_written in that completed restart run
  - bybit-linear has one durable row beyond persisted events_written in that completed restart run
  - production restart finalization did not seal durable NDJSON suffixes to the persisted commit boundary
  - producer repair seals to events_written before historical finalization and fails closed on missing committed rows
  - dangling source symlinks are rejected before the zero-row missing-file shortcut
  - focused restart durability regression coverage passes after the review repair
derived:
  - after the permanent producer fix is integrated a guarded repair of only the already completed inconsistent history should allow WH09 to recover naturally without weakening fail-closed behavior
unknown:
  - final exact-head PR 1450 standard CI result after temporary workflow removal
  - canonical post-merge Liquid20 Synology deployment result
  - guarded completed-history repair result on the Synology runtime
  - whether WH09 returns healthy naturally with two consecutive successful generation advances after upstream repair
  - whether the prior Portal BuildKit context failure recurs after WH09 recovery
  - terminal Portal adoption API browser persistence and desired-observed generation result
  - final independent audit exact-head CI archive and Issue closure result
conflicts: []
first_failure:
  marker: LIQUID20_RESTART_COMMIT_BOUNDARY_MISMATCH
  evidence: run 31425261462 exposed the exact WH09 error and run 31425883292 isolated the completed restart run with plus five Binance rows and plus one Bybit row beyond persisted commit counts
rejected_hypotheses:
  - the current WH09 blocker is the earlier Portal BuildKit failure
  - current Liquid20 pointer freshness or active run state is stale or inconsistent
  - WH09 has stopped running or restarted
  - weakening WH09 completed-history row-count validation is an acceptable repair
changed_paths:
  - ai_platform/scripts/liquidation_live_stream.py
  - tests/ai_platform_integration/test_liquidation_live_restart_durability.py
  - docs/agents/tasks/active/FTAI-20260808-wickhunter-unified-runtime-mode.md
  - .github/workflows/portal-wickhunter-buildkit-cache-recovery.yml
validation:
  - command: Read-only WH09 root-cause diagnostic
    result: PASS
    evidence: GitHub Actions run 31425261462 job 93575331867
  - command: Read-only Liquid20 integrity isolation
    result: PASS
    evidence: GitHub Actions run 31425883292 job 93577345378
  - command: Focused restart durability pytest before review repair
    result: PASS
    evidence: run 31427098950 job 93581282842 reported two passing tests before the later lint-only failure
  - command: Dangling symlink fail-closed review repair workflow
    result: PASS
    evidence: GitHub Actions run 31427855045 job 93583737395 completed source repair lint format and focused regression validation
blockers: []
next_action: Complete PR 1450 exact-head validation and review, remove the temporary recovery workflow, merge only when gates pass, then observe canonical Liquid20 deployment before applying the single guarded completed-history commit-boundary repair through the protected Synology environment.
```

## Recovery checkpoint

```yaml
recovery:
  policy_version: 1
  generation: 5
  session_id: 2026-08-10T21:37+02:00
  session_started_at: 2026-08-10T21:37:00+02:00
  checkpointed_at: 2026-08-10T22:02:00+02:00
  last_progress_at: 2026-08-10T22:02:00+02:00
  phase: liquid20_restart_durability_repair_validation
  exact_head_before_checkpoint_commit: bf9927579032538a5b53bb09fde8332207b96d35
  pull_request: none
  active_operation: permanent producer repair validation
  external_run_ids:
    - 31425261462
    - 31425883292
  checks_used: 0
  status: active
  safe_to_resume: true
  resume_condition: permanent repair and focused tests validated
  next_action: Run focused validation for the Liquid20 restart-sealing repair, then open the task repair PR against current develop.
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
