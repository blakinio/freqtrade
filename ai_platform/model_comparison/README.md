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

Validate the semantic contract without running market research:

```bash
python -m ai_platform.scripts.model_comparison_contract \
  ai_platform/model_comparison/lightgbm-vs-xgboost-v1.json
```

`schema-v1.json` validates comparison plans. `result-schema-v1.json` defines the future
machine-readable output contract and hard-codes `final_holdout_used`, `promotion_allowed`, and
`profitability_claim_allowed` to `false`.

## Next dependency

The next separate work package may execute the two materialized single-training prediction manifests,
then calculate model-comparison metrics only from the consumed historical OOS scoring window and
assemble a result conforming to `result-schema-v1.json`. That execution must:

1. use only the already-pinned model identities;
2. keep one frozen Dec-Feb training window per model with no sliding retraining into OOS;
3. perform no joint tuning or feature changes;
4. use the same prediction and scoring windows for both models;
5. keep `final_holdout_used: false`;
6. refuse any overlap with `20260801-20260930` through the central protected-holdout guard;
7. make no promotion or profitability claim;
8. never represent `20260501-20260630` as unseen final evidence.
