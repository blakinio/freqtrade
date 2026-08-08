# FTAI-20260808 — WH09 Production Research Runtime

```yaml
task_id: FTAI-20260808-wickhunter-wh09-production-research-runtime
project_lane: freqtrade-wickhunter
programme: WickHunter WH09
policy_version: 2
prompting_standard_version: 2.1
task_kind: implementation
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
automatic_promotion_enabled: false
trading_credentials_present: false
order_adapter_present: false
real_exchange_execution_enabled: false
orders_submitted: 0
live_capital_authorized: false
```

## Objective and frozen acceptance

Deploy one persistent internal-production WH09 research/SHADOW runtime using demo/non-capital data. It must observe the canonical Liquid20 path, run the frozen H900 model, journal every eligible decision including `NO_TRADE`, materialize leakage-safe outcomes only after 900 seconds, expose durable health/telemetry, survive restart idempotently, and prove zero trading authority. The frozen threshold remains `0.60`; PAPER activation, credentials, order adapters, real execution, automatic promotion and live capital remain forbidden.

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
- The same start reported that Synology discarded the requested PIDs limit because the kernel/cgroup lacks that capability. This remains a hardening caveat that must be resolved or explicitly dispositioned before final acceptance.
- PR `#1394` keeps diagnostics inside the existing registered WH09 deployment workflow. A merge adding/modifying diagnostic request v4 skips deploy and runs only the read-only diagnostic job; removing v4 also fails closed and cannot start deploy.
- Diagnostic request v4 is immutable and binds inspection to the exact failed run/job, exact original container ID and exact image ID. The diagnostic job contains no container start/stop/restart/recreate/remove/kill path and uploads evidence with `if: always()`.
- Prior review P2 `Bind inspection to the deployed image and container` is resolved by exact container/image binding.
- Final diagnostic workflow/request/test code head is `7c08031c12ad789f7d44d47105b27592cab27d70`. This checkpoint commit is documentation-only.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-08T22:27:00+02:00
branch: diagnose/wickhunter-wh09-runtime-health-20260808
pr: 1394
status: validating
phase: diagnose
execution_mode: chat_github_actions
context_pressure: medium
context_growth: stable
session_rotation_count: 2
invocation_started_at: 2026-08-08T21:04:00+02:00
last_progress_at: 2026-08-08T22:27:00+02:00
ci_checks_for_current_head: 0
unchanged_state_checks: 0
identical_failure_retries: 0
repair_cycles_for_current_gate: 2
repair_cycle_generation: runtime_health_absent_diagnostic_v4
repair_cycle_reset_reason: materially_new_failure_signature_after_successful_container_start
latest_deployment:
  run_id: 31275253098
  job_id: 93147659559
  authorization_commit: c64df386a4fa3ba739b6eaa1a223ca798a7bcae2
  runtime_commit: ec0f53cc4df7dfcf008f5f7a4e6ab3733a2cefe5
  container_id: 6724290d3078f09fc82c434e239d2d8afd3686ddedd27ff7d400834538cfbfe0
  image_id: sha256:c5a67281912e262a183dd7a5804609a2f69ca356d5eb98e4a5a8da169e07a749
  container_started: true
  first_actionable_failure: runtime_health_file_absent_after_container_start
  terminal_error: health_is_not_a_regular_file
  additional_platform_warning: pids_limit_discarded_by_synology_kernel
diagnostic:
  pr: 1394
  exact_code_head: 7c08031c12ad789f7d44d47105b27592cab27d70
  checkpoint_successor_scope: documentation_only
  request: diagnose-wh09-production-research-20260808-v4.json
  integrated_workflow: .github/workflows/ai-platform-wickhunter-wh09-production-research-runtime-deploy.yml
  deploy_job_skipped_for_v4: true
  removal_fail_closed: true
  container_recreate_authorized: false
  expected_container_id: 6724290d3078f09fc82c434e239d2d8afd3686ddedd27ff7d400834538cfbfe0
  expected_image_id: sha256:c5a67281912e262a183dd7a5804609a2f69ca356d5eb98e4a5a8da169e07a749
proven:
  - H900 model/runtime identities remain frozen
  - no_trade_confidence remains 0.60
  - PAPER and all real trading authority remain disabled
  - exact WH09 container can be created and started on internal Synology
  - diagnostic path cannot recreate the container
unknown:
  - why the started container never produced health.json
  - whether telemetry.json exists independently
  - whether the exact container is currently running, restarting or exited
  - whether an enforceable alternative to PIDs limiting exists on this Synology kernel
conflicts: []
blockers: []
next_action: Complete exact-head CI and fresh review of PR 1394; merge only if green, run diagnostic v4 on Synology, then repair only the first proven runtime/root-path cause and separately disposition the unsupported PIDs-limit control.
```

## Recovery checkpoint

```yaml
recovery:
  policy_version: 1
  generation: 6
  session_id: owner-20260808-2104-cest
  session_started_at: 2026-08-08T21:04:00+02:00
  checkpointed_at: 2026-08-08T22:27:00+02:00
  last_progress_at: 2026-08-08T22:27:00+02:00
  phase: diagnose
  exact_head: 7c08031c12ad789f7d44d47105b27592cab27d70
  exact_head_role: final_diagnostic_workflow_request_and_test_head
  checkpoint_successor_scope: documentation_only
  pull_request: 1394
  active_operation: exact-head validation and read-only Synology diagnostic merge
  external_run_ids:
    - 31275253098
    - 93147659559
  operation_started_at: 2026-08-08T22:25:00+02:00
  wait_deadline_at: 2026-08-08T23:10:00+02:00
  check_generation: runtime-health-diagnostic-v4-final
  checks_used: 0
  status: active
  safe_to_resume: true
  resume_condition: required PR 1394 checks and fresh independent review complete; live head may be documentation-only successor
  next_action: Reconcile live PR head and required checks; if green with no material finding, merge PR 1394 and consume the diagnostic evidence before any redeploy.
```
