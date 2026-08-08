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
branch: feat/wickhunter-wh09-production-research-runtime-20260808
related_issue: 1386
related_pr: 1387
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

- Predecessor discovery PR `#1385` is terminal and merged at `46cd873ccb0c60ec88657d9e7eccb18a93737fd5`; it selected independent chronological evidence growth rather than threshold weakening.
- The implementation reuses the existing Liquid20/public-market and `ShadowRuntime` foundations, keeps H900 in `BotMode.SHADOW`, forces `candidate_paper_validation_authorized=false`, and does not create or consume PAPER activation.
- The runtime records immutable self-hashed decisions containing raw LightGBM probability, calibrated confidence, final decision/reason codes and model/parameter/dataset/code identities; delayed directional outcomes are created only at/after 900 s.
- Due 900 s outcome symbols remain labelable after leaving the current Liquid20 selected universe without re-entering the current decision universe.
- The hardened Synology package is non-root/read-only/capability-dropped, mounts model and Liquid20 read-only, exposes no inbound port and contains no exchange credential/order-adapter path.
- Normal exact-head CI on `88b85b0ae675dd6526f80daba35cbbbe6de0d843` passed Freqtrade CI, Risk-aware component CI, CodeQL and zizmor.
- Fresh independent audit workflow run `31262860311`, job `93116251497`, completed `success` after running the two dedicated `tests/ai_platform_integration/test_wickhunter_production_research_runtime*.py` files: `8 passed`.
- The fresh audit also re-falsified frozen threshold/horizon, zero-authority fields, absence of PAPER activation, absence of API credentials/Docker socket/inbound ports, deployment hardening, compile, Ruff and Ruff-format.
- Audit finding `WH09-PRR-AUDIT-001`: the first dedicated audit attempt found an invalid test-only enum fixture (`CandidateAction.ENTER`); severity `low`, product impact `none`, disposition `fixed`. The corrected fixture uses `ENTER_LONG`; the rerun above passed. Open material findings: `0`.
- Temporary audit/repair workflows are absent from the current PR changed-file set.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-08T16:50:00+02:00
branch: feat/wickhunter-wh09-production-research-runtime-20260808
pr: 1387
status: validating
phase: validate
execution_mode: chat_github_actions
context_pressure: medium
context_growth: stable
decomposition_decision: phased
session_rotation_count: 0
invocation_started_at: 2026-08-08T16:06:00+02:00
last_progress_at: 2026-08-08T16:50:00+02:00
ci_checks_for_current_head: 0
unchanged_state_checks: 0
identical_failure_retries: 0
repair_cycles_for_current_gate: 2
context_reconstruction_attempts: 0
stall_warnings: 0
fresh_audit:
  result: PASS
  run_id: 31262860311
  job_id: 93116251497
  focused_tests: 8
  material_findings_open: 0
  repaired_findings:
    - WH09-PRR-AUDIT-001
owned_paths:
  - docs/agents/tasks/active/FTAI-20260808-wickhunter-wh09-production-research-runtime.md
  - ai_platform/wickhunter/production_research_runtime.py
  - ai_platform/wickhunter/production_research_runtime_operator.py
  - tests/ai_platform_integration/test_wickhunter_production_research_runtime.py
  - tests/ai_platform_integration/test_wickhunter_production_research_runtime_deploy.py
  - deploy/synology/wickhunter-production-research-runtime/
proven:
  - H900 research inference is bound to exact package/model/parameter/dataset/code identities
  - frozen no_trade_confidence remains 0.60 and PAPER candidate authorization remains false
  - immutable decision journaling, delayed H900 outcome labeling, restart persistence and zero-authority telemetry are implemented
  - fresh dedicated acceptance audit passes with zero open material findings
  - historical Synology deployment evidence resolves Liquid20 host root as /var/lib/freqtrade-staging-state/production-market-evidence-v2/latest; deployment must still discover its current numeric reader GID with stat
unknown:
  - exact internal Synology deployment acceptance result is pending merge/deploy
conflicts: []
blockers: []
next_action: Verify required CI on this exact checkpoint head; if green and reviews remain clean, merge PR 1387 and deploy the exact merged implementation to the internal demo-production Synology runtime.
```

## Recovery checkpoint

```yaml
recovery:
  policy_version: 1
  generation: 2
  session_id: owner-20260808-1606-cest
  session_started_at: 2026-08-08T16:06:00+02:00
  checkpointed_at: 2026-08-08T16:50:00+02:00
  last_progress_at: 2026-08-08T16:50:00+02:00
  phase: validate
  exact_head: live PR head created by this checkpoint commit
  pull_request: 1387
  active_operation: final exact-head PR CI
  external_run_ids: []
  operation_started_at: 2026-08-08T16:50:00+02:00
  wait_deadline_at: 2026-08-08T17:06:00+02:00
  check_generation: final-pr-validation
  checks_used: 0
  status: ready
  safe_to_resume: true
  resume_condition: required PR checks complete on the exact current head
  next_action: Inspect the aggregate required checks once; merge only if all merge gates pass, otherwise persist the first actionable failure or waiting state.
```
