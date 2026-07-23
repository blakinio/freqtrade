---
task_id: FTAI-20260722-rl-v2-runtime-integration
status: done
branch: develop
base_branch: develop
created: 2026-07-22
updated: 2026-07-23
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
updated_at: 2026-07-23T00:52:00+02:00
head: 251fa56aeaaa8fb95c7cdf73015da0c1142dc978
branch: develop
pr: 151
status: done
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
  - RL-v2 design contract PR #102 and synthetic implementation PR #107 remain the frozen canonical parent semantics.
  - PR #151 implemented a two-action desired-position environment and strategy adapter that reuse the canonical synthetic transition, reward and observability primitives without adding short semantics.
  - PR #151 added only the bounded runtime adapter surface, descriptor, observability binding, static/synthetic tests and documentation; no training config, experiment manifest, run request or evaluation window was added.
  - Final PR #151 head 01b1e51cff09f0f0c91e41aca5cd975af403af8a passed AI Platform CI 29962856917, Experimental Model Runtime Smoke 29962856904, zizmor 29962857057 and Freqtrade CI 29962856870; Pre-commit Types 29962856867 was skipped, not failed.
  - The heavy freqai_rl dependency profile successfully installed and the bounded canonical experimental-model runtime smoke passed, resolving the prior runtime-import uncertainty for this adapter surface.
  - PR #151 was squash-merged to develop as 251fa56aeaaa8fb95c7cdf73015da0c1142dc978.
  - Consumed historical OOS 20260501-20260630 and protected final holdout 20260801-20260930 were not accessed and remain forbidden.
  - Frozen thresholds 0.006/-0.009 and authoritative Phase 6 selected_model null remain unchanged.
derived:
  - The runtime integration is frozen and ready only for a separately declared execution-preflight work package.
  - Any future training configuration, run request, historical execution or evaluation-window declaration must remain outside this completed task.
unknown:
  - Whether a later separately declared execution-preflight task will need a dedicated config/manifest; those artifacts remain intentionally out of scope here.
conflicts: []
first_failure:
  marker: resolved_ai_platform_ci_formatting
  evidence: Early PR #151 CI first failed at Ruff/Ruff format after compile and tests passed; exact Ruff 0.15.21 formatting was applied, the temporary diagnostic workflow was removed, and final AI Platform CI 29962856917 passed lint and format checks.
rejected_hypotheses:
  - Train or backtest while implementing the runtime adapter.
  - Add a run request, historical timerange, or evaluation window to the integration task.
  - Retune frozen synthetic reward constants using consumed OOS evidence.
  - Modify the completed Phase 6 comparison or frozen Phase 5 thresholds.
  - Treat a temporary formatting diagnostic workflow as part of the deliverable.
changed_paths:
  - docs/agents/tasks/FTAI-20260722-rl-v2-runtime-integration.md
  - docs/ai_platform/RL_V2_RUNTIME_INTEGRATION.md
  - ai_platform/experimental_model_research/rl-v2-runtime-integration-v1.json
  - ai_platform/freqaimodels/DesiredPositionReinforcementLearner.py
  - ai_platform/strategies/AiDesiredPositionRLResearchStrategy.py
  - tests/ai_platform/test_rl_v2_runtime_integration.py
validation:
  - command: PR #151 final AI Platform CI
    result: PASS
    evidence: Run 29962856917 passed compile, AI Platform tests, Ruff lint, Ruff format, Codespell and JSON validation.
  - command: PR #151 Experimental Model Runtime Smoke
    result: PASS
    evidence: Run 29962856904 installed FreqAI/freqai_rl runtime dependencies and passed the bounded canonical experimental-model runtime smoke without training or historical execution.
  - command: PR #151 zizmor
    result: PASS
    evidence: Run 29962857057 completed successfully after the temporary diagnostic workflow had been removed from the final PR diff.
  - command: PR #151 Freqtrade CI
    result: PASS
    evidence: Run 29962856870 completed successfully, including pre-commit checks, documentation build and the applicable core test matrix.
  - command: local targeted pytest/compile/Ruff
    result: NOT_RUN
    evidence: The repository checkout from the handoff path was not mounted in this sandbox; repository CI provided executable validation instead.
blockers: []
next_action: Declare a separate bounded RL-v2 execution-preflight task before adding any training config, run request, historical evaluation window, or model execution.
```
