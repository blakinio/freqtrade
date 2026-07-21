---
task_id: FTAI-20260722-rl-v2-design-contract
status: active
branch: docs/rl-v2-design-contract-task
base_branch: develop
created: 2026-07-22
updated: 2026-07-22
related_pr: "pending"
owned_paths:
  - docs/agents/tasks/FTAI-20260722-rl-v2-design-contract.md
  - docs/ai_platform/RL_V2_DESIGN_CONTRACT.md
  - ai_platform/experimental_model_research/rl-v2-design-contract-v1.json
  - ai_platform/scripts/rl_v2_design_contract.py
  - tests/ai_platform/test_rl_v2_design_contract.py
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/RL_ZERO_TRADE_FUNCTIONAL_DIAGNOSIS.md
  - ai_platform/freqaimodels/LongOnlyReinforcementLearner.py
  - ai_platform/strategies/AiLongOnlyRLResearchStrategy.py
  - freqtrade/freqai/RL/BaseReinforcementLearningModel.py
  - freqtrade/freqai/RL/BaseEnvironment.py
search_first:
  - merged PR #100 and current develop before RL-v2 contract work
  - open PRs or active tasks overlapping RL research ownership
optional_reads:
  - ai_platform/experimental_model_research/evidence/rl-research-v1-historical-oos-v1.json
  - ai_platform/configs/freqai-rl-research.example.json
---

# RL-v2 Design Contract

## Goal

Define a machine-readable, fail-closed design contract for a future RL-v2 research track before any RL-v2 model, strategy, training, backtest, or evaluation implementation begins. The contract must address the root causes and observability gaps established by the completed RL zero-trade functional diagnosis without modifying the frozen `rl-research-v1` track.

## Non-negotiable boundaries

- Contract and synthetic/static validation only: no training, backtest, OOS execution, Hyperopt, market-data download, model fitting, or performance evaluation.
- Do not modify `rl-research-v1` model, strategy, config, manifest, historical evidence, or completed execution records.
- Do not reuse consumed strict historical OOS `20260501-20260630` for tuning, redesign validation, or fresh evidence.
- Do not access protected final holdout `20260801-20260930`.
- Do not change frozen thresholds `0.006/-0.009`.
- Do not change completed Phase 6, its candidates, selection policy, or authoritative `selected_model = null` result.
- Do not rank RL against PyTorch, authorize promotion, or make profitability/superiority claims.
- Do not choose or consume a future evaluation window in this task; any fresh evaluation must be declared separately after implementation is frozen.

## Required contract properties

The RL-v2 design contract must fail closed unless all of the following are explicit:

1. **Reward geometry**
   - remaining flat while already neutral has a strictly lower immediate reward than a valid long-entry transition;
   - perpetual neutral inactivity is not an unpenalized zero-reward solution by construction;
   - invalid actions remain penalized;
   - reward inputs are decision-time/state inputs only and must not derive from future candles.
2. **Position-state and inference parity**
   - the design declares either an explicit position-state observation mechanism available consistently during training and historical inference, or action semantics proven not to require hidden position state;
   - a synthetic parity test is required before any later historical execution.
3. **Mandatory observability**
   - deterministic inference action counts by pair and action;
   - `do_predict` accepted/rejected counts;
   - strategy entry/exit signal counts before trade-capacity/order handling;
   - raw backtest trade counts and strict-OOS extraction counts remain separately attributable.
4. **Evaluation isolation**
   - consumed historical OOS and protected final holdout are explicitly forbidden;
   - a future evaluation window must be prospectively declared in a later bounded task;
   - no cross-track selection or Phase 6 consumption is permitted.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-22T00:45:00+02:00
head: e0f6d3e557a880c49d6146530f806a0826f2d8e6
branch: docs/rl-v2-design-contract-task
pr: pending
status: ready
context_routes:
  - docs/ai_platform/RL_ZERO_TRADE_FUNCTIONAL_DIAGNOSIS.md
  - ai_platform/freqaimodels/LongOnlyReinforcementLearner.py
  - freqtrade/freqai/RL/BaseReinforcementLearningModel.py
owned_paths:
  - docs/agents/tasks/FTAI-20260722-rl-v2-design-contract.md
  - docs/ai_platform/RL_V2_DESIGN_CONTRACT.md
  - ai_platform/experimental_model_research/rl-v2-design-contract-v1.json
  - ai_platform/scripts/rl_v2_design_contract.py
  - tests/ai_platform/test_rl_v2_design_contract.py
proven:
  - RL zero-trade diagnosis PR #100 was squash-merged as e0f6d3e557a880c49d6146530f806a0826f2d8e6 and closed the diagnosis task.
  - The diagnosis classified rl-research-v1 as a functionally successful execution with reward-induced neutral-policy collapse / inactive-policy attractor.
  - The v1 reward gives 0 to Neutral while neutral and 0 to valid Long_enter, while entering exposes the policy to later holding and exit downside.
  - The v1 action mapping itself is internally consistent and the source backtest had zero trades before strict-OOS extraction.
  - The v1 artifact did not preserve deterministic action-frequency, do_predict, or pre-trade signal histograms.
  - Position-dependent action validity exists in v1 while add_state_info is false with a memoryless MlpPolicy; this is a secondary design limitation.
  - Frozen thresholds remain 0.006/-0.009, Phase 6 remains selected_model null, and protected final holdout 20260801-20260930 remains unused.
derived:
  - The smallest safe follow-up is a design contract and synthetic/static validator before any RL-v2 implementation or fresh evaluation.
  - RL-v2 must make reward incentives, position-state/inference parity, and action-level observability prospective requirements rather than post-hoc diagnostics.
unknown:
  - Which concrete RL-v2 action semantics or position-state mechanism will later satisfy the contract; implementation is intentionally out of scope here.
conflicts: []
first_failure:
  marker: none
  evidence: Diagnosis is complete; this task prospectively defines constraints for future redesign rather than fixing v1 in place.
rejected_hypotheses:
  - Modify or rerun rl-research-v1 to validate a redesign.
  - Tune reward magnitudes or model parameters against consumed historical OOS.
  - Use protected final holdout data for RL-v2 design validation.
  - Add RL-v2 to completed Phase 6 or compare it retrospectively with PyTorch.
changed_paths:
  - docs/agents/tasks/FTAI-20260722-rl-v2-design-contract.md
validation:
  - command: live repository and overlap preflight
    result: PASS
    evidence: develop is e0f6d3e557a880c49d6146530f806a0826f2d8e6 after merged PR #100, and no open PR overlaps RL-v2 design-contract ownership.
blockers: []
next_action: Merge this bounded task declaration, then implement only the machine-readable RL-v2 design contract, fail-closed validator, synthetic/static tests and documentation on a dedicated implementation branch without creating an RL-v2 model/strategy/config or running any model execution.
```
