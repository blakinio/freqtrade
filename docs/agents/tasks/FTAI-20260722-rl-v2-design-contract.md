---
task_id: FTAI-20260722-rl-v2-design-contract
status: active
branch: feat/rl-v2-reward-observability-contract
base_branch: develop
created: 2026-07-22
updated: 2026-07-22
related_pr: "103"
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
  - docs/ai_platform/RL_V2_DESIGN_CONTRACT.md
  - ai_platform/experimental_model_research/rl-v2-design-contract-v1.json
search_first:
  - PR #103 live state and current develop before merge
  - open PRs or active tasks overlapping RL-v2 ownership
---

# RL-v2 Design Contract

## Goal

Define a machine-readable, fail-closed design contract for a future RL-v2 research track before any RL-v2 model, strategy, training, backtest, or evaluation implementation begins. The contract must address the root causes and observability gaps established by the completed RL zero-trade functional diagnosis without modifying the frozen `rl-research-v1` track.

## Non-negotiable boundaries

- Contract and static/synthetic validation only: no training, backtest, OOS execution, Hyperopt, market-data download, model fitting, or performance evaluation.
- Do not modify `rl-research-v1` model, strategy, config, manifest, historical evidence, or completed execution records.
- Do not reuse consumed strict historical OOS `20260501-20260630` for tuning, redesign validation, or fresh evidence.
- Do not access protected final holdout `20260801-20260930`.
- Do not change frozen thresholds `0.006/-0.009` or completed Phase 6 `selected_model = null`.
- Do not choose a future evaluation window in this task.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-22T00:55:00+02:00
head: 4319adfecf899d504964381ec690a8d48fb053a4
branch: feat/rl-v2-reward-observability-contract
pr: 103
status: ready
context_routes:
  - docs/ai_platform/RL_ZERO_TRADE_FUNCTIONAL_DIAGNOSIS.md
  - docs/ai_platform/RL_V2_DESIGN_CONTRACT.md
  - ai_platform/experimental_model_research/rl-v2-design-contract-v1.json
owned_paths:
  - docs/agents/tasks/FTAI-20260722-rl-v2-design-contract.md
  - docs/ai_platform/RL_V2_DESIGN_CONTRACT.md
  - ai_platform/experimental_model_research/rl-v2-design-contract-v1.json
  - ai_platform/scripts/rl_v2_design_contract.py
  - tests/ai_platform/test_rl_v2_design_contract.py
proven:
  - RL zero-trade diagnosis PR #100 was merged as e0f6d3e557a880c49d6146530f806a0826f2d8e6.
  - Task declaration PR #101 was merged as e040eb1fcf0761409694856cb36794944d0ca34f before implementation work.
  - RL-v1 zero trades are classified primarily as reward-induced neutral-policy collapse rather than runtime, action mapping, extraction, or broad prediction-gating failure.
  - The v1 artifact lacked deterministic action, do_predict, and pre-trade signal histograms.
  - The v2 contract is design_only and authorizes no model/strategy implementation, training, backtest, market-data download, OOS execution, promotion, or live trading.
  - Desired-position policy semantics are declared as target_flat/target_long so policy output does not require hidden current-position state.
  - Reward invariants require valid entry to be strictly preferred to neutral while flat and prohibit unpenalized perpetual neutrality.
  - PPO, MlpPolicy, seed 42, feature search, algorithm changes, reward sweeps, and hyperparameter sweeps remain isolated from this redesign slice.
  - Consumed historical OOS 20260501-20260630 and protected final holdout 20260801-20260930 are forbidden; no future evaluation window is declared.
  - Future evidence must preserve action, do_predict, pre-trade signal, raw-trade, strict-OOS extraction, deterministic evaluation, and identity/hash evidence.
  - Static validator fails closed if authorization, isolation, reward, parity, observability, or evaluation boundaries are weakened.
derived:
  - The next implementation task can build reward/action/observability code and unit/synthetic tests without historical model execution.
  - Fresh evaluation data may be declared only after the later implementation is frozen and deterministic gates pass.
unknown: []
conflicts: []
first_failure:
  marker: none
  evidence: Contract implementation is complete and awaiting repository validation.
rejected_hypotheses:
  - Modify or rerun rl-research-v1 to validate RL-v2 design.
  - Tune reward magnitudes or model parameters against consumed historical OOS.
  - Use protected final holdout data for RL-v2 design validation.
  - Authorize execution or create an RL-v2 model/strategy/config in this contract task.
changed_paths:
  - docs/agents/tasks/FTAI-20260722-rl-v2-design-contract.md
  - docs/ai_platform/RL_V2_DESIGN_CONTRACT.md
  - ai_platform/experimental_model_research/rl-v2-design-contract-v1.json
  - ai_platform/scripts/rl_v2_design_contract.py
  - tests/ai_platform/test_rl_v2_design_contract.py
validation:
  - command: repository and overlap preflight
    result: PASS
    evidence: PR #101 established the canonical task; implementation branch was reset to merged task HEAD before changes.
  - command: PR #103 repository gates
    result: PENDING
    evidence: Contract implementation PR is open; exact final CI identifiers will be recorded before merge.
blockers: []
next_action: Run PR #103 repository gates, fix only contract/validator/test/documentation defects, then mark this task done and squash-merge if all required gates pass.
```
