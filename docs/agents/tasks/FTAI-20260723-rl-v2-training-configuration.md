---
task_id: FTAI-20260723-rl-v2-training-configuration
status: done
branch: develop
base_branch: develop
created: 2026-07-23
updated: 2026-07-23
related_pr: "184"
owned_paths:
  - docs/agents/tasks/FTAI-20260723-rl-v2-training-configuration.md
  - docs/ai_platform/RL_V2_TRAINING_CONFIGURATION.md
  - ai_platform/experimental_model_research/rl-v2-training-configuration-v1.json
  - ai_platform/configs/rl_v2_training_research.json
  - tests/ai_platform/test_rl_v2_training_configuration.py
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260723-rl-v2-execution-preflight.md
  - docs/ai_platform/RL_V2_EXECUTION_PREFLIGHT.md
  - ai_platform/experimental_model_research/rl-v2-execution-preflight-v1.json
  - docs/ai_platform/RL_V2_RUNTIME_INTEGRATION.md
  - ai_platform/experimental_model_research/rl-v2-runtime-integration-v1.json
  - ai_platform/freqaimodels/DesiredPositionReinforcementLearner.py
  - ai_platform/strategies/AiDesiredPositionRLResearchStrategy.py
search_first:
  - current develop and open PRs before RL-v2 training-configuration work
  - active tasks or PRs overlapping RL-v2 configuration, model, strategy or experimental-research ownership
optional_reads:
  - ai_platform/scripts/rl_v2_execution_preflight.py
  - .github/workflows/ai-platform-rl-v2-execution-preflight.yml
---

# RL-v2 Training Configuration

## Goal

Create a separately declared, bounded RL-v2 training-configuration work package after the completed execution preflight. This package may add a committed, research-only configuration contract for the frozen RL-v2 desired-position runtime, but it must remain non-executing and non-result-producing.

The purpose is to make the future training surface explicit and reproducible before any run request, historical execution, evaluation-window declaration or model-performance extraction is allowed.

## Frozen parent state

The package is bound to the already merged and frozen RL-v2 chain:

- runtime integration: `rl-v2-runtime-integration-v1`;
- execution preflight: `rl-v2-execution-preflight-v1`;
- model: `DesiredPositionReinforcementLearner`;
- strategy: `AiDesiredPositionRLResearchStrategy`;
- backend family: Stable-Baselines3 through FreqAI;
- algorithm: PPO;
- policy: `MlpPolicy`;
- long-only spot semantics;
- policy actions: `0=target_flat`, `1=target_long`;
- transition, reward, action-label and observability semantics remain bound to `ai_platform.scripts.rl_v2_synthetic_reference`.

## Allowed implementation scope

This task may add only:

- a committed research-only RL-v2 configuration file with `dry_run: true`, spot-only semantics, no credentials and no live-capital path;
- a machine-readable training-configuration descriptor binding the config to the frozen runtime/preflight identities;
- explicit model, policy, action-space, reward-reference, observability and strategy bindings;
- fail-closed validation proving the committed configuration cannot silently introduce short semantics, a different model family, a different policy family, a different reward implementation, or live trading;
- dependency-light tests and documentation.

The committed configuration may define construction/training parameters needed to describe the intended RL-v2 training surface, but this task does not authorize execution geometry or execution itself.

## Non-negotiable boundaries

- No run request.
- No training or model fitting.
- No `.learn()` invocation.
- No backtest or historical execution.
- No market-data download or exchange-data access.
- No historical evaluation-window selection or declaration.
- No future evaluation-window selection or declaration.
- No strict-OOS execution or performance extraction.
- No use of consumed historical OOS `20260501-20260630`.
- No access to protected final holdout `20260801-20260930`.
- No Hyperopt, reward sweep, feature search or hyperparameter search.
- No PyTorch-vs-RL ranking.
- No promotion, profitability, superiority or live-trading claim.
- Frozen thresholds `0.006/-0.009` remain unchanged.
- Completed Phase 6 and authoritative `selected_model = null` remain unchanged.
- The configuration must remain research-only and `dry_run: true`.
- No secrets, API keys, private exchange endpoints or withdrawal capability may be committed.
- No `timerange`, `freqai.train_period_days`, `freqai.backtest_period_days` or `freqai.live_retrain_hours` may be introduced by this package; those execution-geometry choices require a later separately declared execution task.

## Required proofs

1. **Frozen runtime binding**
   - model class remains `DesiredPositionReinforcementLearner`;
   - strategy remains `AiDesiredPositionRLResearchStrategy`;
   - PPO and `MlpPolicy` remain unchanged;
   - action space remains exactly `target_flat` and `target_long`;
   - no short semantics are introduced.
2. **Canonical semantic binding**
   - transition and reward behavior remain delegated to the frozen synthetic reference;
   - reward constants are not redefined or tuned;
   - strategy action interpretation remains position-independent.
3. **Configuration safety**
   - `dry_run` is true and trading mode is spot;
   - no credentials or live-capital path are present;
   - execution-geometry keys remain absent;
   - configuration identity and parent hashes/IDs are machine-readable and versioned.
4. **Execution isolation**
   - validation must not train, fit, backtest, download data or access exchange/market data;
   - no result, trade count, strict-OOS metric, profitability metric or ranking is produced.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-23T14:03:00+02:00
head: da1d5b8abe86ec2ac57dc2293d913fdcf1c286ae
branch: develop
pr: 184
status: done
context_routes:
  - docs/agents/tasks/FTAI-20260723-rl-v2-execution-preflight.md
  - docs/ai_platform/RL_V2_EXECUTION_PREFLIGHT.md
  - ai_platform/experimental_model_research/rl-v2-execution-preflight-v1.json
owned_paths:
  - docs/agents/tasks/FTAI-20260723-rl-v2-training-configuration.md
  - docs/ai_platform/RL_V2_TRAINING_CONFIGURATION.md
  - ai_platform/experimental_model_research/rl-v2-training-configuration-v1.json
  - ai_platform/configs/rl_v2_training_research.json
  - tests/ai_platform/test_rl_v2_training_configuration.py
proven:
  - PR #168 merged the bounded RL-v2 execution preflight as ae28c4fe9d1e94313e0b232b1bcd99d6f4ba59bc and PR #177 closed its task as 4cb93b94b1b18baa3b9469ebd52fb5182ec80d03.
  - Declaration PR #182 changed only this task record and was squash-merged to develop as 960251d5534e0921e5a71b661bd4664df0deeac3.
  - PR #184 added exactly the declared research-only config, descriptor, dependency-light fail-closed tests, documentation and this task checkpoint; it added no run request, workflow or execution artifact.
  - The committed config is dry_run true, spot-only, initial_state stopped, uses empty exchange credentials and contains no timerange, train_period_days, backtest_period_days or live_retrain_hours.
  - The config keeps PPO/MlpPolicy and exact DesiredPositionReinforcementLearner/AiDesiredPositionRLResearchStrategy bindings; model_reward_parameters is empty so reward constants remain owned by the canonical synthetic reference.
  - Initial PR #184 head exposed one mypy no-redef failure in a test-only recursive key collector; diagnostic PR #185 isolated the exact failure and closed without merge, and the fix only renamed the list-branch accumulator.
  - Final PR #184 head 3650654e23869ee52344ef1bee91049aedbe3dbd passed AI Platform CI run 30004318561, zizmor run 30004318602 and Freqtrade CI run 30004318584, including pre-commit, documentation and all applicable core-platform jobs.
  - PR #184 was squash-merged to develop as da1d5b8abe86ec2ac57dc2293d913fdcf1c286ae.
  - No model training, fitting, backtest, market-data access, strict-OOS scoring, evaluation-window declaration or protected-final-holdout access occurred in this task.
  - Consumed historical OOS 20260501-20260630 and protected final holdout 20260801-20260930 remain forbidden.
  - Frozen thresholds 0.006/-0.009 and authoritative Phase 6 selected_model null remain unchanged.
derived:
  - The committed configuration is a versioned non-executing input contract; its presence does not authorize or trigger model execution.
  - Fixed training-surface values are compatibility defaults only and are not performance-tuned or supported by RL-v2 result evidence.
  - Any future model training or historical execution now requires a new prospective bounded task that separately declares execution geometry and evidence boundaries before any run request is added.
unknown: []
conflicts: []
first_failure:
  marker: resolved_test_helper_mypy_no_redef
  evidence: Initial Freqtrade CI pre-commit failed only because tests/ai_platform/test_rl_v2_training_configuration.py reused the local name keys in two branches of _collect_keys; diagnostic PR #185 proved the marker and final head 3650654e23869ee52344ef1bee91049aedbe3dbd passed pre-commit after renaming the list accumulator to list_keys.
rejected_hypotheses:
  - Add a run request or execution manifest in the training-configuration task.
  - Add timerange, train_period_days, backtest_period_days or live_retrain_hours to make the config executable.
  - Reuse consumed historical OOS 20260501-20260630 for RL-v2 tuning or validation.
  - Access protected final holdout 20260801-20260930.
  - Define reward constants in model_reward_parameters or retune the frozen reward reference.
  - Rank or promote RL-v2 against PyTorch or completed Phase 6 candidates.
changed_paths:
  - docs/agents/tasks/FTAI-20260723-rl-v2-training-configuration.md
  - docs/ai_platform/RL_V2_TRAINING_CONFIGURATION.md
  - ai_platform/experimental_model_research/rl-v2-training-configuration-v1.json
  - ai_platform/configs/rl_v2_training_research.json
  - tests/ai_platform/test_rl_v2_training_configuration.py
validation:
  - command: PR #184 final AI Platform CI
    result: PASS
    evidence: Run 30004318561 passed compile, AI Platform tests, Ruff lint, Ruff format, Codespell and JSON validation on final head 3650654e23869ee52344ef1bee91049aedbe3dbd.
  - command: PR #184 final zizmor
    result: PASS
    evidence: Run 30004318602 completed successfully on final head 3650654e23869ee52344ef1bee91049aedbe3dbd.
  - command: PR #184 final Freqtrade CI
    result: PASS
    evidence: Run 30004318584 completed successfully, including CI scope, pre-commit, documentation and all applicable core-platform jobs on final head 3650654e23869ee52344ef1bee91049aedbe3dbd.
blockers: []
next_action: Declare a separate bounded RL-v2 training-execution work package that prospectively defines execution geometry and evidence boundaries before adding any run request, model training, historical execution or strict-OOS scoring; consumed OOS 20260501-20260630 and protected final holdout 20260801-20260930 must remain forbidden.
```
