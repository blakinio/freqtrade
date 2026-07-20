# Model Comparison Contracts

This directory defines reviewable Phase 6 model-comparison inputs and outputs. It does not execute
model training, Hyperopt, backtesting, or final-holdout validation.

## First comparison

The first planned comparison is pinned in `lightgbm-vs-xgboost-v1.json`:

- `LightGBMRegressor` versus `XGBoostRegressor`;
- `freqai_model` is the only primary variable under test;
- strategy, feature set, target, training window, tuning window, historical OOS inputs, pairs,
  timeframes, fee, and risk assumptions are shared;
- model parameters are fixed before execution and are part of each model's experiment identity;
- `LightGBMRegressor` keeps the current baseline parameters `n_estimators=400`,
  `learning_rate=0.03`, `num_leaves=31`, and `n_jobs=-1`;
- `XGBoostRegressor` uses the predeclared shared compatible subset `n_estimators=400`,
  `learning_rate=0.03`, and `n_jobs=-1`; the LightGBM-only `num_leaves` parameter is forbidden;
- joint model-parameter tuning is not part of this comparison slice;
- feature changes are forbidden during the comparison.

The explicit model identities prevent the harness from passing the LightGBM-specific `num_leaves`
setting into `XGBoostRegressor`. The contract validator ties the LightGBM identity to the current
baseline config and derives the allowed XGBoost parameter identity from the predeclared shared
parameter keys.

The comparison contract remains `contract_only`. The materialization harness consumes it to prepare
reviewable inputs, but it does not execute either model.

## Materialize-only harness

`ai_platform.scripts.model_comparison_harness` deterministically materializes:

- one model-specific config for LightGBM;
- one model-specific config for XGBoost;
- one single-training historical prediction manifest per model;
- a `materialization.json` plan recording hashes and explicit `execution_performed: false`.

The temporal geometry is derived from the frozen contract:

- training: `20251201-20260228`;
- tuning prediction coverage: `20260301-20260430`;
- consumed historical OOS scoring window: `20260501-20260630`;
- combined prediction manifest timerange: `20260301-20260630`.

FreqAI backtesting normally uses sliding retraining: after each `backtest_period_days` window, the
training window moves forward and includes previously backtested data. That behavior is not allowed
for this comparison because it would allow later May-June models to train on the consumed historical
OOS itself. The harness therefore derives `train_period_days=90` from the declared Dec-Feb training
window and sets `backtest_period_days=122`, covering the complete Mar-June prediction period in one
backtest window. This keeps a single model trained before tuning and OOS for each model type. OOS
scoring remains explicitly restricted to `20260501-20260630`; the earlier Mar-Apr predictions are
coverage from the same frozen model and are not final evidence.

Both models receive the same temporal geometry, download coverage, pairs, timeframes, fee, strategy,
features, target, and risk assumptions. Generated manifests are validated through the central
`run_experiment.load_manifest` path, so protected-final-holdout overlap fails closed before any later
execution path can consume them.

Materialize inputs without training, downloading market data, backtesting, or comparing models:

```bash
python -m ai_platform.scripts.model_comparison_harness \
  ai_platform/model_comparison/lightgbm-vs-xgboost-v1.json
```

The default output is under `ai_platform/artifacts/model-comparison/materialized/` and is not a
completed comparison result. Materialization does not invoke `freqtrade` or any subprocess.

## OOS trade boundary

`oos-trade-boundary-v1.json` defines the exact trade-level boundary for future model-comparison
scoring. Freqtrade's standard periodic reporting realizes profit by `close_date`, but using only the
close timestamp is too permissive for this model-selection task: a trade opened in April and closed
in May would have been initiated during tuning-period prediction coverage.

The Phase 6 OOS boundary is therefore stricter:

- scoring window: `20260501-20260630`;
- UTC start is inclusive: `2026-05-01T00:00:00Z`;
- UTC end is exclusive: `2026-07-01T00:00:00Z`;
- only closed trades with `open_date >= start_inclusive` and `close_date < end_exclusive` are eligible;
- trades opened before the OOS start are excluded and counted;
- trades closing after the OOS end are excluded and counted;
- `force_exit` trades fully contained in the scoring window are included and counted;
- missing or invalid timestamps fail closed;
- all future metrics must use included trades only and preserve original timestamps as evidence.

This fully-contained-trade rule prevents an entry decision made during the tuning period from
contributing to the consumed historical OOS model-selection score.

Validate the boundary contract without reading a backtest archive or executing research:

```bash
python -m ai_platform.scripts.oos_trade_boundary_contract \
  ai_platform/model_comparison/oos-trade-boundary-v1.json
```

## Metric semantics

`metric-semantics-v1.json` fixes the four Phase 6 comparison metrics before any historical model output
is scored:

- `profit` matches Freqtrade `profit_total`: sum strict-OOS included `profit_abs`, divided by the
  strategy-result `starting_balance`;
- `drawdown` matches Freqtrade `max_drawdown_account`: use
  `freqtrade.data.metrics.calculate_max_drawdown` on strict-OOS included trades ordered by
  `close_date`, with `value_col=profit_abs` and the same positive starting balance, then read
  `relative_account_drawdown`;
- `trades` is exactly the number of strict-OOS included trades;
- `stability` is the normalized profitable-fold concept already used by AI Platform validation:
  split the fixed OOS window into the May and June 2026 UTC calendar folds, realize fold profit by
  `close_date`, mark a fold profitable only when its profit is strictly greater than zero, and compute
  `profitable_folds / 2`.

The stability score is therefore constrained to `0.0`, `0.5`, or `1.0` for this two-month OOS window.
An empty month has zero profit and is not profitable. Empty OOS produces zero-valued metrics but is
explicitly insufficient selection evidence. Both models must use the same starting balance, scoring
window, stability folds, trade boundary, and formulas.

The metric contract keeps the existing result field names `profit`, `drawdown`, `trades`, and
`stability`, but `result-schema-v1.json` now also requires the canonical metric-semantics and OOS
boundary identifiers. Drawdown cannot be negative and stability must remain in `[0, 1]`.

Validate metric semantics without reading model output:

```bash
python -m ai_platform.scripts.model_comparison_metric_semantics \
  ai_platform/model_comparison/metric-semantics-v1.json
```

## Final holdout isolation

The prospectively declared final holdout v2 remains:

`20260801-20260930`

It is forbidden for training, tuning, feature selection, model selection, and model comparison. The
contract validator loads `ai_platform/validation/final-holdout-v2-declaration.json`, requires the
comparison's protected range to match that declaration exactly, and rejects any training, tuning, or
historical OOS selection window that overlaps the protected range.

The existing `20260501-20260630` holdout is explicitly marked `consumed_historical_oos`. It may be
referenced as already-observed historical evidence, but it must not be represented as unseen final
evidence for a new model.

Final holdout v2 remains accessible only through the separately guarded final-validation v2 workflow
after its prospective window is complete. Model-comparison results must always record
`final_holdout_used: false`.

## Validation

Validate the semantic comparison contract without running market research:

```bash
python -m ai_platform.scripts.model_comparison_contract \
  ai_platform/model_comparison/lightgbm-vs-xgboost-v1.json
```

`schema-v1.json` validates comparison plans. `result-schema-v1.json` defines the future
machine-readable output contract and hard-codes `final_holdout_used`, `promotion_allowed`, and
`profitability_claim_allowed` to `false`.

## Next dependency

The next smallest work package is an OOS result extractor that reads an already-produced backtest
archive, applies `oos-trade-boundary-v1.json`, and computes `metric-semantics-v1.json` exactly. It must:

1. validate the source archive and expected strategy/model identity;
2. apply the fully-contained closed-trade rule exactly;
3. emit counts for excluded pre-window opens, excluded post-window closes, and included force exits;
4. preserve original trade timestamps as audit evidence;
5. require the same positive `starting_balance` basis for both models;
6. compute profit, drawdown, trades, and May/June profitable-fold stability exactly as declared;
7. emit metric evidence sufficient to reproduce the stability score;
8. keep `final_holdout_used: false` and refuse any final-holdout overlap;
9. make no promotion or profitability claim.

Actual LightGBM-versus-XGBoost execution remains a later separate work package. The extractor must be
reviewed and merged before historical model outputs are used for selection.
