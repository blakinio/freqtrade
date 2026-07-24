---
task_id: FTAI-20260724-rl-v2-historical-evidence-diagnosis
status: done
branch: docs/rl-v2-historical-evidence-diagnosis
base_branch: develop
created: 2026-07-24
updated: 2026-07-24
related_pr: "237"
owned_paths:
  - docs/agents/tasks/FTAI-20260724-rl-v2-historical-evidence-diagnosis.md
  - docs/ai_platform/RL_V2_HISTORICAL_EVIDENCE_DIAGNOSIS.md
  - ai_platform/experimental_model_research/rl-v2-historical-evidence-diagnosis-v1.json
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260723-rl-v2-historical-training-execution.md
  - docs/ai_platform/RL_V2_HISTORICAL_TRAINING_EXECUTION.md
  - ai_platform/experimental_model_research/rl-v2-historical-training-execution-contract-v1.json
  - ai_platform/strategies/AiDesiredPositionRLResearchStrategy.py
  - ai_platform/strategies/AiLongOnlyRLResearchStrategy.py
  - ai_platform/freqaimodels/DesiredPositionReinforcementLearner.py
search_first:
  - current develop and open PRs overlapping RL-v2 evidence, strategy lifecycle, reward or evaluation work
---

# RL-v2 Historical Evidence Diagnosis

## Goal

Diagnose the immutable historical-development evidence from workflow run `30022863894` without
executing a model, accessing market data, retuning any frozen input, or converting the result into
selection or promotion evidence.

The task must identify one highest-confidence mechanism that can become a separately declared,
single-variable future hypothesis.

## Source boundary

The only result source is immutable artifact
`rl-v2-historical-training-execution-218` with digest
`sha256:5d74d87bf4408c7b51779cd9038d815c88d3f5cc193cd229b6757edf32112b55`.

The artifact remains:

- `historical_development_evidence`;
- `strict_oos=false`;
- `protected_final_validation=false`;
- `consumed_historical_oos_accessed=false`;
- `protected_final_holdout_accessed=false`.

## Allowed scope

- Inspect provenance, config, logs and raw backtest trades from the immutable artifact.
- Recalculate deterministic gross-price PnL, fees and net PnL from recorded trades.
- Decompose results by pair, month, exit reason, duration and re-entry interval.
- Inspect committed model and strategy adapters to explain observed trade lifecycle.
- Record one diagnostic hypothesis for a future separately bounded task.

## Non-negotiable boundaries

- No new training, backtest or market-data access.
- No PPO, reward, feature, threshold, ROI or stop-loss mutation.
- No use of consumed OOS `20260501-20260630`.
- No access to protected final holdout `20260801-20260930`.
- No strict-OOS, final-validation, ranking, promotion, profitability or superiority claim.
- Frozen thresholds `0.006/-0.009` remain unchanged.
- Phase 6 authoritative `selected_model=null` remains unchanged.
- The diagnosis cannot itself authorize another experiment.

## Result

The analysis is recorded in:

- `docs/ai_platform/RL_V2_HISTORICAL_EVIDENCE_DIAGNOSIS.md`;
- `ai_platform/experimental_model_research/rl-v2-historical-evidence-diagnosis-v1.json`.

The selected primary mechanism is a lifecycle conflict between desired-position policy semantics and
the inherited deterministic ROI schedule. A separate future task may prospectively test one
lifecycle-only change, but it must not combine that change with PPO, reward, feature, threshold,
stop-loss or action-semantics tuning.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-24T10:10:00+02:00
head: 12ff9f8e766521493b23791f48effa9607d3389e
branch: docs/rl-v2-historical-evidence-diagnosis
pr: 237
status: done
context_routes:
  - docs/agents/tasks/FTAI-20260723-rl-v2-historical-training-execution.md
  - docs/ai_platform/RL_V2_HISTORICAL_TRAINING_EXECUTION.md
  - docs/ai_platform/RL_V2_HISTORICAL_EVIDENCE_DIAGNOSIS.md
owned_paths:
  - docs/agents/tasks/FTAI-20260724-rl-v2-historical-evidence-diagnosis.md
  - docs/ai_platform/RL_V2_HISTORICAL_EVIDENCE_DIAGNOSIS.md
  - ai_platform/experimental_model_research/rl-v2-historical-evidence-diagnosis-v1.json
proven:
  - The only analyzed result is immutable artifact rl-v2-historical-training-execution-218 from run 30022863894, digest sha256:5d74d87bf4408c7b51779cd9038d815c88d3f5cc193cd229b6757edf32112b55.
  - Artifact metadata classifies the result as historical_development_evidence with strict_oos=false, protected_final_validation=false, consumed_historical_oos_accessed=false and protected_final_holdout_accessed=false.
  - The 174 trades reconcile to gross price PnL +21.791297 USDT, fees 69.643465 USDT and net PnL -47.852168 USDT.
  - BTC/USDT contributed -28.115502 USDT net and ETH/USDT contributed -19.736665 USDT net, so the loss mechanism is not isolated to one pair.
  - There were 122 ROI exits; all had positive gross price PnL, 34 became net losses after fees, and all 122 were followed by same-pair re-entry exactly 15 minutes later.
  - Nine of 11 stop-loss exits were followed by same-pair re-entry exactly 15 minutes later.
  - ROI plus stop-loss created 131 immediate 15-minute external-exit/re-entry boundaries with 52.582123 USDT of close-plus-reopen fees.
  - The desired-position strategy correctly maps action 0 to target_flat and action 1 to target_long.
  - The strategy inherits minimal_roi values 0:0.03, 240:0.015 and 720:0.0, allowing external ROI closure after 720 minutes while the next policy decision can still request target_long.
  - Target-flat exits are a separate loss-concentrated observation: 39 trades, -58.907848 USDT gross, -74.390001 USDT net and 38 net losses.
  - No new training, backtest, market-data access, retuning, ranking, promotion or holdout access occurred in this diagnosis.
  - Frozen thresholds remain 0.006/-0.009 and Phase 6 selected_model remains null.
derived:
  - The highest-confidence observed mechanism is transaction-cost churn at the boundary between desired-position policy state and inherited external ROI exits.
  - The artifact does not prove PPO lacks directional information because aggregate gross price PnL was positive and 124 trades were gross-positive.
  - Lifecycle alignment and target-flat policy quality must be tested separately to preserve causal attribution.
unknown:
  - The artifact lacks a full action-time-series export and multiple seeds, so PPO stability and action persistence cannot be concluded from this task.
conflicts: []
first_failure:
  marker: historical_development_net_loss_after_lifecycle_churn
  evidence: The completed March-April historical-development result was -47.852168 USDT net while immediate ROI/stop-loss exit and re-entry boundaries carried 52.582123 USDT of fees.
rejected_hypotheses:
  - Treat the diagnosis as proof that disabling ROI would make RL-v2 profitable.
  - Tune lifecycle, PPO, reward, features, thresholds and target-flat behavior in one experiment.
  - Re-run completed trigger PR #218.
  - Use consumed OOS 20260501-20260630 for tuning or scoring.
  - Access protected final holdout 20260801-20260930.
  - Treat March-April evidence as strict OOS or final validation.
  - Rank RL-v2 against PyTorch or completed Phase 6 candidates.
  - Infer promotion eligibility or profitability from this analysis.
changed_paths:
  - docs/agents/tasks/FTAI-20260724-rl-v2-historical-evidence-diagnosis.md
  - docs/ai_platform/RL_V2_HISTORICAL_EVIDENCE_DIAGNOSIS.md
  - ai_platform/experimental_model_research/rl-v2-historical-evidence-diagnosis-v1.json
validation:
  - command: immutable artifact identity and provenance inspection
    result: PASS
    evidence: Artifact name, run, trigger head, digest, evidence classification and OOS/holdout access flags match the completed execution checkpoint.
  - command: deterministic trade-accounting reconciliation
    result: PASS
    evidence: For every trade, amount times close-minus-open price less recorded open and close fees reconciles to profit_abs within floating-point tolerance; totals reproduce -47.852168 USDT.
  - command: committed lifecycle adapter inspection
    result: PASS
    evidence: Desired-position action mapping is correct and inherited minimal_roi explains an external exit surface independent of target-flat policy exits.
blockers: []
next_action: Declare a separate prospective single-variable RL-v2 lifecycle-alignment task before changing or executing anything; preserve hard stop-loss and all frozen PPO, reward, feature, fee, pair, threshold and action-semantics inputs, and do not access consumed OOS or the protected final holdout.
```
