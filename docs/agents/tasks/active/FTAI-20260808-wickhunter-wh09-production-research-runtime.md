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
status: implementing
base_branch: develop
trusted_base_sha: 46cd873ccb0c60ec88657d9e7eccb18a93737fd5
branch: feat/wickhunter-wh09-production-research-runtime-20260808
related_issue: 1386
related_pr: null
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

The runtime may maintain simulated PAPER state and simulated outcomes. It may not submit exchange orders, use trading credentials, instantiate a real order adapter, automatically promote a model, or allocate live capital.

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
- `A5`: 900 s outcomes are materialized only after the horizon from chronological observations; future data cannot enter decision-time features.
- `A6`: restart is idempotent and does not duplicate immutable decision/outcome records.
- `A7`: operator telemetry exposes health, decision/no-trade counts, confidence distribution summary, labeled outcome statistics, model/data identities and zero-authority state.
- `A8`: deployment is hardened, internal, demo/non-capital, and contains no trading credential/order/exchange-execution path.
- `A9`: focused/component tests, fresh audit and real internal deployment E2E pass on the exact implementation.
- `A10`: final merged/deployed state records `automatic_promotion_enabled=false`, `trading_credentials_present=false`, `order_adapter_present=false`, `real_exchange_execution_enabled=false`, `orders_submitted=0`, `live_capital_authorized=false`.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-08T16:11:00+02:00
head: initial_task_commit
branch: feat/wickhunter-wh09-production-research-runtime-20260808
pr: none
status: implementing
phase: implement
execution_mode: chat_github_actions
context_pressure: medium
context_growth: stable
decomposition_decision: phased
session_rotation_count: 0
invocation_started_at: 2026-08-08T16:06:00+02:00
last_progress_at: 2026-08-08T16:11:00+02:00
ci_checks_for_current_head: 0
unchanged_state_checks: 0
identical_failure_retries: 0
repair_cycles_for_current_gate: 0
context_reconstruction_attempts: 0
stall_warnings: 0
owned_paths:
  - docs/agents/tasks/active/FTAI-20260808-wickhunter-wh09-production-research-runtime.md
  - ai_platform/wickhunter/
  - tests/ai_platform_integration/
  - deploy/synology/wickhunter-production-research-runtime/
  - .github/workflows/
proven:
  - predecessor discovery task and PR 1385 are terminal and merged at 46cd873ccb0c60ec88657d9e7eccb18a93737fd5
  - current H900 calibration ceiling remains below frozen 0.60 and the selected scientific route is independent chronological evidence growth
  - existing ShadowRuntime already provides simulated positions, PnL, persistent state and fail-closed live-mode rejection
  - existing candidate paper operator already provides the hardened Liquid20 plus public-market feature adapter but is correctly candidate-activation gated
derived:
  - the smallest safe implementation is a research binding/journal/operator that reuses existing data and shadow components without bypassing candidate promotion
  - current owner authorization permits internal-production deployment with demo/non-capital data but not real exchange execution
unknown:
  - exact H900 model artifact host binding and current Synology deployment path must be resolved from existing trusted artifacts/workflows before deployment
conflicts: []
blockers: []
next_action: Implement the research binding, immutable decision/outcome journal, operator telemetry and hardened Synology deployment using the existing WickHunter and Liquid20 components, then open one PR for Issue 1386.
```
