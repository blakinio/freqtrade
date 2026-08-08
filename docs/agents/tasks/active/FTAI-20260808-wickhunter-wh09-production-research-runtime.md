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
branch: fix/wickhunter-wh09-synology-cpu-cfs-compat-20260808
related_issue: 1386
related_pr: 1392
implementation_pr: 1387
implementation_merge_commit: ec0f53cc4df7dfcf008f5f7a4e6ab3733a2cefe5
prior_deployment_control_pr: 1390
prior_deployment_retry_pr: 1391
prior_deployment_retry_merge_commit: 286376990bf9afeb1832f1d643a2b3dd6d2e12d5
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
- Fresh implementation audit run `31262860311`, job `93116251497`, passed the dedicated WH09 runtime tests with zero open material findings after the test-only `CandidateAction.ENTER` fixture was corrected to `ENTER_LONG`.
- Deployment-control PR `#1390` merged as `3af40aaa3820c91fdf8382e2a8cd61577babb90d`. Its first protected deployment run `31268955706` was cancelled by the former 20-minute image-export budget.
- Deployment-retry PR `#1391` merged as `286376990bf9afeb1832f1d643a2b3dd6d2e12d5`. It preserved the exact runtime identity, exact-image reuse/rebuild and Compose `--no-build` startup; final required CI and review gates passed before merge.
- Protected deploy run `31273808566`, job `93144045334`, passed immutable authorization, exact runtime checkout, runner identity, credential/proxy absence, zero-authority checks, Liquid20 identity/path validation and exact-image identity. Container creation then failed with Docker daemon error `NanoCPUs can not be set, as your kernel does not support CPU CFS scheduler or the cgroup is not mounted`.
- The new failure is materially different from the prior image-export/Compose deadline failure. It is isolated to Synology kernel/cgroup incompatibility with Compose `cpus: 2.0`; it does not change model science or trading authority.
- Repair PR `#1392` is bounded to removing the CPU-CFS/NanoCPUs quota while retaining memory/PID limits and all other container/security/SHADOW safeguards, plus immutable retry request v3 bound to run `31273808566` / job `93144045334`.
- Exact deployment/config/test repair head is `486bafff6e1e3b0822ee144581a33eb589a032eb`. The following checkpoint commit is documentation-only.
- The workflow repair snapshots the authorized deployment Compose before checking out exact runtime commit `ec0f53cc...`, builds/reuses the image from the untouched exact runtime source, then restores only the authorized Synology-compatible Compose for `docker compose config/up`.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-08T21:23:00+02:00
branch: fix/wickhunter-wh09-synology-cpu-cfs-compat-20260808
pr: 1392
status: validating
phase: validate
execution_mode: chat_github_actions
context_pressure: medium
context_growth: stable
decomposition_decision: phased
session_rotation_count: 2
invocation_started_at: 2026-08-08T21:04:00+02:00
last_progress_at: 2026-08-08T21:23:00+02:00
ci_checks_for_current_head: 0
unchanged_state_checks: 0
identical_failure_retries: 0
repair_cycles_for_current_gate: 1
repair_cycle_generation: synology_cpu_cfs_compat
repair_cycle_reset_reason: materially_new_failure_signature_after_successful_exact_image_and_predeploy_validation
context_reconstruction_attempts: 1
stall_warnings: 0
failed_deployment:
  run_id: 31273808566
  job_id: 93144045334
  authorization_commit: 286376990bf9afeb1832f1d643a2b3dd6d2e12d5
  runtime_commit: ec0f53cc4df7dfcf008f5f7a4e6ab3733a2cefe5
  first_actionable_failure: synology_kernel_rejects_nanocpus_without_cpu_cfs
  passed_before_failure:
    - immutable deployment authorization
    - exact runtime checkout
    - runner and host-path validation
    - credential/proxy absence
    - zero trading authority
    - exact runtime image identity
repair:
  pr: 1392
  exact_code_head: 486bafff6e1e3b0822ee144581a33eb589a032eb
  checkpoint_successor_scope: documentation_only
  strategy: remove_cpu_cfs_quota_only_and_deploy_authorized_compose_after_exact_image_identity
  immutable_retry_request: retry-wh09-production-research-20260808-v3.json
owned_paths:
  - docs/agents/tasks/active/FTAI-20260808-wickhunter-wh09-production-research-runtime.md
  - ai_platform/wickhunter/production_research_runtime.py
  - ai_platform/wickhunter/production_research_runtime_operator.py
  - tests/ai_platform_integration/test_wickhunter_production_research_runtime.py
  - tests/ai_platform_integration/test_wickhunter_production_research_runtime_deploy.py
  - deploy/synology/wickhunter-production-research-runtime/
  - .github/workflows/ai-platform-wickhunter-wh09-production-research-runtime-deploy.yml
  - .github/workflow-registry.yaml
proven:
  - H900 research inference is bound to exact package/model/parameter/dataset/code identities
  - frozen no_trade_confidence remains 0.60 and PAPER candidate authorization remains false
  - immutable decision journaling, delayed H900 outcome labeling, restart persistence and zero-authority telemetry are implemented
  - fresh dedicated implementation audit passes with zero open material findings
  - implementation PR 1387 is merged at ec0f53cc4df7dfcf008f5f7a4e6ab3733a2cefe5
  - canonical Liquid20 live source is active and passed deployment preflight in run 31273808566
  - PR 1391 merged at 286376990bf9afeb1832f1d643a2b3dd6d2e12d5 after exact-head CI and review
unknown:
  - internal Synology deployment E2E remains unproven because container creation stopped before health/two-cycle verification
conflicts: []
blockers: []
next_action: Complete exact-head CI and fresh review of PR 1392; if green with no material findings, merge it and verify the protected retry-v3 Synology SHADOW deployment reaches healthy state plus two post-start advances with zero trading authority.
```

## Recovery checkpoint

```yaml
recovery:
  policy_version: 1
  generation: 5
  session_id: owner-20260808-2104-cest
  session_started_at: 2026-08-08T21:04:00+02:00
  checkpointed_at: 2026-08-08T21:23:00+02:00
  last_progress_at: 2026-08-08T21:23:00+02:00
  phase: validate
  exact_head: 486bafff6e1e3b0822ee144581a33eb589a032eb
  exact_head_role: final_deployment_config_workflow_and_test_head
  checkpoint_successor_scope: documentation_only
  pull_request: 1392
  active_operation: exact-head CI and fresh independent review for bounded Synology CPU-CFS compatibility repair
  external_run_ids:
    - 31273808566
    - 93144045334
  operation_started_at: 2026-08-08T21:20:48+02:00
  wait_deadline_at: 2026-08-08T22:05:00+02:00
  check_generation: synology-cpu-cfs-compat-final-validation
  checks_used: 0
  status: active
  safe_to_resume: true
  resume_condition: required PR 1392 checks and fresh independent review complete; live PR head may be a documentation-only successor and must be reconciled from GitHub before merge
  next_action: If exact-head required checks are green and review has no material finding, merge PR 1392 and verify the triggered retry-v3 Synology deployment E2E; otherwise repair only the first actionable failure.
```
