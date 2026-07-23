---
task_id: FTAI-20260723-rl-v2-historical-training-execution
status: active
branch: develop
base_branch: develop
created: 2026-07-23
updated: 2026-07-23
related_pr: "200"
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
updated_at: 2026-07-23T15:39:05+02:00
head: 3268d391312a549b84acd282f0f29fc4df391908
branch: develop
pr: 200
status: ready
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
  - PR #184 merged the frozen non-executing RL-v2 training configuration and PR #186 closed that configuration task; declaration PR #187 then created this bounded execution task before implementation.
  - PR #188 added the separate RL-v2 execution contract, canonical request validator/materializer, request-triggered workflow, tests and documentation without adding a run request or executing a model.
  - Frozen geometry is download 20250801-20260501, execution 20260301-20260501, train_period_days 90, backtest_period_days 61, BTC/USDT plus ETH/USDT, 15m plus 1h plus 4h, Kraken spot and fee 0.002.
  - PR #188 final head passed AI Platform CI, zizmor and every applicable Freqtrade CI platform job, then squash-merged as aa974bb16d8724d171c5ebc45e26a3a8cfc63841.
  - Trigger PRs #193 and #195 produced zero dedicated workflow runs and were closed without merge, so neither consumed the one-shot execution or accessed market data.
  - Diagnostic PR #194 plus actionlint isolated the zero-run cause to job-level env use of unavailable runner context for RUN_CONFIG.
  - Repair PR #196 moved runtime config path construction to step-level $RUNNER_TEMP, added a regression test, passed actionlint and repository CI, and squash-merged as a1910dcc934b0d185a1e3378b61fee90ada0bfba.
  - Checkpoint PR #198 recorded the repair state and squash-merged as 3268d391312a549b84acd282f0f29fc4df391908.
  - Diagnostic PR #199 regenerated and validated the post-repair canonical request; its repaired workflow_sha256 is 7311fe6cd53e5e9a0ecec6b923a13265a0308a4c1175170774b8765c060bd74b.
  - Trigger PR #200 changed exactly the canonical run-request file and successfully created dedicated workflow run 30011986442, proving the repaired workflow now starts.
  - Run 30011986442 passed exact-one-file scope validation and then failed closed at bounded checkpoint validation before Python setup; data preparation and backtest jobs were skipped.
  - No RL-v2 market-data download, model training, backtest, consumed historical OOS access or protected final holdout access has occurred yet; the one-shot execution remains unconsumed.
  - Protected final holdout 20260801-20260930 remains unused, frozen thresholds 0.006/-0.009 remain unchanged and Phase 6 selected_model remains null.
derived:
  - The post-repair canonical request from PR #199 remains canonical across a checkpoint-only repair because the request hashes contract, descriptor, config, model, strategy, validator and workflow, not the task checkpoint file.
  - A fresh trigger must branch from develop after the checkpoint compactness fix so the exact trigger head contains a governance-valid task checkpoint while still differing from develop by only the canonical request file.
  - March-April output remains historical development evidence only and cannot be treated as strict OOS, protected final validation or promotion evidence.
unknown:
  - Whether the first execution that passes checkpoint validation will accept the direct frozen FreqAI backtesting surface without an additional runtime adapter.
conflicts: []
first_failure:
  marker: checkpoint_compactness_gate
  evidence: Dedicated run 30011986442 started on trigger PR #200 and passed exact-one-file scope validation, then tools/agents/checkpoint.py rejected the task checkpoint before Python or data access because the PR #198 checkpoint recorded 18 proven facts while governance compactness permits at most 16.
rejected_hypotheses:
  - Treat PR #193, #195 or #200 as consumed one-shot executions despite no market-data or model execution.
  - Reuse consumed OOS 20260501-20260630 as RL-v2 evaluation evidence.
  - Access protected final holdout 20260801-20260930.
  - Call March-April evidence strict OOS or final validation.
  - Restore older historical caches that may contain May-June or later data.
  - Retune PPO, policy, reward, features or thresholds from this execution package.
  - Rank RL-v2 against PyTorch or completed Phase 6 candidates.
changed_paths:
  - docs/agents/tasks/FTAI-20260723-rl-v2-historical-training-execution.md
validation:
  - command: PR #196 actionlint and repository CI
    result: PASS
    evidence: Exact repair head 612beb0060171df2fb85b203763590d3a2d7af62 passed actionlint v1.7.7, AI Platform CI, zizmor, pre-commit and all applicable Freqtrade CI platform jobs.
  - command: PR #199 canonical request generation and self-validation
    result: PASS
    evidence: Canonical generator produced and validator accepted the post-repair request with workflow_sha256 7311fe6cd53e5e9a0ecec6b923a13265a0308a4c1175170774b8765c060bd74b.
  - command: PR #200 exact trigger scope
    result: PASS
    evidence: Dedicated workflow run 30011986442 passed Validate trigger PR scope before runtime or data access.
  - command: PR #200 bounded checkpoint validation
    result: FAIL
    evidence: Dedicated workflow run 30011986442 failed at Validate bounded execution checkpoint before Python setup; data and backtest jobs were skipped.
blockers: []
next_action: Merge this compact checkpoint repair, then open a new separate PR from updated develop that adds only ai_platform/experimental_model_research/run-requests/rl-v2-historical-training-execution-v1.json using the already validated post-repair canonical payload; do not merge that trigger PR after the one-shot execution.
```
