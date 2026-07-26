# RL-v2 Action Observability Execution Declaration

## Purpose

The completed seed-validity diagnosis left the lifecycle seed-robustness result `inconclusive`. Immutable trade artifacts associated the two invalid seeds with very long completed positions, but they retained no inference-time action or prediction-gate timeline. The action-level mechanism therefore remains unknown.

This prospective declaration freezes one fresh historical-development experiment before any wiring, data access, training or backtest. It does not reinterpret or rerun any prior seed and cannot change the frozen seed-robustness decision.

## Fresh evidence window

The instrumented study uses:

- download range `20250601-20251101`, end-exclusive;
- execution range `20250901-20251101`, end-exclusive;
- semantic evidence range `20250901-20251031`;
- 90 training days and 61 backtest days.

This range predates the previously executed March-April 2026 development window. Its training and evidence periods do not touch consumed historical OOS `20260501-20260630` or protected final holdout `20260801-20260930`. No previous RL-v2 execution used the selected September-October 2025 evidence window. Cache restore is forbidden so coverage must be freshly verified.

## Frozen execution panel

Exactly four new seeds are declared:

- `271828182`;
- `628318530`;
- `1414213562`;
- `1618033988`.

No prior seed may be rerun, replaced or removed. A new seed cannot be replaced after its outcome is known.

All other runtime inputs remain frozen:

- Kraken spot;
- `BTC/USDT` and `ETH/USDT`;
- `15m`, `1h` and `4h` data;
- fee `0.002`;
- PPO with `MlpPolicy`;
- data split `random_state=42`, `shuffle=false`;
- model `DesiredPositionReinforcementLearner`, SHA-256 `3cec25cc7b43e3214a8e22d153107307a7a7bfbfd48b6bf313ecb4624cb79d46`;
- lifecycle-aligned parent strategy SHA-256 `366785129798d1332ce593f919c54aa23eefb2b15b2d850ab32d5c5cbdf0d5b7`;
- base config SHA-256 `5adc805deadcfe6dc3c52d0745f62546952a96b38b3bd06bc28ac9987063f6de`.

Each seed must use an isolated identifier derived only from the frozen template.

## Project-specific wiring

A later implementation must add a new strategy subclass named `AiDesiredPositionRLLifecycleAlignedObservableResearchStrategy`. The parent lifecycle-aligned strategy and upstream Freqtrade core remain immutable.

The subclass may only:

1. invoke inherited exit-signal evaluation unchanged;
2. after `super().populate_exit_trend(...)`, pass the resulting inference dataframe to the merged `RLV2ActionObservabilityRecorder`;
3. capture each pair exactly once;
4. atomically write the frozen timeline, manifest and summary to an explicit workflow-owned directory.

The recorder must remain disabled unless `RL_V2_ACTION_OBSERVABILITY_ENABLED` is explicitly set by the authorized workflow. Runtime provenance must be supplied through explicit workflow environment variables. Missing, duplicate or malformed telemetry fails closed.

The instrumentation may not change actions, prediction gating, dataframe values, entry or exit signals, ROI handling, stop-loss handling, rewards, features, model state, orders or trade lifecycle.

## Required evidence

Each seed must retain together:

- the canonical action timeline, manifest and summary;
- the immutable raw backtest archive;
- the effective runtime configuration;
- verified data coverage;
- logs and exact runtime hashes;
- deterministic per-seed action-versus-trade reconciliation.

A deterministic aggregate must combine exactly the four declared seed artifacts. It may report action fractions, accepted action streaks, prediction-gate counts, trade-duration-conditioned action counts and completed-trade metrics.

Position state must be derived post-hoc from immutable completed-trade intervals. The declared assumption is `open_date <= candle_timestamp < close_date`; terminal force-open cases must be reported separately. The required transition labels are `hold_flat`, `enter_long`, `hold_long` and `exit_long`.

## Interpretation boundary

The primary question is whether long-held positions on the fresh window coincide with:

- repeated accepted `target_long` actions;
- absence of accepted `target_flat` actions;
- or raw `target_flat` actions suppressed by `do_predict` gating.

The output is descriptive mechanism evidence only. It cannot claim causality for the old invalid seeds, strict OOS validity, final validation, statistical proof, profitability, superiority, ranking, promotion, dry-run or live readiness. No automatic supported/not-supported decision is authorized.

## Authorization sequence

This declaration authorizes no implementation or execution. The sequence is:

1. merge this three-file declaration;
2. create and validate a separate bounded implementation/infrastructure task;
3. merge inert wiring, request validation, workflow and evidence tooling with no canonical request present;
4. create a separate exact-one-file canonical request PR;
5. execute exactly the four frozen seeds;
6. retain immutable evidence and close the trigger PR without merge;
7. record a separate evidence-only interpretation.

Phase 6 remains complete with authoritative `selected_model=null`.
