---
task_id: FTAI-20260723-rl-v2-execution-preflight
status: active
branch: docs/rl-v2-execution-preflight-task
base_branch: develop
created: 2026-07-23
updated: 2026-07-23
related_pr: ""
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

A later implementation under this task may add only:

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
updated_at: 2026-07-23T01:12:00+02:00
head: 9a5abdf3ce4fcbe0feb5b9a278f237796c8bcd92
branch: docs/rl-v2-execution-preflight-task
pr: none
status: investigating
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
  - PR #151 merged the frozen RL-v2 desired-position runtime integration as 251fa56aeaaa8fb95c7cdf73015da0c1142dc978.
  - PR #160 closed the RL-v2 runtime integration task on develop as 9a5abdf3ce4fcbe0feb5b9a278f237796c8bcd92.
  - Final PR #151 AI Platform CI 29962856917, runtime smoke 29962856904, zizmor 29962857057 and Freqtrade CI 29962856870 succeeded.
  - The merged runtime exposes exactly target_flat and target_long desired-position actions with canonical synthetic transition, reward and observability bindings.
  - No current open PR overlaps the declared RL-v2 execution-preflight owned paths.
  - Stale duplicate runtime-integration PR #154 was closed without merge after the authoritative PR #151/#160 state was discovered.
  - Consumed historical OOS 20260501-20260630 remains forbidden.
  - Protected final holdout 20260801-20260930 remains unused and forbidden.
  - Frozen thresholds 0.006/-0.009 and authoritative Phase 6 selected_model null remain unchanged.
derived:
  - The next safe RL-v2 work is a non-result-producing execution preflight only.
  - No evaluation window may be selected or declared by this task.
  - Any later training or historical execution requires a separate prospectively declared task after this preflight is merged and frozen.
unknown:
  - Exact minimal configuration keys required for safe current-runtime model construction and resolver checks.
  - Whether current FreqAI resolution requires a dedicated ephemeral in-memory config shape beyond the merged runtime-smoke construction path.
conflicts: []
first_failure:
  marker: none
  evidence: Declaration-only task; no preflight implementation, model execution, data access, training, or backtest has occurred.
rejected_hypotheses:
  - Add a committed training config, experiment manifest, or run request in this task.
  - Select a historical or future evaluation window during preflight.
  - Reuse consumed historical OOS 20260501-20260630.
  - Access protected final holdout 20260801-20260930.
  - Train, fit, download data, or backtest during preflight.
  - Rank or promote RL-v2 against PyTorch from this task.
changed_paths:
  - docs/agents/tasks/FTAI-20260723-rl-v2-execution-preflight.md
validation:
  - command: live develop and overlap preflight
    result: PASS
    evidence: develop is 9a5abdf3ce4fcbe0feb5b9a278f237796c8bcd92; open PRs #158, #159 and #109 do not overlap RL-v2 preflight paths, and duplicate #154 is closed without merge.
blockers: []
next_action: Implement the bounded RL-v2 execution preflight from current develop using only non-result-producing resolver and configuration-surface checks, then merge it only after checkpoint, AI Platform CI, Freqtrade CI, zizmor and any dedicated preflight workflow are green.
```
