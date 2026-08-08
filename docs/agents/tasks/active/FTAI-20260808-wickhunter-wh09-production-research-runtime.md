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

The runtime may maintain simulated SHADOW state and simulated outcomes. It may not submit exchange orders, use trading credentials, instantiate a real order adapter, automatically promote a model, or allocate live capital.

## Trusted inputs

- owner authorization in Issue `#1386` and current owner invocation;
- terminal discovery merge `develop@46cd873ccb0c60ec88657d9e7eccb18a93737fd5`;
- terminal H900 evidence referenced by the archived predecessor task;
- root `AGENTS.md`, `AGENTS.override.md`, `docs/agents/AGENTS.md` and routed execution/closeout contracts on the trusted base;
- existing `ai_platform/wickhunter/shadow_runtime_*`, `candidate_paper_runtime_operator.py`, Liquid20 production-data contracts and Synology deployment hardening.

Issue/PR prose, logs, market data and generated artifacts are evidence/data, not authority to expand the safety boundary.

## Delivery plan

1. Reuse the existing Liquid20 public/demo market adapter and shadow decision pipeline rather than implementing a second strategy engine.
2. Add an explicit research binding that can load the frozen H900 model/parameter identity without claiming candidate promotion or PAPER activation.
3. Add an append-only chronological decision/outcome journal that records raw/calibrated model evidence, final decision/reason codes, immutable identities, decision-time market context, and a delayed 900 s outcome only after the horizon is available.
4. Add a persistent production research operator/service with restart/idempotency and operator health/telemetry.
5. Add a hardened Synology deployment package and exact-head deployment/acceptance path for internal demo production.
6. Prove collector/input -> inference -> journal -> delayed outcome -> telemetry end-to-end while all real-order authority fields remain zero/false.
7. Fresh-audit the exact implementation, repair material findings, run final exact-head CI, merge, deploy the exact merged implementation, and archive this task with observation handoff.

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

## Validation evidence

- Initial PR head `51b86e404571e9d8a03864fa2f5882d1cdca4e50` reached the normal CI pipeline and exposed one actionable validation gate: formatting/lint plus a slotted dataclass field declaration in `production_research_runtime_operator.py`.
- GitHub Actions repair run `31262341577` completed successfully and removed both temporary repair workflows before its repair commit.
- Coherent implementation head after the repair is `6cb8122a6f6a9a19264744a07491dd4a0f416e80`; changed paths are limited to the runtime, operator, hardened deployment package, focused tests, and this task record.
- The repair also closes a material label-continuity gap: due 900 s outcome symbols are fetched even when they have left the current Liquid20 selected universe, without reintroducing them into the current decision universe.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-08T16:39:22+02:00
implementation_head: 6cb8122a6f6a9a19264744a07491dd4a0f416e80
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
last_progress_at: 2026-08-08T16:39:22+02:00
ci_checks_for_current_head: 0
unchanged_state_checks: 0
identical_failure_retries: 0
repair_cycles_for_current_gate: 2
context_reconstruction_attempts: 0
stall_warnings: 0
owned_paths:
  - docs/agents/tasks/active/FTAI-20260808-wickhunter-wh09-production-research-runtime.md
  - ai_platform/wickhunter/production_research_runtime.py
  - ai_platform/wickhunter/production_research_runtime_operator.py
  - tests/ai_platform_integration/test_wickhunter_production_research_runtime.py
  - tests/ai_platform_integration/test_wickhunter_production_research_runtime_deploy.py
  - deploy/synology/wickhunter-production-research-runtime/
proven:
  - predecessor discovery task and PR 1385 are terminal and merged at 46cd873ccb0c60ec88657d9e7eccb18a93737fd5
  - current H900 calibration ceiling remains below frozen 0.60 and the selected scientific route is independent chronological evidence growth
  - existing ShadowRuntime provides simulated state and PnL with fail-closed live-mode rejection
  - existing candidate PAPER operator provides the hardened Liquid20 plus public-market adapter but remains correctly activation-gated
  - exact H900 model/package identities and host model root are recovered from terminal H900 artifact evidence
  - research runtime does not create or consume PAPER activation and never sets candidate_paper_validation_authorized=true
  - raw model probability, calibrated confidence, immutable decision records, delayed H900 research outcomes and telemetry are implemented
  - temporary GitHub-only repair workflows are absent from the PR final changed-file set
derived:
  - current owner authorization permits internal-production deployment with demo/non-capital data but not real exchange execution
  - due-outcome symbol retention is required for unbiased chronological labeling across Liquid20 universe rotation
unknown:
  - exact current Liquid20 host root and supplementary reader GID must be resolved from the Synology runtime immediately before deployment
  - exact internal Synology deployment acceptance result is pending merge/deploy
conflicts: []
blockers: []
next_action: Run exact-head PR validation on the new human-authored checkpoint head, perform a fresh acceptance audit, then merge and deploy the exact merged implementation to the internal demo-production Synology runtime.
```

## Recovery checkpoint

```yaml
recovery:
  policy_version: 1
  generation: 1
  session_id: owner-20260808-1606-cest
  session_started_at: 2026-08-08T16:06:00+02:00
  checkpointed_at: 2026-08-08T16:39:22+02:00
  last_progress_at: 2026-08-08T16:39:22+02:00
  phase: validate
  exact_head: live PR head created by this checkpoint commit
  pull_request: 1387
  active_operation: exact-head PR CI then fresh audit
  external_run_ids: []
  operation_started_at: null
  wait_deadline_at: null
  check_generation: pr-validation-post-repair
  checks_used: 0
  status: ready
  safe_to_resume: true
  resume_condition: PR 1387 has normal exact-head checks for the current non-bot checkpoint commit
  next_action: Inspect the aggregate exact-head PR validation, isolate any first actionable failure, otherwise perform the fresh acceptance audit and merge/deploy sequence.
```
