---
task_id: FTAI-20260723-rl-v2-execution-preflight
status: done
branch: develop
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
updated_at: 2026-07-23T12:04:00+02:00
head: ae28c4fe9d1e94313e0b232b1bcd99d6f4ba59bc
branch: develop
pr: 168
status: ready
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
  - Declaration PR #161 merged to develop as f3d486068110491a302872ecc4e668939ba72930 before implementation work began.
  - PR #168 added only the declared descriptor, ephemeral configuration builder, resolver and construction checks, fail-closed tests, dedicated preflight workflow and documentation; it added no training config, experiment manifest, run request or evaluation window.
  - The ephemeral configuration declares no timerange, train_period_days, backtest_period_days or live_retrain_hours and rejects those execution-geometry keys if introduced.
  - The preflight source contains no fit, learn, train, backtest or download invocation and constructs only synthetic in-memory frames.
  - Final AI Platform CI run 29996056913 completed successfully on PR #168 head e262687e7900bc1ddd9e6e3b537c5a93d1635e68.
  - Final dedicated RL-v2 execution-preflight run 29996057022 installed heavy freqai_rl dependencies, passed targeted tests and completed bounded resolver, construction, semantic and observability validation successfully.
  - Final zizmor run 29996056962 completed successfully on the exact final PR #168 head.
  - Freqtrade CI run 29996057493 had all applicable jobs complete successfully, including pre-commit, documentation and the Python 3.11-3.14, macOS and Windows core matrix; the connector aggregate status remained stale after job completion.
  - PR #168 was squash-merged to develop as ae28c4fe9d1e94313e0b232b1bcd99d6f4ba59bc.
  - Consumed historical OOS 20260501-20260630 and protected final holdout 20260801-20260930 were not accessed and remain forbidden.
  - Frozen thresholds 0.006/-0.009 and authoritative Phase 6 selected_model null remain unchanged.
derived:
  - The minimal ephemeral configuration is sufficient for current resolver and synthetic construction preflight only; it is not a committed training configuration.
  - Successful bounded preflight is runtime-resolvability evidence only and is not model-performance, profitability or superiority evidence.
  - Any future training configuration, run request, model execution or evaluation-window declaration requires a separate prospectively declared bounded task.
unknown: []
conflicts: []
first_failure:
  marker: resolved_preflight_validation_chain
  evidence: Validation exposed Ruff McCabe and format issues, missing pytest plugins, dynamic resolver class identity, static IFreqaiModel typing and NumPy JSON scalar serialization; all were resolved without training, backtesting, market data, evaluation geometry, OOS scoring or holdout access.
rejected_hypotheses:
  - Add a committed training config, experiment manifest or run request in this task.
  - Select a historical or future evaluation window during preflight.
  - Reuse consumed historical OOS 20260501-20260630 or access protected final holdout 20260801-20260930.
  - Train, fit, download data, backtest or score performance during preflight.
  - Rank or promote RL-v2 against PyTorch from this task.
changed_paths:
  - docs/agents/tasks/FTAI-20260723-rl-v2-execution-preflight.md
  - docs/ai_platform/RL_V2_EXECUTION_PREFLIGHT.md
  - ai_platform/experimental_model_research/rl-v2-execution-preflight-v1.json
  - ai_platform/scripts/rl_v2_execution_preflight.py
  - tests/ai_platform/test_rl_v2_execution_preflight.py
  - .github/workflows/ai-platform-rl-v2-execution-preflight.yml
validation:
  - command: PR #168 final AI Platform CI
    result: PASS
    evidence: Run 29996056913 passed compile, AI Platform tests, Ruff lint, Ruff format, Codespell and JSON validation on final head e262687e7900bc1ddd9e6e3b537c5a93d1635e68.
  - command: PR #168 final RL-v2 execution preflight
    result: PASS
    evidence: Run 29996057022 passed checkpoint validation, heavy dependency installation, targeted tests and the bounded runtime preflight without training or historical execution.
  - command: PR #168 final zizmor
    result: PASS
    evidence: Run 29996056962 completed successfully on the exact final head.
  - command: PR #168 final Freqtrade CI
    result: PASS
    evidence: Run 29996057493 completed all applicable jobs successfully, including pre-commit, documentation and the core platform matrix; the connector aggregate status remained stale after successful job completion.
blockers: []
next_action: Declare a separate bounded RL-v2 training or execution work package before adding any committed training config, experiment manifest, run request, historical or future evaluation window, model training, backtest, strict-OOS scoring or final-holdout access.
```
