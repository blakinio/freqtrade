# Phase 6 Final Comparison Result Assembler v1

This work package assembles the existing `result-schema-v1.json` output only from already-produced and already-bound Phase 6 evidence. It does not execute Freqtrade, train a model, run a backtest, download market data, retune thresholds, access the protected final holdout, promote a strategy, or make a profitability claim.

## Inputs

The assembler consumes:

- bound `result-provenance-schema-v1.json` evidence emitted after Provenance Binding Implementation v1 succeeds;
- one strict-OOS extraction JSON for `LightGBMRegressor`;
- one strict-OOS extraction JSON for `XGBoostRegressor`;
- the bound selection-decision JSON.

It does not consume a protected-final-holdout artifact.

## Assembly rules

`ai_platform.scripts.model_comparison_result_assembler` fails closed unless all of the following hold:

1. the result-provenance evidence passes the existing canonical schema and semantic validator;
2. each supplied extraction exact-byte SHA-256 matches the corresponding bound `extraction_sha256`;
3. each extraction model and experiment identity match its bound provenance source;
4. the supplied selection-decision exact-byte SHA-256 matches the bound provenance evidence;
5. the deterministic predeclared selection decision recomputed from the two bound extraction payloads exactly matches the supplied selection-decision payload;
6. `result.git_commit` and `result.plan_sha256` are populated only through the canonical `result_binding_values()` provenance mapping;
7. model metrics are copied only from the two validated strict-OOS extraction payloads;
8. the emitted completed result passes `result-schema-v1.json`.

For each model, `artifact_paths` records only the strict-OOS extraction path actually supplied to the assembler. Runtime backtest and run-provenance paths are not invented or reconstructed by this step; their hashes remain in the bound provenance evidence.

## Usage

```bash
python -m ai_platform.scripts.model_comparison_result_assembler \
  path/to/result-provenance.json \
  --lightgbm-extraction path/to/lightgbm/oos-extraction.json \
  --xgboost-extraction path/to/xgboost/oos-extraction.json \
  --selection-decision path/to/selection-decision.json \
  --output path/to/comparison-result.json
```

A successful result always has `status: completed`. Any validation or binding failure exits without assembling a result.

## Safety boundary

The protected final holdout remains exactly `20260801-20260930` and is not an assembler input. Frozen Phase 5.2 thresholds remain:

- `entry_prediction_threshold = 0.006`;
- `exit_prediction_threshold = -0.009`.

The assembled historical comparison result keeps `final_holdout_used: false`, `promotion_allowed: false`, and `profitability_claim_allowed: false`. A historical model selection is not a promotion or live-trading authorization.
