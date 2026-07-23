---
task_id: FTAI-20260723-rl-v2-historical-training-execution
status: done
branch: develop
base_branch: develop
created: 2026-07-23
updated: 2026-07-23
related_pr: "218"
owned_paths:
  - docs/agents/tasks/FTAI-20260723-rl-v2-historical-training-execution.md
  - docs/ai_platform/RL_V2_HISTORICAL_TRAINING_EXECUTION.md
  - ai_platform/experimental_model_research/rl-v2-historical-training-execution-contract-v1.json
  - ai_platform/scripts/rl_v2_historical_training_execution_run_request.py
  - tests/ai_platform/test_rl_v2_historical_training_execution.py
  - .github/workflows/ai-platform-rl-v2-historical-training-execution.yml
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260723-rl-v2-training-configuration.md
  - docs/ai_platform/RL_V2_TRAINING_CONFIGURATION.md
  - ai_platform/experimental_model_research/rl-v2-training-configuration-v1.json
  - ai_platform/configs/rl_v2_training_research.json
  - docs/ai_platform/RL_V2_EXECUTION_PREFLIGHT.md
  - ai_platform/experimental_model_research/rl-v2-execution-preflight-v1.json
  - docs/ai_platform/EXPERIMENTAL_MODEL_HISTORICAL_BACKTEST_EXECUTION.md
  - ai_platform/experimental_model_research/historical-backtest-execution-contract-v1.json
  - ai_platform/validation/final-holdout-v2-declaration.json
search_first:
  - current develop and open PRs before RL-v2 historical training-execution work
  - active tasks or PRs overlapping RL-v2 execution, model, strategy, config or experimental-research ownership
optional_reads:
  - ai_platform/scripts/experimental_model_historical_backtest_runner.py
  - ai_platform/scripts/experimental_model_historical_backtest_run_request.py
  - .github/workflows/experimental-model-historical-backtest-execution.yml
---

# RL-v2 Historical Training Execution

## Goal

Build a separately bounded, one-shot historical training/execution path for the frozen RL-v2 desired-position runtime and committed research-only training configuration. The implementation must prospectively freeze execution geometry and evidence semantics before any result-producing run request can exist.

This task may build guarded execution infrastructure, but the infrastructure implementation PR itself must not train a model, run a backtest, download market data, or add the canonical one-shot run-request file.

## Frozen parent state

The task is bound to:

- training configuration: `rl-v2-training-configuration-v1`;
- training-configuration merge: `da1d5b8abe86ec2ac57dc2293d913fdcf1c286ae`;
- runtime integration: `rl-v2-runtime-integration-v1`;
- execution preflight: `rl-v2-execution-preflight-v1`;
- model: `DesiredPositionReinforcementLearner`;
- strategy: `AiDesiredPositionRLResearchStrategy`;
- backend: Stable-Baselines3 through FreqAI;
- algorithm/policy: PPO / `MlpPolicy`;
- long-only desired-position actions: `0=target_flat`, `1=target_long`;
- canonical transition, reward, action-label and observability semantics from `ai_platform.scripts.rl_v2_synthetic_reference`.

## Prospectively frozen historical geometry

This work package must use only pre-consumed-holdout history:

- download timerange: `20250801-20260501` with May 1 as the exclusive stop;
- trailing training geometry: `train_period_days = 90`;
- historical evidence execution timerange: `20260301-20260501` with May 1 as the exclusive stop;
- evidence window represented by that execution: March 1 through April 30, 2026;
- `backtest_period_days = 61`;
- pairs: `BTC/USDT`, `ETH/USDT`;
- timeframes: `15m`, `1h`, `4h`;
- exchange: Kraken spot;
- fee ratio: `0.002`.

The March-April window is historical development evidence only. It is not a fresh project-wide strict-OOS window and must not be labeled or interpreted as protected final validation.

## Allowed implementation scope

This task may add only:

- an immutable machine-readable execution contract containing the frozen geometry and safety boundaries;
- a canonical run-request generator/validator that derives one exact request from tracked repository inputs;
- a request-triggered workflow that remains inert until a later separate PR adds exactly one canonical run-request file;
- temporary runtime materialization of the committed RL-v2 config with only the frozen `train_period_days` and `backtest_period_days` execution geometry added;
- exact model/strategy/config/contract hash binding;
- fail-closed market-data coverage checks restricted to the declared historical range;
- exactly one RL-v2 FreqAI backtest/training execution when a later separately reviewed trigger request is opened;
- evidence extraction limited to raw historical backtest, action/prediction/signal/trade observability and provenance;
- tests and documentation.

## Non-negotiable boundaries

- No canonical run-request file in the infrastructure implementation PR.
- No training, fitting, `.learn()`, backtest or market-data download while implementing or validating infrastructure.
- No use or access of consumed historical OOS `20260501-20260630`.
- No access to protected final holdout `20260801-20260930`.
- No strict-OOS claim for March-April historical evidence.
- No Hyperopt, reward sweep, feature search or hyperparameter search.
- No mutation of the committed RL-v2 training configuration or frozen synthetic reward constants.
- No short semantics.
- No PyTorch-vs-RL ranking or cross-track selection.
- No Phase 6 mutation; authoritative `selected_model = null` remains unchanged.
- Frozen thresholds `0.006/-0.009` remain unchanged and are not RL-v2 tuning inputs.
- No promotion, profitability, superiority, dry-run deployment or live-capital claim.
- Any later canonical trigger must be a separate one-file PR and must not be merged as a reusable execution switch after the one-shot run.

## Required proofs

1. **Prospective geometry binding**
   - exact timeranges and 90/61-day FreqAI geometry are immutable and machine-readable;
   - all declared data stops before consumed OOS begins on 2026-05-01;
   - forbidden OOS/final-holdout windows fail closed.
2. **Frozen RL-v2 binding**
   - exact config/model/strategy/runtime identities and hashes are bound;
   - PPO, `MlpPolicy`, desired-position actions and canonical reward semantics cannot drift.
3. **Execution separation**
   - infrastructure merge cannot execute because the canonical run-request path is absent;
   - a later trigger PR must add exactly the generated request and no other file;
   - the workflow checks out the exact trigger head before data access or execution.
4. **Evidence honesty**
   - March-April output is labeled historical development evidence, not strict OOS;
   - zero trades, negative results or execution failure remain valid negative evidence;
   - no ranking, promotion or profitability conclusion is produced automatically.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-23T19:31:00+02:00
head: d5d8fc583f9d5da980a0fec8f24c46966f4e2c8b
branch: develop
pr: 218
status: done
context_routes:
  - docs/agents/tasks/FTAI-20260723-rl-v2-training-configuration.md
  - docs/ai_platform/RL_V2_TRAINING_CONFIGURATION.md
  - ai_platform/experimental_model_research/rl-v2-training-configuration-v1.json
owned_paths:
  - docs/agents/tasks/FTAI-20260723-rl-v2-historical-training-execution.md
  - docs/ai_platform/RL_V2_HISTORICAL_TRAINING_EXECUTION.md
  - ai_platform/experimental_model_research/rl-v2-historical-training-execution-contract-v1.json
  - ai_platform/scripts/rl_v2_historical_training_execution_run_request.py
  - tests/ai_platform/test_rl_v2_historical_training_execution.py
  - .github/workflows/ai-platform-rl-v2-historical-training-execution.yml
proven:
  - PR #188 merged the guarded RL-v2 historical execution infrastructure and later repair PRs #196 and #208 fixed workflow registration and repository-package visibility without changing frozen model, strategy, reward, features or execution geometry.
  - Trigger PR #218 changed exactly the canonical run-request file and was closed without merge after dedicated workflow run 30022863894 reached terminal success.
  - Run 30022863894 passed exact-one-file scope, bounded checkpoint and fresh canonical request validation before runtime or data access.
  - BTC/USDT and ETH/USDT data jobs downloaded or restored only the declared 20250801-20260501 Kraken spot history for 15m, 1h and 4h, then passed fail-closed pre-OOS coverage verification.
  - Combined data were re-verified before execution; evidence metadata records consumed_historical_oos_accessed=false and protected_final_holdout_accessed=false.
  - Exactly one frozen `freqtrade backtesting` command executed on trigger head 36f175477c848ae2ecfc92dbd335d7573af4933d with execution timerange 20260301-20260501 and semantic evidence window 20260301-20260430.
  - FreqAI trained the frozen PPO/MlpPolicy RL-v2 model once per pair for BTC/USDT and ETH/USDT using the declared 90-day trailing training geometry, then completed the 61-day historical backtest successfully.
  - Historical-development result: 174 trades, final balance 9952.148 USDT from 10000 USDT, absolute profit -47.852 USDT, total profit -0.48%, profit factor 0.65, with 89 wins and 85 losses.
  - Result classification is historical_development_evidence with strict_oos=false and protected_final_validation=false; it is negative development evidence only and creates no ranking, promotion, profitability or superiority claim.
  - Immutable execution artifact `rl-v2-historical-training-execution-218` was uploaded with digest sha256:5d74d87bf4408c7b51779cd9038d815c88d3f5cc193cd229b6757edf32112b55 and contains raw backtest, effective runtime config, coverage and provenance metadata.
  - Consumed historical OOS 20260501-20260630 and protected final holdout 20260801-20260930 remain unused; frozen thresholds remain 0.006/-0.009 and Phase 6 selected_model remains null.
derived:
  - The bounded RL-v2 historical training/execution objective is complete because the declared one-shot run reached terminal success and immutable historical-development evidence was captured.
  - The observed negative March-April result cannot be used as strict-OOS, protected-final-validation, cross-track selection or promotion evidence.
  - Any further RL-v2 execution, evaluation, tuning, comparison or holdout work requires a new prospectively bounded task rather than reusing this completed trigger path.
unknown: []
conflicts: []
first_failure:
  marker: resolved_freqtrade_dynamic_strategy_import_path
  evidence: The prior #202 runtime import failure was repaired by PR #208; run 30022863894 subsequently resolved both AiDesiredPositionRLResearchStrategy and DesiredPositionReinforcementLearner and completed training/backtesting successfully.
rejected_hypotheses:
  - Treat March-April 2026 evidence as strict OOS or protected final validation.
  - Reuse consumed OOS 20260501-20260630 for tuning, validation or scoring.
  - Access protected final holdout 20260801-20260930 before its separately governed one-shot evaluation.
  - Retune PPO, policy, reward, features or thresholds based on this run.
  - Rank RL-v2 against PyTorch or completed Phase 6 candidates from this task.
  - Infer profitability, superiority or promotion eligibility from the completed historical-development run.
changed_paths:
  - docs/agents/tasks/FTAI-20260723-rl-v2-historical-training-execution.md
validation:
  - command: dedicated workflow run 30022863894
    result: PASS
    evidence: Request validation, both pair data jobs, combined coverage re-verification, exactly one frozen historical training/backtest, provenance recording and immutable artifact upload all completed successfully.
  - command: execution artifact inspection
    result: PASS
    evidence: Metadata confirms historical_development_evidence, strict_oos=false, protected_final_validation=false, consumed_historical_oos_accessed=false and protected_final_holdout_accessed=false; raw result reports 174 trades and -0.48% total profit.
blockers: []
next_action: Do not run another historical execution from this completed task; any further RL-v2 evaluation, retuning, comparison, promotion or final-holdout work must start as a separate prospectively bounded task that preserves consumed-OOS and protected-final-holdout boundaries.
```
