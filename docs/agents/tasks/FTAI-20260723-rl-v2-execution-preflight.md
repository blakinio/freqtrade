---
task_id: FTAI-20260723-rl-v2-execution-preflight
status: active
branch: fix/rl-v2-execution-preflight-ruff
base_branch: develop
created: 2026-07-23
updated: 2026-07-23
related_pr: "168"
owned_paths:
  - docs/agents/tasks/FTAI-20260723-rl-v2-execution-preflight.md
  - docs/ai_platform/RL_V2_EXECUTION_PREFLIGHT.md
  - ai_platform/experimental_model_research/rl-v2-execution-preflight-v1.json
  - ai_platform/scripts/rl_v2_execution_preflight.py
  - tests/ai_platform/test_rl_v2_execution_preflight.py
  - .github/workflows/ai-platform-rl-v2-execution-preflight.yml
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260722-rl-v2-runtime-integration.md
  - docs/ai_platform/RL_V2_RUNTIME_INTEGRATION.md
  - ai_platform/experimental_model_research/rl-v2-runtime-integration-v1.json
  - ai_platform/freqaimodels/DesiredPositionReinforcementLearner.py
  - ai_platform/strategies/AiDesiredPositionRLResearchStrategy.py
search_first:
  - current develop and open PRs before RL-v2 execution-preflight work
  - active tasks or PRs overlapping RL-v2 preflight ownership
optional_reads:
  - .github/workflows/experimental-model-runtime-smoke.yml
  - ai_platform/scripts/experimental_model_runtime_smoke.py
---

# RL-v2 Execution Preflight

## Goal

Create a bounded, non-result-producing execution preflight for the merged and frozen RL-v2 desired-position runtime integration. The preflight may prove current runtime symbol resolution, strategy resolution, configuration-surface requirements, action/reward binding, and observability compatibility, but it may not train, fit, backtest, download market data, select an evaluation window, or produce performance evidence.

## Frozen parent state

The parent runtime integration is complete and frozen on `develop`:

- runtime integration merge: `251fa56aeaaa8fb95c7cdf73015da0c1142dc978` from PR #151;
- closure commit: `9a5abdf3ce4fcbe0feb5b9a278f237796c8bcd92` from PR #160;
- model: `DesiredPositionReinforcementLearner`;
- strategy: `AiDesiredPositionRLResearchStrategy`;
- backend family: Stable-Baselines3 through FreqAI;
- algorithm: PPO;
- policy: MLP policy;
- long-only spot semantics;
- policy actions: `0=target_flat`, `1=target_long`;
- transition, reward, action-label, and observability semantics remain bound to `ai_platform.scripts.rl_v2_synthetic_reference`.

## Allowed implementation scope

This task may add only:

- a machine-readable preflight descriptor defining required configuration keys and fail-closed constraints;
- a preflight script that resolves the merged model and strategy under current repository runtime dependencies;
- ephemeral or in-memory configuration materialization solely for construction/resolver checks, with no committed executable training configuration;
- proof that the action space remains exactly the two frozen desired-position actions;
- proof that PPO, MLP policy, long-only semantics, transition/reward bindings, and observability vocabulary remain unchanged;
- dependency-light tests plus a bounded heavy-runtime import/construction check if it does not call training, fitting, backtesting, data download, or market-data access;
- a dedicated preflight-only workflow with no result-producing job;
- documentation.

## Non-negotiable boundaries

- No committed training config.
- No experiment manifest.
- No run request.
- No training or model fitting.
- No backtest or historical execution.
- No market-data download or exchange-data access.
- No historical evaluation-window selection or declaration.
- No future evaluation-window selection or declaration.
- No strict-OOS execution or performance extraction.
- No use of consumed historical OOS `20260501-20260630`.
- No access to protected final holdout `20260801-20260930`.
- No Hyperopt, reward sweep, feature search, or hyperparameter search.
- No PyTorch-vs-RL ranking.
- No promotion, profitability, superiority, or live-trading claim.
- Frozen thresholds `0.006/-0.009` remain unchanged.
- Completed Phase 6 and authoritative `selected_model = null` remain unchanged.

## Required proofs

1. **Runtime resolution**
   - the exact merged `DesiredPositionReinforcementLearner` symbol resolves with current heavy `freqai_rl` dependencies;
   - the exact merged `AiDesiredPositionRLResearchStrategy` symbol resolves;
   - any construction check is bounded and does not call `.learn()`, fit, backtest, downloader, or market data.
2. **Configuration surface**
   - required keys for safe construction/resolution are identified;
   - missing or incompatible PPO/MLP/long-only requirements fail closed;
   - no executable training config or timerange is committed by this task.
3. **Semantic binding**
   - action space remains exactly `target_flat` and `target_long`;
   - canonical transition/reward/action-label bindings remain unchanged;
   - no short semantics or hidden position-dependent policy action meaning is introduced.
4. **Observability and isolation**
   - canonical zero-count action buckets and separate prediction/signal/trade/OOS layers remain resolvable;
   - runtime counts are not fabricated because no execution occurs;
   - consumed OOS and protected final holdout remain unreachable from the preflight path.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-23T10:48:00+02:00
head: d52c0649130d2b37a6b0980e3d84f31a16021e49
branch: fix/rl-v2-execution-preflight-ruff
pr: 168
status: validating
context_routes:
  - docs/agents/tasks/FTAI-20260722-rl-v2-runtime-integration.md
  - docs/ai_platform/RL_V2_RUNTIME_INTEGRATION.md
  - ai_platform/experimental_model_research/rl-v2-runtime-integration-v1.json
owned_paths:
  - docs/agents/tasks/FTAI-20260723-rl-v2-execution-preflight.md
  - docs/ai_platform/RL_V2_EXECUTION_PREFLIGHT.md
  - ai_platform/experimental_model_research/rl-v2-execution-preflight-v1.json
  - ai_platform/scripts/rl_v2_execution_preflight.py
  - tests/ai_platform/test_rl_v2_execution_preflight.py
  - .github/workflows/ai-platform-rl-v2-execution-preflight.yml
proven:
  - PR #151 merged the frozen RL-v2 desired-position runtime integration as 251fa56aeaaa8fb95c7cdf73015da0c1142dc978 and PR #160 closed its task as 9a5abdf3ce4fcbe0feb5b9a278f237796c8bcd92.
  - Declaration PR #161 passed Freqtrade CI 29965391425 and zizmor 29965391458, then merged to develop as f3d486068110491a302872ecc4e668939ba72930.
  - The implementation contains only the declared descriptor, ephemeral config builder, resolver/construction checks, fail-closed tests, dedicated preflight workflow, documentation, and this task record.
  - Ephemeral config declares no timerange, train_period_days, backtest_period_days, or live_retrain_hours and rejects those execution-geometry keys if introduced.
  - The preflight source contains no fit, learn, train, backtest, or download invocation and constructs only synthetic in-memory frames.
  - AI Platform CI proved compile and lightweight tests pass; its initial Ruff McCabe failure was isolated to _runtime_checks complexity 13 and resolved by splitting bounded helper checks.
  - Dedicated preflight CI initially failed before assertions because repository pytest addopts require xdist; pytest-xdist and pytest-asyncio were added to the dedicated validation environment.
  - Exact Ruff 0.15.21 format diffs were captured by temporary read-only diagnostics; the script diff was empty and the sole test diff was applied exactly, after which diagnostic workflows were removed from the final deliverable.
  - Stale/superseded PRs #162, #163, #164 and #166 were closed without merge; PR #168 is the sole implementation candidate.
  - Consumed historical OOS 20260501-20260630 and protected final holdout 20260801-20260930 remain forbidden and unreachable from the preflight configuration surface.
  - Frozen thresholds 0.006/-0.009 and authoritative Phase 6 selected_model null remain unchanged.
derived:
  - The explicit minimal construction surface is sufficient in principle for current resolver checks without committing a training configuration or evaluation geometry.
  - Successful dedicated heavy-runtime CI would prove runtime resolvability only and would not be model-performance evidence.
unknown:
  - Whether current FreqAI and StrategyResolver accept the declared minimal ephemeral config without additional construction-only keys.
  - Whether current develop advancement requires replaying the six final owned implementation paths onto a fresh base before merge.
conflicts: []
first_failure:
  marker: resolved_validation_infrastructure_and_formatting
  evidence: Early validation exposed three non-performance blockers: Ruff McCabe complexity 13, pytest --dist without pytest-xdist, and one Ruff test-format diff; each was remediated without training, backtesting, market data, evaluation geometry, or holdout access.
rejected_hypotheses:
  - Add a committed training config, experiment manifest, or run request in this task.
  - Select a historical or future evaluation window during preflight.
  - Reuse consumed historical OOS 20260501-20260630 or access protected final holdout 20260801-20260930.
  - Train, fit, download data, backtest, or score performance during preflight.
  - Rank or promote RL-v2 against PyTorch from this task.
changed_paths:
  - docs/agents/tasks/FTAI-20260723-rl-v2-execution-preflight.md
  - docs/ai_platform/RL_V2_EXECUTION_PREFLIGHT.md
  - ai_platform/experimental_model_research/rl-v2-execution-preflight-v1.json
  - ai_platform/scripts/rl_v2_execution_preflight.py
  - tests/ai_platform/test_rl_v2_execution_preflight.py
  - .github/workflows/ai-platform-rl-v2-execution-preflight.yml
validation:
  - command: required reads and incremental live-state verification
    result: PASS
    evidence: Required governance, architecture, frozen runtime integration, resolver, and existing heavy-runtime construction surfaces were inspected before implementation.
  - command: AI Platform CI diagnostic validation
    result: FAIL
    evidence: Compile and lightweight AI tests passed; early runs isolated McCabe complexity and then Ruff formatting as the first failures, which were remediated without expanding execution scope.
  - command: dedicated RL-v2 execution-preflight diagnostic validation
    result: FAIL
    evidence: Heavy dependencies installed successfully; early pytest failed because pyproject addopts require pytest-xdist, which is now installed by the final dedicated workflow.
  - command: local targeted pytest/compile/Ruff
    result: NOT_RUN
    evidence: No repository checkout is mounted in the current sandbox; executable validation is delegated to repository CI and the dedicated preflight workflow without substituting model execution.
blockers: []
next_action: Synchronize PR #168 to this final checkpoint head, run AI Platform CI, Freqtrade CI, zizmor and the dedicated RL-v2 execution-preflight workflow on the exact latest head, fix only the first concrete failure if any, otherwise merge after verifying compatibility with current develop and close the task checkpoint.
```
