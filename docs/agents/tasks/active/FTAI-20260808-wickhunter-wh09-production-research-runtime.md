# FTAI-20260808 — WH09 Production Research Runtime

```yaml
task_id: FTAI-20260808-wickhunter-wh09-production-research-runtime
project_lane: freqtrade-wickhunter
programme: WickHunter WH09
policy_version: 2
prompting_standard_version: 2.1
task_kind: implementation
feature_scope:
  type: data_pipeline
  user_facing: false
  backend_required: true
  frontend_required: false
  integration_required: true
  e2e_required: true
  completion_claim: internal_only
execution_mode: chat_github_actions
run_scope: autonomous_program
continuation_policy: continue_until_real_stop
task_completion_policy: finalize_archive_and_continue
implementation_authorized: true
internal_demo_production_deployment_authorized: true
status: validating
base_branch: develop
branch: diagnose/wickhunter-wh09-runtime-health-20260808
related_issue: 1386
related_pr: 1394
implementation_pr: 1387
implementation_merge_commit: ec0f53cc4df7dfcf008f5f7a4e6ab3733a2cefe5
prior_synology_compat_pr: 1392
prior_synology_compat_merge_commit: c64df386a4fa3ba739b6eaa1a223ca798a7bcae2
no_trade_confidence: 0.60
protected_holdout_accessed: false
test_used_for_selection: false
automatic_promotion_enabled: false
trading_credentials_present: false
order_adapter_present: false
real_exchange_execution_enabled: false
orders_submitted: 0
live_capital_authorized: false
```

## Objective

Deploy one persistent internal-production WH09 research/SHADOW runtime using demo/non-capital data that continuously observes the existing Liquid20 market-data path, performs frozen H900 model inference without weakening `no_trade_confidence=0.60`, journals every eligible decision including `NO_TRADE`, and materializes leakage-safe research outcomes after the frozen `900 s` horizon for future challenger training and operator observation.

The runtime may maintain simulated SHADOW state and outcomes. It may not submit exchange orders, use trading credentials, instantiate a real order adapter, automatically promote a model, or allocate live capital.

## Acceptance inventory

- `A1`: frozen threshold remains exactly `0.60`; no threshold override or bypass exists.
- `A2`: research model identity is explicit and immutable; loading it does not create candidate/PAPER promotion state.
- `A3`: every eligible live/demo decision is durably journaled, including `NO_TRADE`, with model/parameter/dataset/code identities and reason codes.
- `A4`: raw model probability and calibrated confidence are both available in research telemetry without changing execution semantics.
- `A5`: 900 s outcomes are materialized only after the horizon from chronological observations; future data cannot enter decision-time features. Due directional observations remain labelable even after their symbol leaves the current Liquid20 universe.
- `A6`: restart is idempotent and does not duplicate immutable decision/outcome records.
- `A7`: operator telemetry exposes health, decision/no-trade counts, confidence distribution summary, labeled outcome statistics, model/data identities and zero-authority state.
- `A8`: deployment is hardened, internal, demo/non-capital, and contains no trading credential/order/exchange-execution path.
- `A9`: focused/component tests, fresh audit and real internal deployment E2E pass on the exact implementation.
- `A10`: final merged/deployed state records `automatic_promotion_enabled=false`, `trading_credentials_present=false`, `order_adapter_present=false`, `real_exchange_execution_enabled=false`, `orders_submitted=0`, `live_capital_authorized=false`.

## Frozen H900 identity

```yaml
package_id: wickhunter-wh09-candidate-materialization-20260808-r1-h900s-7b23a958fd4d
package_manifest_sha256: 9f5ba852e33915678ca085c2eeafbf526457a079ba8f6f2fb7c1097f1d20ab79
model_artifact_sha256: 0488eaea68a316e3659e3b9e2fcea667eb57de87a22888ce396d112a5c075d2e
model_hash: eddd12e3d0c5922547df89d9fa3d8556b8131a62c3cb8057c5a20c66747a240b
parameter_hash: 014b471b9ccc663c3551a151353ae7cd932bd43ed48b9fbf239baad3483e2c11
runtime_commit: ec0f53cc4df7dfcf008f5f7a4e6ab3733a2cefe5
```

## Evidence and current diagnostic state

- Runtime implementation PR `#1387` merged at `ec0f53cc4df7dfcf008f5f7a4e6ab3733a2cefe5`; dedicated implementation audit run `31262860311`, job `93116251497`, passed with zero open material findings.
- Deployment-control/retry work `#1390` and `#1391` established the protected Synology route and exact-image semantics.
- Synology compatibility PR `#1392` merged at `c64df386a4fa3ba739b6eaa1a223ca798a7bcae2`, removing only the unsupported CPU-CFS/NanoCPUs quota.
- Protected deployment run `31275253098`, job `93147659559`, passed immutable authorization, authorized Compose snapshot, exact runtime checkout, credential/zero-authority/host-path checks and successfully created/started the WH09 container.
- Exact deployed identity from that run: container `6724290d3078f09fc82c434e239d2d8afd3686ddedd27ff7d400834538cfbfe0`; image `sha256:c5a67281912e262a183dd7a5804609a2f69ca356d5eb98e4a5a8da169e07a749`; source revision `ec0f53cc4df7dfcf008f5f7a4e6ab3733a2cefe5`.
- Final E2E verification timed out after 720 seconds with `WH09 deployment E2E did not reach two advances: health is not a regular file`; no PASS report was emitted.
- Synology also discarded the requested PIDs limit because the kernel/cgroup lacks that capability; this remains a separate hardening caveat before final acceptance.
- PR `#1394` keeps diagnostics inside the existing registered WH09 deployment workflow. Diagnostic v4 now classifies mode across the whole push exclusively through each commit's `added`, `modified`, and `removed` filename arrays, so commit message or author metadata cannot switch deployment mode.
- Diagnostic v4 binds the exact failed run/job, original 64-character container ID and exact image ID. Container discovery uses `docker ps -aq --no-trunc` before exact comparison. The diagnostic job contains no start/stop/restart/recreate/remove/kill path and uploads evidence with `if: always()`.
- All diagnostic workflow/test P1/P2 findings are repaired and resolved as of diagnostic code head `6f02ed7c70b04fd0964fde462abc6cb860de34d3`; focused static regression coverage requires changed-file-array-only routing and forbids whole-commit serialization.
- Recovery does not treat that functional parent as merge authority: any replacement worker must resolve the current live PR #1394 head and require exact-final-head CI before merge.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-08T23:05:00+02:00
branch: diagnose/wickhunter-wh09-runtime-health-20260808
pr: 1394
status: validating
phase: diagnose
execution_mode: chat_github_actions
context_pressure: medium
context_growth: stable
session_rotation_count: 3
invocation_started_at: 2026-08-08T22:51:00+02:00
last_progress_at: 2026-08-08T23:05:00+02:00
ci_checks_for_current_head: 0
unchanged_state_checks: 0
identical_failure_retries: 0
repair_cycles_for_current_gate: 1
repair_cycle_generation: recovery_live_head_semantics
latest_deployment:
  run_id: 31275253098
  job_id: 93147659559
  authorization_commit: c64df386a4fa3ba739b6eaa1a223ca798a7bcae2
  runtime_commit: ec0f53cc4df7dfcf008f5f7a4e6ab3733a2cefe5
  container_id: 6724290d3078f09fc82c434e239d2d8afd3686ddedd27ff7d400834538cfbfe0
  image_id: sha256:c5a67281912e262a183dd7a5804609a2f69ca356d5eb98e4a5a8da169e07a749
  container_started: true
  first_actionable_failure: runtime_health_file_absent_after_container_start
  additional_platform_warning: pids_limit_discarded_by_synology_kernel
diagnostic:
  pr: 1394
  exact_code_head: 6f02ed7c70b04fd0964fde462abc6cb860de34d3
  request: diagnose-wh09-production-research-20260808-v4.json
  whole_push_classification: true
  changed_file_arrays_only: true
  deploy_job_skipped_for_v4: true
  container_recreate_authorized: false
  expected_container_id: 6724290d3078f09fc82c434e239d2d8afd3686ddedd27ff7d400834538cfbfe0
  expected_image_id: sha256:c5a67281912e262a183dd7a5804609a2f69ca356d5eb98e4a5a8da169e07a749
proven:
  - H900 model/runtime identities remain frozen
  - no_trade_confidence remains 0.60
  - PAPER and all real trading authority remain disabled
  - exact WH09 container can be created and started on internal Synology
  - diagnostic path cannot recreate the container
  - diagnostic/deploy mode selection ignores commit metadata and uses changed-file arrays only
unknown:
  - why the started container never produced health.json
  - whether telemetry.json exists independently
  - whether the exact container is currently running, restarting or exited
  - whether an enforceable alternative to PIDs limiting exists on this Synology kernel
conflicts: []
blockers: []
next_action: Resolve live PR #1394 head, require exact-final-head CI plus fresh independent review, then merge only if green and consume diagnostic v4 evidence before any redeploy.
```

## Recovery checkpoint

```yaml
recovery:
  policy_version: 1
  generation: 8
  session_id: owner-20260808-2251-cest
  session_started_at: 2026-08-08T22:51:00+02:00
  checkpointed_at: 2026-08-08T23:05:00+02:00
  last_progress_at: 2026-08-08T23:05:00+02:00
  phase: diagnose
  diagnostic_code_head: 6f02ed7c70b04fd0964fde462abc6cb860de34d3
  live_head_source: pr_1394
  exact_final_head_required: true
  parent_checkpoint_head: d52e1a93d49ee29d0b883b783f1de062b3b67153
  parent_checkpoint_role: documentation_predecessor_only
  pull_request: 1394
  active_operation: resolve live PR head, validate that exact final head, then perform diagnostic-only merge
  external_run_ids:
    - 31275253098
    - 93147659559
  operation_started_at: 2026-08-08T23:05:00+02:00
  wait_deadline_at: 2026-08-08T23:50:00+02:00
  check_generation: runtime-health-diagnostic-v4-final-live-head
  checks_used: 0
  status: active
  safe_to_resume: true
  resume_condition: resolve PR 1394 live head, then require required CI and fresh review on that exact head with zero material findings
  next_action: Query PR 1394 live head; never use diagnostic_code_head as merge authority. Merge only after exact-final-head checks are green and no material review finding remains, then consume diagnostic evidence before any redeploy.
```
