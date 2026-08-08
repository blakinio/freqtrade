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
decomposition_decision: phased
execution_mode: chat_github_actions
run_scope: autonomous_program
continuation_policy: continue_until_real_stop
task_completion_policy: finalize_archive_and_continue
implementation_authorized: true
internal_demo_production_deployment_authorized: true
status: validating
base_branch: develop
trusted_base_sha: 46cd873ccb0c60ec88657d9e7eccb18a93737fd5
branch: diagnose/wickhunter-wh09-runtime-health-20260808
related_issue: 1386
related_pr: 1394
implementation_pr: 1387
implementation_merge_commit: ec0f53cc4df7dfcf008f5f7a4e6ab3733a2cefe5
prior_deployment_control_pr: 1390
prior_deployment_retry_pr: 1391
prior_synology_compat_pr: 1392
prior_synology_compat_merge_commit: c64df386a4fa3ba739b6eaa1a223ca798a7bcae2
upstream_discovery_issue: 1384
upstream_discovery_pr: 1385
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

Deploy one persistent internal-production WH09 research/shadow runtime using demo/non-capital data that continuously observes the existing Liquid20 market-data path, performs frozen H900 model inference without weakening `no_trade_confidence=0.60`, journals every eligible decision including `NO_TRADE`, and materializes leakage-safe research outcomes after the frozen `900 s` horizon for future challenger training and operator observation.

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

## H900 production-research identity

```yaml
package_id: wickhunter-wh09-candidate-materialization-20260808-r1-h900s-7b23a958fd4d
package_manifest_sha256: 9f5ba852e33915678ca085c2eeafbf526457a079ba8f6f2fb7c1097f1d20ab79
model_artifact_sha256: 0488eaea68a316e3659e3b9e2fcea667eb57de87a22888ce396d112a5c075d2e
model_version: wickhunter-lightgbm-eddd12e3d0c59225
model_hash: eddd12e3d0c5922547df89d9fa3d8556b8131a62c3cb8057c5a20c66747a240b
parameter_version: wickhunter-production-h900s-09
parameter_hash: 014b471b9ccc663c3551a151353ae7cd932bd43ed48b9fbf239baad3483e2c11
model_source_commit: 7b23a958fd4d2bb43569c7f693d2247ef43d1ae9
model_root_host: /var/lib/freqtrade-staging-state/wickhunter-candidate-materialization/packages/wickhunter-wh09-candidate-materialization-20260808-r1-h900s-7b23a958fd4d
```

## Implementation and validation evidence

- Discovery PR `#1385` merged at `46cd873ccb0c60ec88657d9e7eccb18a93737fd5`; it selected chronological evidence growth rather than weakening the frozen threshold.
- Runtime implementation PR `#1387` merged at `ec0f53cc4df7dfcf008f5f7a4e6ab3733a2cefe5` after exact-head CI and fresh audit. H900 remains `BotMode.SHADOW`, `candidate_paper_validation_authorized=false`, with immutable decision journals and delayed 900 s outcomes.
- Fresh implementation audit run `31262860311`, job `93116251497`, passed the dedicated WH09 runtime tests with zero open material findings.
- Deployment-control PR `#1390` and deployment-retry PR `#1391` established the protected Synology route and exact-image reuse/build semantics.
- Synology compatibility PR `#1392` merged at `c64df386a4fa3ba739b6eaa1a223ca798a7bcae2`; it removed only the unsupported CPU-CFS/NanoCPUs quota while retaining the remaining SHADOW hardening and exact runtime identity.
- Protected deployment run `31275253098`, job `93147659559`, then passed immutable authorization, authorized Compose snapshot, exact runtime checkout, runner/credential/zero-authority/host-path validation and container creation/start. The prior CPU-CFS failure is therefore resolved.
- The running container used exact image `wickhunter-production-research-runtime:ec0f53cc4df7` / image id `sha256:c5a67281912e262a183dd7a5804609a2f69ca356d5eb98e4a5a8da169e07a749` and exact runtime revision `ec0f53cc4df7dfcf008f5f7a4e6ab3733a2cefe5`.
- Final E2E verification in the same run failed after the full 720 s window with `WH09 deployment E2E did not reach two advances: health is not a regular file`. No deployment PASS report was emitted.
- The same container-start log reports `Your kernel does not support PIDs limit capabilities or the cgroup is not mounted. PIDs limit discarded.` This is a separate hardening caveat that must be resolved or explicitly dispositioned before claiming A8 complete.
- Diagnostic PR `#1394` is read-only with respect to the deployed container. It adds immutable diagnostic request v4 and a bounded self-hosted diagnostic workflow that does not recreate the container and captures only safe runtime state, restart/error status, expected mount metadata, health/telemetry file metadata and bounded container logs.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-08T22:05:00+02:00
branch: diagnose/wickhunter-wh09-runtime-health-20260808
pr: 1394
status: validating
phase: diagnose
execution_mode: chat_github_actions
context_pressure: medium
context_growth: stable
decomposition_decision: phased
session_rotation_count: 2
invocation_started_at: 2026-08-08T21:04:00+02:00
last_progress_at: 2026-08-08T22:05:00+02:00
ci_checks_for_current_head: 0
unchanged_state_checks: 0
identical_failure_retries: 0
repair_cycles_for_current_gate: 2
repair_cycle_generation: runtime_health_absent_diagnostic
repair_cycle_reset_reason: materially_new_failure_signature_after_successful_container_start
context_reconstruction_attempts: 1
stall_warnings: 0
latest_deployment:
  run_id: 31275253098
  job_id: 93147659559
  authorization_commit: c64df386a4fa3ba739b6eaa1a223ca798a7bcae2
  runtime_commit: ec0f53cc4df7dfcf008f5f7a4e6ab3733a2cefe5
  container_started: true
  first_actionable_failure: runtime_health_file_absent_after_container_start
  terminal_error: health_is_not_a_regular_file
  additional_platform_warning: pids_limit_discarded_by_synology_kernel
  passed_before_failure:
    - immutable diagnostic/deployment authorization
    - authorized Synology compose snapshot
    - exact runtime checkout
    - runner and host-path validation
    - credential absence and zero trading authority
    - exact runtime image identity
    - container creation and start
diagnostic:
  pr: 1394
  request: diagnose-wh09-production-research-20260808-v4.json
  container_recreate_authorized: false
  purpose: inspect_existing_container_state_logs_mounts_and_health_telemetry_files
owned_paths:
  - docs/agents/tasks/active/FTAI-20260808-wickhunter-wh09-production-research-runtime.md
  - ai_platform/wickhunter/production_research_runtime.py
  - ai_platform/wickhunter/production_research_runtime_operator.py
  - tests/ai_platform_integration/test_wickhunter_production_research_runtime.py
  - tests/ai_platform_integration/test_wickhunter_production_research_runtime_deploy.py
  - deploy/synology/wickhunter-production-research-runtime/
  - .github/workflows/ai-platform-wickhunter-wh09-production-research-runtime-deploy.yml
  - .github/workflows/ai-platform-wickhunter-wh09-synology-runtime-diagnostic.yml
  - .github/workflow-registry.yaml
proven:
  - H900 research inference is bound to exact package/model/parameter/dataset/code identities
  - frozen no_trade_confidence remains 0.60 and PAPER candidate authorization remains false
  - immutable decision journaling, delayed H900 outcome labeling, restart persistence and zero-authority telemetry are implemented in tested code
  - fresh dedicated implementation audit passes with zero open material findings
  - exact WH09 container can now be created and started on the internal Synology
unknown:
  - why the started container never produced /runtime/operator/health.json during 720 seconds
  - whether telemetry.json exists independently of health.json
  - whether the container is running, restarting or exited after the failed verification job
  - whether PIDs limiting can be enforced by an alternative mechanism on this Synology kernel
conflicts: []
blockers: []
next_action: Validate and merge diagnostic-only PR 1394, inspect the existing Synology container without recreation, then repair only the first proven runtime/root-path failure and separately disposition the unsupported PIDs-limit hardening control.
```

## Recovery checkpoint

```yaml
recovery:
  policy_version: 1
  generation: 6
  session_id: owner-20260808-2104-cest
  session_started_at: 2026-08-08T21:04:00+02:00
  checkpointed_at: 2026-08-08T22:05:00+02:00
  last_progress_at: 2026-08-08T22:05:00+02:00
  phase: diagnose
  exact_head: live PR 1394 head; resolve from GitHub before mutation
  pull_request: 1394
  active_operation: validate bounded read-only Synology diagnostics for existing WH09 container
  external_run_ids:
    - 31275253098
    - 93147659559
  operation_started_at: 2026-08-08T22:03:00+02:00
  wait_deadline_at: null
  check_generation: runtime-health-diagnostic-v4
  checks_used: 0
  status: active
  safe_to_resume: true
  resume_condition: PR 1394 exact-head CI/review permits diagnostic merge and the diagnostic run returns current container/log/filesystem evidence
  next_action: Merge PR 1394 only after required exact-head gates, consume its diagnostic evidence, and make no redeploy until the health-file absence cause is proven.
```
