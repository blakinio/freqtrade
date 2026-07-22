---
task_id: FTAI-20260722-rl-v2-runtime-integration
status: active
branch: feat/rl-v2-runtime-integration
base_branch: develop
created: 2026-07-22
updated: 2026-07-22
related_pr: "151"
owned_paths:
  - docs/agents/tasks/FTAI-20260722-rl-v2-runtime-integration.md
  - docs/ai_platform/RL_V2_RUNTIME_INTEGRATION.md
  - ai_platform/experimental_model_research/rl-v2-runtime-integration-v1.json
  - ai_platform/freqaimodels/DesiredPositionReinforcementLearner.py
  - ai_platform/strategies/AiDesiredPositionRLResearchStrategy.py
  - tests/ai_platform/test_rl_v2_runtime_integration.py
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260722-rl-v2-synthetic-implementation.md
  - docs/ai_platform/RL_V2_DESIGN_CONTRACT.md
  - docs/ai_platform/RL_V2_SYNTHETIC_IMPLEMENTATION.md
  - ai_platform/experimental_model_research/rl-v2-design-contract-v1.json
  - ai_platform/experimental_model_research/rl-v2-synthetic-implementation-v1.json
  - ai_platform/scripts/rl_v2_synthetic_reference.py
  - ai_platform/freqaimodels/LongOnlyReinforcementLearner.py
  - ai_platform/strategies/AiLongOnlyRLResearchStrategy.py
search_first:
  - current develop and open PRs before runtime integration work
  - active tasks or PRs overlapping RL-v2 model/strategy ownership
optional_reads:
  - freqtrade/freqai/prediction_models/ReinforcementLearner.py
  - freqtrade/freqai/RL/BaseEnvironment.py
---

# RL-v2 Runtime Integration

## Goal

Add a bounded, non-executing RL-v2 FreqAI runtime integration surface that reuses the frozen synthetic desired-position semantics, reward reference, and observability contract without performing training, backtesting, historical evaluation, or final-holdout access.

## Prospective runtime surface

The implementation task may add only:

- `DesiredPositionReinforcementLearner` and its two-action long-only environment adapter;
- `AiDesiredPositionRLResearchStrategy` mapping `target_long` to entry intent and `target_flat` to exit intent;
- a machine-readable runtime-integration descriptor;
- synthetic/static integration tests proving action/reward parity with `rl-v2-synthetic-implementation-v1`;
- observability hooks or adapters that preserve the merged synthetic counter vocabulary;
- documentation.

The runtime adapter must reuse the canonical pure functions from `ai_platform.scripts.rl_v2_synthetic_reference` rather than redefining action or reward semantics independently.

## Frozen integration choices

For variable isolation from `rl-research-v1`, later implementation under this task must keep:

- backend family: Stable-Baselines3 through the existing FreqAI `ReinforcementLearner` integration;
- algorithm family: PPO;
- policy family: MLP policy unless the existing FreqAI base requires another already-frozen default;
- long-only spot semantics;
- desired-position action space: `0=target_flat`, `1=target_long`;
- no short actions;
- no feature-set search or reward-parameter search.

This task does not authorize a training config, experiment manifest, run request, or evaluation timerange.

## Non-negotiable boundaries

- No training or model fitting.
- No backtest or historical execution.
- No market-data download.
- No Hyperopt, reward sweep, feature search, or hyperparameter search.
- No strict-OOS execution or performance extraction.
- Do not reuse consumed historical OOS `20260501-20260630` for validation or tuning.
- Do not access protected final holdout `20260801-20260930`.
- Do not declare a future evaluation window.
- Do not modify `rl-research-v1` code or evidence.
- Do not change frozen thresholds `0.006/-0.009`.
- Do not change completed Phase 6 or authoritative `selected_model = null`.
- No PyTorch-vs-RL ranking, promotion, profitability, or superiority claim.
- Any real execution must be declared by a later separate bounded task after this integration is frozen.

## Required implementation proofs

1. **Model/environment binding**
   - action space is exactly two desired-position actions;
   - environment transition and reward behavior call the merged synthetic reference semantics;
   - both desired-position actions remain valid policy outputs in either current position state;
   - unsupported action codes fail closed or receive the frozen invalid-action penalty as appropriate.
2. **Strategy binding**
   - `do_predict == 1` and `target_long` produce entry intent;
   - `do_predict == 1` and `target_flat` produce exit intent;
   - no hidden current-position state is required to interpret the policy-facing action;
   - no short-entry or short-exit semantics are introduced.
3. **Observability binding**
   - runtime-facing helpers preserve desired-position action labels and zero-count buckets;
   - `do_predict`, pre-trade signal, raw-trade and strict-OOS layers remain separately attributable;
   - this task does not fabricate runtime counts because no execution is authorized.
4. **Heavy-runtime safety**
   - import/static or minimal synthetic construction checks may be used only if they do not train, download data, or run a backtest;
   - if `freqai_rl` dependencies are unavailable in lightweight CI, tests must validate source/contract binding without weakening the runtime contract.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-22T23:45:00+02:00
head: 8ad99ab56b59fc0532d963905ee4619dc963269a
branch: feat/rl-v2-runtime-integration
pr: 151
status: review
context_routes:
  - docs/agents/tasks/FTAI-20260722-rl-v2-synthetic-implementation.md
  - docs/ai_platform/RL_V2_SYNTHETIC_IMPLEMENTATION.md
  - ai_platform/scripts/rl_v2_synthetic_reference.py
owned_paths:
  - docs/agents/tasks/FTAI-20260722-rl-v2-runtime-integration.md
  - docs/ai_platform/RL_V2_RUNTIME_INTEGRATION.md
  - ai_platform/experimental_model_research/rl-v2-runtime-integration-v1.json
  - ai_platform/freqaimodels/DesiredPositionReinforcementLearner.py
  - ai_platform/strategies/AiDesiredPositionRLResearchStrategy.py
  - tests/ai_platform/test_rl_v2_runtime_integration.py
proven:
  - RL-v2 design contract PR #102 and synthetic implementation PR #107 are merged and frozen as the canonical parent semantics.
  - Canonical synthetic implementation uses position_independent_action_semantics with stable desired-position actions target_flat/target_long and prospectively frozen reward constants.
  - Runtime-integration task declaration PR #142 was squash-merged as 5ad498e6a2538690ff371fd7b061bdd363820bf5.
  - Live develop advanced from the prior checkpoint to 02e580d3a0ef8892ab57539ac833e5a4066d082a only through unrelated checkpoint/lookahead work before this implementation branch was created.
  - No open PR found during the live preflight overlapped the declared RL-v2 model/strategy owned paths.
  - Branch feat/rl-v2-runtime-integration was created from develop 02e580d3a0ef8892ab57539ac833e5a4066d082a and PR #151 targets develop.
  - DesiredPositionEnvironment exposes exactly two policy-facing desired-position actions and delegates transition and reward behavior to ai_platform.scripts.rl_v2_synthetic_reference.
  - AiDesiredPositionRLResearchStrategy maps do_predict-gated target_long to entry intent and target_flat to exit intent without introducing short semantics.
  - Runtime observability binding reuses RLV2ObservabilityAccumulator for action, do_predict and pre-trade signal layers and does not fabricate raw-trade or strict-OOS counts.
  - Runtime descriptor freezes Stable-Baselines3/FreqAI, PPO and MlpPolicy integration metadata while authorizing no config, manifest, run request, training, backtest or historical evaluation.
  - AI Platform CI run 29959805166 compiled the new Python and passed the AI Platform test suite before its Ruff step failed; the formatting-only lint remediation is commit 8ad99ab56b59fc0532d963905ee4619dc963269a.
  - Consumed historical OOS 20260501-20260630 and protected final holdout 20260801-20260930 remain forbidden.
  - Frozen thresholds 0.006/-0.009 and authoritative Phase 6 selected_model null remain unchanged.
derived:
  - Static/AST tests prove runtime source binding to the canonical synthetic reference without importing the heavy freqai_rl dependency profile.
  - Any concrete runtime import/construction or execution remains a separately declared later task after this integration is frozen.
unknown:
  - Whether the heavy freqai_rl dependency profile can complete import/runtime smoke for the new adapter; the first smoke run was cancelled by the lint-fix synchronize event before the smoke step and the latest PR #151 CI is the current evidence source.
  - Whether a later separately declared execution-preflight task will need a dedicated config/manifest; those artifacts remain intentionally out of scope here.
conflicts: []
first_failure:
  marker: ai_platform_ci_ruff
  evidence: AI Platform CI run 29959805166 passed compile and tests, then failed at Ruff; changed Python source was reviewed for the repository 100-character line-length rule and commit 8ad99ab56b59fc0532d963905ee4619dc963269a wrapped the overlong static-test path assignment before CI re-ran.
rejected_hypotheses:
  - Train or backtest while implementing the runtime adapter.
  - Add a run request, historical timerange, or evaluation window to the integration task.
  - Retune frozen synthetic reward constants using consumed OOS evidence.
  - Modify the completed Phase 6 comparison or frozen Phase 5 thresholds.
  - Import the heavy RL runtime from lightweight static tests when source/AST binding is sufficient.
changed_paths:
  - docs/agents/tasks/FTAI-20260722-rl-v2-runtime-integration.md
  - docs/ai_platform/RL_V2_RUNTIME_INTEGRATION.md
  - ai_platform/experimental_model_research/rl-v2-runtime-integration-v1.json
  - ai_platform/freqaimodels/DesiredPositionReinforcementLearner.py
  - ai_platform/strategies/AiDesiredPositionRLResearchStrategy.py
  - tests/ai_platform/test_rl_v2_runtime_integration.py
validation:
  - command: live develop/open-PR/overlap preflight
    result: PASS
    evidence: develop was 02e580d3a0ef8892ab57539ac833e5a4066d082a before branch creation and no open PR overlapped the declared RL-v2 model/strategy owned paths.
  - command: required reads plus concrete BaseEnvironment/ReinforcementLearner API compatibility read
    result: PASS
    evidence: all required reads were inspected; optional core files were opened only to resolve the concrete runtime adapter API binding.
  - command: local targeted pytest/compile/Ruff
    result: NOT_RUN
    evidence: /tmp/handoff_repo is not mounted in the current sandbox; no training, backtest or historical execution was substituted for missing local validation.
  - command: AI Platform CI 29959805166 before lint remediation
    result: FAIL
    evidence: compile and AI Platform tests passed; Ruff was the first failing step. Ruff format and later validation steps were skipped after that failure.
  - command: PR #151 repository CI after lint remediation 8ad99ab56b59fc0532d963905ee4619dc963269a
    result: PENDING
    evidence: replacement AI Platform CI, Freqtrade CI, zizmor and Experimental Model Runtime Smoke runs were created; Pre-commit Types is skipped, not failed.
blockers: []
next_action: Inspect the latest PR #151 CI and review results; fix the first concrete failure if any, otherwise squash-merge the PR and close the task checkpoint without performing model execution.
```
