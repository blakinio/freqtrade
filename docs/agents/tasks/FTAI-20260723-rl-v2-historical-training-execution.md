---
task_id: FTAI-20260723-rl-v2-historical-training-execution
status: active
branch: docs/rl-v2-historical-training-execution-task
base_branch: develop
created: 2026-07-23
updated: 2026-07-23
related_pr: null
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
updated_at: 2026-07-23T14:05:00+02:00
head: a42858a6b6b2accdf47f78fa71cee557b3352448
branch: docs/rl-v2-historical-training-execution-task
pr: null
status: active
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
  - PR #184 merged the frozen non-executing RL-v2 training configuration as da1d5b8abe86ec2ac57dc2293d913fdcf1c286ae and PR #186 closed its task as a42858a6b6b2accdf47f78fa71cee557b3352448.
  - The committed RL-v2 config is dry-run, stopped by default, contains no credentials and has no execution geometry.
  - The consumed historical OOS 20260501-20260630 is not reusable as unseen evidence and remains forbidden for this track.
  - The protected final holdout 20260801-20260930 remains unused and forbidden.
  - Baseline source-of-truth declares training 20251201-20260228 and tuning 20260301-20260430; this task may use March-April only as explicitly labeled historical development evidence, not strict OOS.
  - No open RL-v2 training-execution PR or overlapping branch was found before this declaration.
  - Frozen thresholds 0.006/-0.009 and Phase 6 selected_model null remain unchanged.
derived:
  - Ending all execution/data geometry at the exclusive 2026-05-01 boundary prevents access to the consumed May-June OOS while allowing a bounded historical RL-v2 execution using already available pre-OOS history.
  - A separate one-file trigger after infrastructure merge preserves the same one-shot separation used by prior guarded experimental execution workflows.
unknown:
  - Whether the existing historical backtest runner can be reused directly for RL-v2 or requires a small RL-v2-specific adapter without weakening one-shot guards.
conflicts: []
first_failure:
  marker: none
  evidence: No implementation failure has occurred; this declaration executes no model and accesses no market data.
rejected_hypotheses:
  - Reuse consumed OOS 20260501-20260630 as RL-v2 evaluation evidence.
  - Access protected final holdout 20260801-20260930.
  - Call March-April evidence strict OOS or final validation.
  - Add the canonical run request in the same PR as execution infrastructure.
  - Retune PPO, policy, reward, features or thresholds from this execution package.
  - Rank RL-v2 against PyTorch or completed Phase 6 candidates.
changed_paths:
  - docs/agents/tasks/FTAI-20260723-rl-v2-historical-training-execution.md
validation:
  - command: repository live-state and overlap preflight
    result: PASS
    evidence: Current develop and open PR/branch state were checked before declaration; no active RL-v2 training-execution work overlapped this task.
blockers: []
next_action: Implement the declared RL-v2 historical training-execution infrastructure contract, canonical request validator, guarded request-triggered workflow, fail-closed tests and documentation without adding the canonical run-request file or executing training, backtesting, market-data download, strict-OOS scoring or protected-final-holdout access.
```
