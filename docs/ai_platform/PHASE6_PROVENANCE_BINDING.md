# Phase 6 Provenance Binding Implementation v1

This work package binds already-produced Phase 6 model-comparison artifacts into one validated provenance evidence object. It does not execute Freqtrade, train a model, run a backtest, download market data, retune thresholds, access the protected final holdout, promote a strategy, or make a profitability claim.

## Inputs

The binder consumes the actual files produced by the already-defined comparison lifecycle:

- canonical `materialization.json`;
- LightGBM `provenance.json`, backtest ZIP, and strict-OOS extraction JSON;
- XGBoost `provenance.json`, backtest ZIP, and strict-OOS extraction JSON;
- selection-decision JSON.

The tracked `selection-policy-v1.json` remains the canonical selection-policy source.

## Binding rules

`ai_platform.scripts.model_comparison_provenance_binding` fails closed unless all of the following hold:

1. the supplied materialization payload equals the canonical Phase 6 plan and its exact bytes hash to the canonical `materialization.json` SHA-256;
2. each model has exactly one artifact set and uses the canonical experiment identity;
3. each run provenance is bound by the SHA-256 of its exact file bytes and its `experiment_id` matches the canonical materialization identity;
4. each supplied backtest archive is bound by the SHA-256 of its exact file bytes;
5. each supplied strict-OOS extraction is bound by the SHA-256 of its exact file bytes, matches the canonical model/experiment identity, and records the SHA-256 of the supplied backtest archive;
6. the supplied selection decision is recomputed from the two bound extraction payloads using the tracked predeclared selection policy and must match that deterministic decision;
7. the selection decision is bound by the SHA-256 of its exact file bytes;
8. the resulting evidence passes the existing result-provenance schema and semantic validator, including shared execution commit, materialized manifest/config hash equality, and shared strategy hash requirements.

The emitted evidence is still provenance evidence only. Final result assembly is a separate dependency.

## Usage

```bash
python -m ai_platform.scripts.model_comparison_provenance_binding \
  path/to/materialization.json \
  --lightgbm-run-provenance path/to/lightgbm/provenance.json \
  --lightgbm-backtest path/to/lightgbm/backtest-result.zip \
  --lightgbm-extraction path/to/lightgbm/oos-extraction.json \
  --xgboost-run-provenance path/to/xgboost/provenance.json \
  --xgboost-backtest path/to/xgboost/backtest-result.zip \
  --xgboost-extraction path/to/xgboost/oos-extraction.json \
  --selection-decision path/to/selection-decision.json \
  --output path/to/result-provenance.json
```

## Safety boundary

The protected final holdout remains exactly `20260801-20260930` and is not an input to this binder. Frozen Phase 5.2 thresholds remain:

- `entry_prediction_threshold = 0.006`;
- `exit_prediction_threshold = -0.009`.

No retuning, promotion, live trading, or profitability claim is authorized by provenance binding.
