---
task_id: FTAI-20260722-rl-v2-design-contract
status: implementing
branch: feat/rl-v2-design-contract-v1
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
  - merged task declaration PR #101 and current develop before implementation merge
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
updated_at: 2026-07-22T00:55:00+02:00
head: 6156e23efccd4cc41a3424b2a73e05ad9483da80
branch: feat/rl-v2-design-contract-v1
pr: pending
status: ready
context_routes:
  - docs/ai_platform/RL_V2_DESIGN_CONTRACT.md
  - ai_platform/experimental_model_research/rl-v2-design-contract-v1.json
  - ai_platform/scripts/rl_v2_design_contract.py
owned_paths:
  - docs/agents/tasks/FTAI-20260722-rl-v2-design-contract.md
  - docs/ai_platform/RL_V2_DESIGN_CONTRACT.md
  - ai_platform/experimental_model_research/rl-v2-design-contract-v1.json
  - ai_platform/scripts/rl_v2_design_contract.py
  - tests/ai_platform/test_rl_v2_design_contract.py
proven:
  - RL zero-trade diagnosis PR #100 was squash-merged as e0f6d3e557a880c49d6146530f806a0826f2d8e6 and closed the diagnosis task.
  - Task declaration PR #101 was squash-merged as e040eb1fcf0761409694856cb36794944d0ca34f before implementation began.
  - The v1 reward admits permanent neutrality as an unpenalized zero-reward solution while valid Long_enter has no immediate reward advantage.
  - The design contract keeps rl-research-v1 immutable and authorizes no RL-v2 model, strategy, config, training, backtest, data download or performance evaluation.
  - Reward invariants require flat-neutral reward to be strictly below valid long-entry reward, invalid-action penalty, no future-derived reward inputs and synthetic edge-case coverage.
  - Future implementation must choose exactly one position-state design mode and prove training/historical-inference parity synthetically before any historical execution.
  - Mandatory evidence requires action histograms, do_predict counts, pre-trade signal counts, raw backtest counts and strict-OOS counts as separately attributable layers.
  - Consumed historical OOS 20260501-20260630 and protected final holdout 20260801-20260930 are forbidden; this task selects no future evaluation window.
  - Frozen thresholds 0.006/-0.009 and completed Phase 6 selected_model null remain unchanged and RL-v2 cannot be consumed by Phase 6.
derived:
  - The contract removes post-hoc ambiguity by making reward geometry, position-state parity and action-level observability merge-time requirements for any later RL-v2 implementation task.
  - Numeric reward magnitudes and the concrete position-state/action-semantics architecture remain intentionally deferred and cannot be tuned in this design-contract task.
unknown:
  - Which concrete RL-v2 design mode and reward magnitudes a later implementation task will choose.
  - Whether repository CI will expose formatting or validator issues in the new static implementation.
conflicts: []
first_failure:
  marker: none
  evidence: No runtime execution was attempted; implementation is limited to a static canonical contract and mutation tests.
rejected_hypotheses:
  - Modify or rerun rl-research-v1 to validate the design contract.
  - Select numeric reward magnitudes or a future evaluation window in this task.
  - Tune any design against consumed historical OOS or protected final holdout data.
  - Add RL-v2 to completed Phase 6 or compare it retrospectively with PyTorch.
changed_paths:
  - docs/agents/tasks/FTAI-20260722-rl-v2-design-contract.md
  - docs/ai_platform/RL_V2_DESIGN_CONTRACT.md
  - ai_platform/experimental_model_research/rl-v2-design-contract-v1.json
  - ai_platform/scripts/rl_v2_design_contract.py
  - tests/ai_platform/test_rl_v2_design_contract.py
validation:
  - command: task declaration PR #101
    result: PASS
    evidence: Freqtrade CI 29874237734 and zizmor 29874237741 completed successfully before squash merge e040eb1fcf0761409694856cb36794944d0ca34f.
  - command: static contract construction review
    result: PASS
    evidence: Contract and canonical validator encode exact design-only authorization, reward, parity, observability, evaluation-isolation, Phase 6 and frozen-threshold boundaries.
  - command: targeted validator mutation tests and repository CI
    result: PENDING
    evidence: Implementation PR has not yet been opened.
blockers: []
next_action: Open the RL-v2 design-contract implementation PR, require AI Platform CI, Freqtrade CI and zizmor to pass, fix only concrete static validation failures, then squash-merge and close the durable checkpoint without starting any RL-v2 model execution.
```
