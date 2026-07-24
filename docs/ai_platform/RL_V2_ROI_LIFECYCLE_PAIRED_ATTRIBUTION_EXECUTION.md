# RL-v2 ROI Lifecycle Paired Attribution Execution

## Purpose

This package implements guarded infrastructure for one variant-only historical-development attribution
run. It does not execute during infrastructure review and contains no canonical run request.

The future run will execute:

- strategy `AiDesiredPositionRLLifecycleAlignedResearchStrategy`;
- model `DesiredPositionReinforcementLearner`;
- the frozen PPO / `MlpPolicy` configuration;
- the already-known March-April 2026 development geometry.

The immutable baseline model and backtest are not rerun. Baseline metrics are read from the committed
diagnosis bound to artifact `rl-v2-historical-training-execution-218`.

## Evidence classification

Any later output is:

- `paired_historical_development_attribution`;
- `strict_oos=false`;
- `protected_final_validation=false`;
- profitability non-gating.

The window was already used to diagnose and select the lifecycle hypothesis. It cannot become fresh
validation, strict OOS, promotion evidence, or a model-ranking result.

## Canonical request boundary

The workflow remains inert until a later, separate PR adds exactly:

`ai_platform/experimental_model_research/run-requests/rl-v2-roi-lifecycle-paired-attribution-execution-v1.json`

The request is generated and validated by:

`ai_platform.scripts.rl_v2_roi_lifecycle_paired_attribution_run_request`

It binds SHA-256 identities for:

- the execution contract;
- immutable baseline diagnosis;
- lifecycle variant declaration;
- base config;
- FreqAI model;
- lifecycle-aligned strategy;
- request validator;
- evidence extractor;
- workflow.

The trigger workflow checks out the exact PR head and rejects any PR that changes more than the one
canonical request file.

## Frozen variant execution

Temporary runtime materialization changes only:

- `strategy` to `AiDesiredPositionRLLifecycleAlignedResearchStrategy`;
- `freqai.identifier` to `rl-v2-roi-lifecycle-paired-attribution-v1`;
- `freqai.train_period_days` to `90`;
- `freqai.backtest_period_days` to `61`.

All other base configuration remains byte-derived from
`ai_platform/configs/rl_v2_training_research.json`.

The runtime executes exactly one `freqtrade backtesting` command. The workflow contains no baseline
training or baseline backtest command.

## Data boundary

Data are restricted to:

- download timerange `20250801-20260501`, end-exclusive;
- pairs `BTC/USDT`, `ETH/USDT`;
- timeframes `15m`, `1h`, `4h`;
- Kraken spot;
- fee `0.002`.

The workflow may reuse the exact verified baseline pre-OOS cache namespace because the data geometry is
identical. On a cache miss it may download only the declared pre-OOS range after a canonical trigger.
Every pair and the combined dataset are re-verified before execution.

Consumed historical OOS `20260501-20260630` and protected final holdout
`20260801-20260930` remain forbidden.

## Deterministic attribution

The extractor reads the single raw Freqtrade backtest JSON and validates:

- exact lifecycle-aligned strategy;
- isolated FreqAI identifier;
- `ignore_roi_if_entry_signal=true`;
- inherited ROI schedule;
- hard stop-loss;
- long-only spot mode;
- exact execution timerange;
- trade-level accounting.

Primary metrics use the same definitions as the committed baseline diagnosis:

1. ROI exits followed by a same-pair entry exactly 15 minutes later;
2. immediate ROI/stop-loss exit plus same-pair 15-minute re-entry boundaries;
3. close-plus-reopen fees at those boundaries.

The lifecycle hypothesis is directionally supported only if both prospectively frozen criteria pass:

- ROI-to-15-minute re-entry count is below `122`;
- immediate boundary fees are below `52.582123 USDT`.

Net PnL, profit factor, drawdown, trades, target-flat exits, and stop-loss exits are descriptive only.
A negative, neutral, zero-trade, or failed run remains valid evidence.

## Immutable artifact

A successful later trigger uploads a 90-day artifact containing:

- raw backtest ZIP;
- effective runtime config;
- combined data coverage;
- stdout and stderr logs;
- deterministic paired-attribution JSON;
- evidence provenance metadata.

The trigger PR must be closed without merge after the run reaches terminal state.

## Forbidden interpretations

This infrastructure does not authorize:

- baseline rerun;
- consumed-OOS or final-holdout access;
- PPO, reward, feature, threshold, fee, ROI, stop-loss, target-flat, or cooldown tuning;
- strict-OOS or final-validation claims;
- PyTorch/RL ranking;
- promotion, superiority, profitability, dry-run, or live deployment claims.
