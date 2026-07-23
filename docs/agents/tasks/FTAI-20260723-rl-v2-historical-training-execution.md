---
task_id: FTAI-20260723-rl-v2-historical-training-execution
status: active
branch: develop
base_branch: develop
created: 2026-07-23
updated: 2026-07-23
related_pr: "196"
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
updated_at: 2026-07-23T15:30:43+02:00
head: a1910dcc934b0d185a1e3378b61fee90ada0bfba
branch: develop
pr: 196
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
  - PR #184 merged the frozen non-executing RL-v2 training configuration as da1d5b8abe86ec2ac57dc2293d913fdcf1c286ae and PR #186 closed its task as a42858a6b6b2accdf47f78fa71cee557b3352448.
  - Declaration PR #187 changed only the new bounded task record and was squash-merged to develop as c663626ea8581fe82c107f959873d8c260927881 before implementation began.
  - PR #188 added only the declared execution contract, canonical request validator/materializer, guarded request-triggered workflow, fail-closed tests, documentation and task checkpoint; it did not add the canonical run-request file.
  - The frozen geometry uses download 20250801-20260501 and execution 20260301-20260501 with exclusive May 1 stop, train_period_days 90 and backtest_period_days 61; consumed historical OOS 20260501-20260630 is outside all declared execution/data geometry.
  - The workflow uses a dedicated rl-v2-historical-training-pre-oos-v1 cache namespace with no restore-keys fallback and does not call the strict-OOS extractor.
  - Existing experimental historical execution infrastructure is hard-bound to pytorch-research-v1/rl-research-v1 and May-June strict-OOS extraction, so PR #188 uses a separate RL-v2-specific guard rather than weakening the frozen older contract.
  - Initial PR #188 validation exposed only 11 Ruff E501 formatting violations and later 13 mypy inference errors for heterogeneous frozen dictionaries; diagnostic PRs #189 and #190 isolated those exact markers and closed without merge, and both were resolved without changing contract values, execution geometry or workflow semantics.
  - Final PR #188 head 3a565198c317fae9f1a49236bb9696c46f1f388f passed AI Platform CI run 30006965475 and zizmor run 30006965476.
  - Freqtrade CI run 30006965504 completed every applicable job successfully on final head 3a565198c317fae9f1a49236bb9696c46f1f388f, including CI scope, pre-commit, documentation, Ubuntu Python 3.11-3.14, macOS and Windows; the connector aggregate status remained stale after job completion.
  - PR #188 was squash-merged to develop as aa974bb16d8724d171c5ebc45e26a3a8cfc63841.
  - Canonical trigger PRs #193 and #195 each added exactly the run-request file but produced zero dedicated RL-v2 workflow runs; both were closed without merge and consumed no one-shot execution.
  - Read-only Actions API diagnostics in PR #194 proved the dedicated workflow was registered but had zero pull-request runs; actionlint isolated the cause to job-level env use of the unavailable runner context in RUN_CONFIG.
  - Repair PR #196 removed job-level `${{ runner.temp }}`, uses `$RUNNER_TEMP` only inside execution steps, and added a fail-closed regression test without changing frozen execution geometry, model, strategy, config, cache policy, OOS boundary or holdout boundary.
  - Exact repair head 612beb0060171df2fb85b203763590d3a2d7af62 passed actionlint v1.7.7, AI Platform CI, zizmor, pre-commit and every applicable Freqtrade CI platform job.
  - PR #196 was squash-merged to develop as a1910dcc934b0d185a1e3378b61fee90ada0bfba.
  - No RL-v2 model training, backtest, market-data download or historical evidence execution has occurred yet; the one-shot execution remains unconsumed.
  - The protected final holdout 20260801-20260930 remains unused and forbidden.
  - Frozen thresholds 0.006/-0.009 and Phase 6 selected_model null remain unchanged.
derived:
  - Because PR #196 changed the workflow bytes, the pre-repair canonical request is stale by design and must not be reused.
  - A new canonical request must be generated from develop after a1910dcc934b0d185a1e3378b61fee90ada0bfba so its workflow_sha256 binds the repaired workflow.
  - March-April output from the later trigger is historical development evidence only and must not be treated as strict OOS, protected final validation or promotion evidence.
unknown:
  - Whether the first real FreqAI RL execution accepts the direct frozen freqtrade backtesting surface without an additional runtime adapter; no dedicated RL-v2 execution workflow has run yet.
conflicts: []
first_failure:
  marker: resolved_workflow_registration_context
  evidence: Trigger PRs #193 and #195 created zero dedicated workflow runs. Read-only Actions API plus actionlint isolated the exact defect to job-level env use of `${{ runner.temp }}`. PR #196 moved runtime-config path construction to step-level shell use of `$RUNNER_TEMP`, passed actionlint and repository CI, and merged without executing the model.
rejected_hypotheses:
  - Treat PR #193 or #195 as consumed one-shot executions despite zero dedicated workflow runs.
  - Reuse the pre-repair canonical request after workflow bytes changed.
  - Reuse consumed OOS 20260501-20260630 as RL-v2 evaluation evidence.
  - Access protected final holdout 20260801-20260930.
  - Call March-April evidence strict OOS or final validation.
  - Restore older historical caches that may contain May-June or later data.
  - Retune PPO, policy, reward, features or thresholds from this execution package.
  - Rank RL-v2 against PyTorch or completed Phase 6 candidates.
changed_paths:
  - .github/workflows/ai-platform-rl-v2-historical-training-execution.yml
  - tests/ai_platform/test_rl_v2_historical_training_execution.py
validation:
  - command: actionlint v1.7.7 on exact PR #196 head
    result: PASS
    evidence: Diagnostic PR #197 validated .github/workflows/ai-platform-rl-v2-historical-training-execution.yml from exact repair head 612beb0060171df2fb85b203763590d3a2d7af62 successfully and was closed without merge.
  - command: PR #196 AI Platform CI and zizmor
    result: PASS
    evidence: AI Platform CI run 30009223919 and zizmor run 30009223948 completed successfully on exact repair head 612beb0060171df2fb85b203763590d3a2d7af62.
  - command: PR #196 Freqtrade CI platform jobs
    result: PASS
    evidence: Run 30009223862 completed every applicable individual job successfully, including pre-commit and Ubuntu, macOS and Windows platform jobs; the connector aggregate status remained stale after job completion.
blockers: []
next_action: Generate a fresh canonical request from develop after repair merge a1910dcc934b0d185a1e3378b61fee90ada0bfba, open a separate PR adding exactly ai_platform/experimental_model_research/run-requests/rl-v2-historical-training-execution-v1.json, verify the repaired dedicated workflow actually starts, and do not merge the trigger PR after one-shot execution.
```
