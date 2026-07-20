# Model Comparison Contracts

This directory defines reviewable Phase 6 model-comparison inputs and outputs. It does not execute
model training, Hyperopt, backtesting, or final-holdout validation.

## First comparison

The first planned comparison is pinned in `lightgbm-vs-xgboost-v1.json`:

- `LightGBMRegressor` versus `XGBoostRegressor`;
- `freqai_model` is the only primary variable under test;
- strategy, feature set, target, training window, tuning window, historical OOS inputs, pairs,
  timeframes, fee, and risk assumptions are shared;
- model parameters must be fixed before execution and become part of each model's experiment
  identity; joint model-parameter tuning is not part of this comparison slice;
- feature changes are forbidden during the comparison.

The contract is intentionally `contract_only`. A later, separate work package may implement the
reproducible harness and execute only historical comparisons covered by this contract.

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

The next smallest work package is a model-comparison harness that:

1. materializes two experiment identities from this contract;
2. varies only `freqai_model` plus predeclared model-specific identity parameters;
3. executes the same historical windows for both models;
4. emits `result-schema-v1.json` output;
5. refuses any protected final-holdout overlap;
6. does not run `20260801-20260930` and does not make a profitability or promotion claim.
