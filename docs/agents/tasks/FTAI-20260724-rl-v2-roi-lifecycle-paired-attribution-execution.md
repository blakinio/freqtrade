---
task_id: FTAI-20260724-rl-v2-roi-lifecycle-paired-attribution-execution
status: active
branch: docs/rl-v2-roi-lifecycle-paired-attribution-declaration
base_branch: develop
created: 2026-07-24
updated: 2026-07-24
related_pr: null
owned_paths:
  - docs/agents/tasks/FTAI-20260724-rl-v2-roi-lifecycle-paired-attribution-execution.md
  - docs/ai_platform/RL_V2_ROI_LIFECYCLE_PAIRED_ATTRIBUTION_EXECUTION.md
  - ai_platform/experimental_model_research/rl-v2-roi-lifecycle-paired-attribution-execution-contract-v1.json
  - ai_platform/scripts/rl_v2_roi_lifecycle_paired_attribution_run_request.py
  - ai_platform/scripts/rl_v2_roi_lifecycle_paired_attribution_evidence.py
  - tests/ai_platform/test_rl_v2_roi_lifecycle_paired_attribution.py
  - .github/workflows/ai-platform-rl-v2-roi-lifecycle-paired-attribution.yml
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260724-rl-v2-historical-evidence-diagnosis.md
  - docs/ai_platform/RL_V2_HISTORICAL_EVIDENCE_DIAGNOSIS.md
  - ai_platform/experimental_model_research/rl-v2-historical-evidence-diagnosis-v1.json
  - docs/agents/tasks/FTAI-20260724-rl-v2-roi-lifecycle-alignment.md
  - docs/ai_platform/RL_V2_ROI_LIFECYCLE_ALIGNMENT.md
  - ai_platform/experimental_model_research/rl-v2-roi-lifecycle-alignment-v1.json
  - docs/agents/tasks/FTAI-20260723-rl-v2-historical-training-execution.md
  - docs/ai_platform/RL_V2_HISTORICAL_TRAINING_EXECUTION.md
search_first:
  - current develop and open PRs overlapping RL-v2 execution, lifecycle attribution, model, strategy, config or experimental-research ownership
optional_reads:
  - ai_platform/scripts/rl_v2_historical_training_execution_run_request.py
  - .github/workflows/ai-platform-rl-v2-historical-training-execution.yml
  - tests/ai_platform/test_rl_v2_historical_training_execution.py
---

# RL-v2 ROI Lifecycle Paired Attribution Execution

## Goal

Build a new, separately bounded, one-shot historical-development attribution path that executes only
the merged lifecycle-aligned RL-v2 variant and compares its mechanistic lifecycle metrics against the
already completed immutable baseline evidence.

The baseline model/backtest must not be rerun. The existing completed trigger path must not be reused.
The infrastructure implementation PR must remain inert and may not train, backtest, download market
data, or add a canonical run request.

## Frozen identities

Baseline evidence:

- workflow run: `30022863894`;
- trigger PR: `#218`, closed without merge;
- artifact: `rl-v2-historical-training-execution-218`;
- artifact digest:
  `sha256:5d74d87bf4408c7b51779cd9038d815c88d3f5cc193cd229b6757edf32112b55`;
- committed diagnosis:
  `ai_platform/experimental_model_research/rl-v2-historical-evidence-diagnosis-v1.json`;
- baseline strategy: `AiDesiredPositionRLResearchStrategy`;
- baseline strategy SHA-256:
  `9318a4d13937d9b572c4bcecfb56f999fd82d8309c6f898d0166c0c71dfd5c19`.

Experimental variant:

- strategy: `AiDesiredPositionRLLifecycleAlignedResearchStrategy`;
- strategy SHA-256:
  `366785129798d1332ce593f919c54aa23eefb2b15b2d850ab32d5c5cbdf0d5b7`;
- only semantic delta: `ignore_roi_if_entry_signal=True`;
- model: `DesiredPositionReinforcementLearner`;
- model SHA-256:
  `3cec25cc7b43e3214a8e22d153107307a7a7bfbfd48b6bf313ecb4624cb79d46`;
- config: `ai_platform/configs/rl_v2_training_research.json`;
- config SHA-256:
  `5adc805deadcfe6dc3c52d0745f62546952a96b38b3bd06bc28ac9987063f6de`;
- separate runtime identifier:
  `rl-v2-roi-lifecycle-paired-attribution-v1`.

## Prospectively frozen geometry

The experimental run must use the same already-known development geometry as the immutable baseline:

- download timerange: `20250801-20260501`, end-exclusive;
- trailing training geometry: `train_period_days = 90`;
- execution timerange: `20260301-20260501`, end-exclusive;
- semantic evidence window: `20260301-20260430`;
- `backtest_period_days = 61`;
- pairs: `BTC/USDT`, `ETH/USDT`;
- timeframes: `15m`, `1h`, `4h`;
- exchange: Kraken spot;
- fee: `0.002`;
- PPO / `MlpPolicy` and seed `42` remain frozen.

This window was already used to diagnose and select the lifecycle hypothesis. The result is therefore
paired historical-development attribution only. It is not strict OOS, fresh validation, or protected
final validation.

## Frozen attribution semantics

The baseline is represented by the committed diagnosis values bound to the immutable artifact digest.
It must not be retrained or rerun.

Primary baseline mechanism values:

- ROI exits: `122`;
- ROI exits followed by same-pair re-entry after exactly 15 minutes: `122`;
- immediate ROI/stop-loss external-exit and same-pair 15-minute re-entry boundaries: `131`;
- close-plus-reopen fees at those boundaries: `52.582123 USDT`.

The experimental evidence extractor must calculate the same definitions from raw variant trades.

The lifecycle hypothesis is directionally supported only when both are true:

1. ROI exits followed by same-pair 15-minute re-entry are fewer than `122`;
2. immediate external-exit/re-entry boundary fees are below `52.582123 USDT`.

These are mechanistic attribution criteria, not profitability gates. Net PnL, profit factor, trade count,
drawdown, target-flat exits and stop-losses are secondary descriptive evidence only.

A negative, neutral, zero-trade, or execution-failure result remains valid evidence. No automatic
selection, promotion, superiority, or profitability conclusion may be produced.

## Allowed implementation scope

- immutable machine-readable attribution execution contract;
- canonical request generator and validator bound to exact tracked inputs;
- request-triggered workflow that is inert until a separate one-file trigger PR;
- runtime materialization that changes only the isolated FreqAI identifier and frozen 90/61-day
  execution geometry;
- exact baseline evidence, model, config, strategy, validator and workflow hash binding;
- fail-closed market-data coverage restricted to the declared pre-OOS range;
- exactly one variant-only FreqAI historical training/backtest after a later canonical trigger;
- deterministic raw-trade evidence extraction using prospectively frozen metric definitions;
- immutable artifact upload, tests and documentation.

## Non-negotiable boundaries

- No baseline retraining or baseline backtest rerun.
- No canonical run-request file in declaration or infrastructure implementation PRs.
- No model training, `.learn()`, backtest or market-data download before the later trigger PR.
- No PPO, policy, reward, feature, pair, timeframe, fee, ROI schedule, stop-loss, action-semantics or
  threshold mutation.
- No target-flat tuning or additional cooldown.
- No use or access of consumed historical OOS `20260501-20260630`.
- No access to protected final holdout `20260801-20260930`.
- No strict-OOS, final-validation, ranking, promotion, profitability, superiority, dry-run or live claim.
- Frozen thresholds `0.006/-0.009` and Phase 6 `selected_model=null` remain unchanged.
- Any later canonical trigger must be a separate exact-one-file PR and must be closed without merge.

## Required proofs

1. **Single-variable identity**
   - exact variant strategy hash and one semantic delta remain bound;
   - model, config, reward, features and execution geometry cannot drift.
2. **Baseline non-rerun**
   - baseline values are read only from the committed diagnosis bound to the immutable artifact digest;
   - no baseline model or backtest command exists in the workflow.
3. **Execution separation**
   - infrastructure merge remains inert;
   - a later trigger must add exactly one canonical request file;
   - exact trigger head is checked out before data access or execution.
4. **Attribution honesty**
   - evidence is labeled `paired_historical_development_attribution`, `strict_oos=false` and
     `protected_final_validation=false`;
   - mechanistic criteria are evaluated separately from profitability;
   - negative or failed evidence is retained without promotion language.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-24T11:15:00+02:00
head: 353e215b1cc694c9b982f1a214b6f5cc96003690
branch: docs/rl-v2-roi-lifecycle-paired-attribution-declaration
pr: null
status: ready
context_routes:
  - docs/agents/tasks/FTAI-20260724-rl-v2-historical-evidence-diagnosis.md
  - docs/agents/tasks/FTAI-20260724-rl-v2-roi-lifecycle-alignment.md
  - docs/agents/tasks/FTAI-20260723-rl-v2-historical-training-execution.md
owned_paths:
  - docs/agents/tasks/FTAI-20260724-rl-v2-roi-lifecycle-paired-attribution-execution.md
  - docs/ai_platform/RL_V2_ROI_LIFECYCLE_PAIRED_ATTRIBUTION_EXECUTION.md
  - ai_platform/experimental_model_research/rl-v2-roi-lifecycle-paired-attribution-execution-contract-v1.json
  - ai_platform/scripts/rl_v2_roi_lifecycle_paired_attribution_run_request.py
  - ai_platform/scripts/rl_v2_roi_lifecycle_paired_attribution_evidence.py
  - tests/ai_platform/test_rl_v2_roi_lifecycle_paired_attribution.py
  - .github/workflows/ai-platform-rl-v2-roi-lifecycle-paired-attribution.yml
proven:
  - PR #218 produced immutable baseline artifact rl-v2-historical-training-execution-218 from run 30022863894 and was closed without merge.
  - PR #237 merged diagnosis 49167cdf9ab6fd126de72613101c35fef6cc07e2, binding baseline accounting and lifecycle metrics to artifact digest sha256:5d74d87bf4408c7b51779cd9038d815c88d3f5cc193cd229b6757edf32112b55.
  - PR #238 prospectively declared ignore_roi_if_entry_signal=true as the only lifecycle variant delta and merged as 9d5cc48db3aaa72995b10214642be6064ad5e00e.
  - PR #240 implemented the versioned variant and merged as 09044f824ea102955147900f3d6d5e8f83929c0a after AI Platform CI, zizmor and full cross-platform Freqtrade CI passed.
  - PR #245 closed the lifecycle implementation task as 353e215b1cc694c9b982f1a214b6f5cc96003690 without executing a model or accessing market data.
  - Variant strategy SHA-256 is 366785129798d1332ce593f919c54aa23eefb2b15b2d850ab32d5c5cbdf0d5b7 and baseline strategy remains unchanged.
  - Baseline primary metrics are 122 ROI exits, 122 ROI-to-15m re-entries, 131 immediate ROI/stop-loss boundaries and 52.582123 USDT boundary fees.
  - The exact execution geometry remains download 20250801-20260501, execution 20260301-20260501, 90/61-day training/backtest, BTC/USDT plus ETH/USDT, 15m/1h/4h, Kraken spot and fee 0.002.
  - The already-used March-April window is development attribution only and cannot become strict OOS or final validation.
  - Consumed OOS 20260501-20260630 and protected final holdout 20260801-20260930 remain forbidden; thresholds stay 0.006/-0.009 and Phase 6 selected_model remains null.
derived:
  - A variant-only run plus immutable committed baseline metrics is sufficient for paired mechanistic attribution without rerunning the baseline.
  - A separate runtime identifier is required to prevent model-artifact collision while preserving model semantics.
  - Mechanistic churn reduction and net profitability must remain separate conclusions.
unknown:
  - Whether the lifecycle-aligned variant reduces the two prospectively frozen primary churn metrics.
conflicts: []
first_failure:
  marker: unresolved_paired_lifecycle_attribution
  evidence: The variant is implemented and validated but has not been trained or backtested; its effect relative to the immutable baseline remains unknown.
rejected_hypotheses:
  - Rerun the baseline model or baseline backtest.
  - Reuse the completed #218 trigger path.
  - Combine lifecycle alignment with target-flat, reward, PPO, feature, threshold, stop-loss or cooldown tuning.
  - Treat lower net loss or positive PnL as the primary success criterion.
  - Use consumed OOS 20260501-20260630.
  - Access protected final holdout 20260801-20260930.
  - Label the paired result strict OOS, final validation or promotion evidence.
changed_paths:
  - docs/agents/tasks/FTAI-20260724-rl-v2-roi-lifecycle-paired-attribution-execution.md
validation:
  - command: live develop and open-PR preflight
    result: PASS
    evidence: Current develop contains diagnosis, declaration, implementation and terminal checkpoint merges; no open PR overlaps RL-v2 paired attribution ownership.
  - command: diagnosis-to-variant traceability inspection
    result: PASS
    evidence: Baseline artifact digest, committed metrics, variant strategy hash and sole lifecycle delta are all versioned and repository-bound.
blockers: []
next_action: Merge this declaration-only task record, then implement guarded paired-attribution execution infrastructure in a separate PR without adding a run request or executing training, backtest or market-data access.
```
