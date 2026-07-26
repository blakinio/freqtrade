# RL-v2 Action Observability Execution Infrastructure

## Result

The prospective fresh-window declaration is implemented as request-gated infrastructure. The canonical request remains absent, so the workflow is inert on `develop` and infrastructure validation performs no market-data, model, training, backtest or cache operation.

## Observable strategy

`AiDesiredPositionRLLifecycleAlignedObservableResearchStrategy` inherits the lifecycle-aligned research strategy without changing its model, reward, features, ROI behavior, stop-loss behavior or signal predicates.

Its exit hook:

1. executes `super().populate_exit_trend(...)`;
2. returns immediately when `RL_V2_ACTION_OBSERVABILITY_ENABLED` is not `1`;
3. captures the resulting inference dataframe once per pair;
4. writes the merged deterministic timeline, manifest and summary through `RLV2ActionObservabilityRecorder`.

Duplicate pair capture, missing pair metadata, missing provenance or malformed inference rows fail closed. The recorder does not mutate the dataframe or any strategy-visible signal.

## Frozen execution contract

The immutable contract binds:

- fresh download range `20250601-20251101`;
- execution range `20250901-20251101`;
- exactly seeds `271828182`, `628318530`, `1414213562` and `1618033988`;
- Kraken spot, BTC/USDT and ETH/USDT, 15m/1h/4h and fee `0.002`;
- PPO/MlpPolicy, unchanged data split and unchanged lifecycle-aligned parent;
- no cache restore;
- exact request-only workflow trigger;
- descriptive action-versus-trade evidence with no automatic decision.

The request validator binds the contract, declaration, base configuration, model, parent strategy, observable strategy, recorder, validator, evidence extractor and workflow by SHA-256. Runtime configuration materialization changes only the declared observable strategy, isolated identifier, 90/61-day geometry and one frozen seed.

## Workflow

The workflow can start only when a PR opened against `develop` adds exactly:

`ai_platform/experimental_model_research/run-requests/rl-v2-action-observability-execution-v1.json`

The request must exactly equal the canonical payload. A separate execution task checkpoint must exist before any data access.

After validation, the workflow is frozen to:

- two fresh pair-download jobs with no cache restore;
- exact coverage verification through exclusive `2025-11-01`;
- four and only four seed backtests;
- explicit telemetry environment variables;
- one immutable artifact per seed;
- one exact-four-seed descriptive aggregate.

The trigger request PR must be closed without merge after evidence collection.

## Evidence

Each seed retains:

- raw backtest archive and effective runtime configuration;
- exact data coverage;
- action timeline, manifest and summary;
- position/action reconciliation;
- provenance and logs.

Position state is derived from completed trade intervals using:

`open_timestamp <= candle_timestamp < close_timestamp`

Rejected predictions preserve the raw desired action but produce `hold_flat` or `hold_long`. Accepted actions produce the declared transition classes `enter_long`, `exit_long`, `hold_flat` and `hold_long`.

The evidence extractor reports action and prediction-gate counts, accepted-action streaks, long-position action breakdown, duration-conditioned long rows and descriptive completed-trade metrics. The aggregate combines exactly the four new seeds and deliberately emits `decision: null`.

## Isolation

The infrastructure does not:

- add the canonical request;
- access any historical data or cache;
- execute training or backtesting;
- rerun or replace a prior seed;
- modify upstream Freqtrade core, the parent strategy, PPO, reward or features;
- touch consumed OOS `20260501-20260630`;
- touch protected holdout `20260801-20260930`;
- rank, promote, dry-run or deploy a model.

The evidence remains `fresh_historical_development_action_observability`, with `strict_oos=false`, `protected_final_validation=false`, profitability non-gating and Phase 6 `selected_model=null`.
