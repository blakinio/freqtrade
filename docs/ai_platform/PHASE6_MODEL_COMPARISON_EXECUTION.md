# Phase 6 Historical Model Comparison Execution Workflow v1

This work package adds execution infrastructure for the frozen Phase 6 `LightGBMRegressor` versus `XGBoostRegressor` historical comparison. It does not itself authorize or trigger the historical run.

The infrastructure pull request and the execution trigger must remain separate. The workflow is installed first. Only after that workflow has passed review, CI, and merge may a second pull request add the canonical run-request file that starts the one-shot historical comparison.

## Trigger boundary

The workflow listens only for an `opened` pull request that touches:

`ai_platform/model_comparison/run-requests/lightgbm-vs-xgboost-v1.json`

Before any market-data access, the workflow requires all of the following:

1. the pull request comes from the same repository and targets `develop`;
2. the pull request diff adds exactly the canonical run-request file and no other path;
3. `ai_platform.scripts.model_comparison_run_request` accepts the request as an exact match for the canonical payload derived from the current frozen Phase 6 contract;
4. the Phase 6 comparison contract validates successfully;
5. materialization reproduces the declared historical windows, their Freqtrade execution timeranges, frozen model set, protected-final-holdout boundary, and no-promotion/no-profitability flags.

The canonical request can be printed with:

```bash
python -m ai_platform.scripts.model_comparison_run_request --print-canonical
```

The infrastructure pull request must not add that generated request file.

## Frozen execution boundary

The research semantics remain pinned to the existing Phase 6 contract:

- training window: `20251201-20260228`;
- tuning window: `20260301-20260430`;
- strict historical scoring window: `20260501-20260630`;
- semantic prediction window: `20260301-20260630`;
- semantic market-data download window: `20250801-20260630`;
- candidates: `LightGBMRegressor` and `XGBoostRegressor` only;
- `entry_prediction_threshold = 0.006`;
- `exit_prediction_threshold = -0.009`.

Freqtrade date timeranges use the stop date as the execution boundary at midnight. To include the complete semantic end date of June 30 without changing the research window, the materialized execution inputs therefore use:

- backtest/prediction execution timerange: `20260301-20260701`;
- market-data download execution timerange: `20250801-20260701`.

The strict OOS extractor still scores only fully contained trades with open time on or after `2026-05-01T00:00:00Z` and close time strictly before `2026-07-01T00:00:00Z`. The extra execution boundary does not extend historical scoring into July.

The protected final holdout remains `20260801-20260930` and is outside every semantic and execution range in this workflow.

## Execution chain

After the trigger and frozen-input gates pass, the workflow:

1. checks out the exact trigger pull-request head SHA;
2. materializes the frozen semantic windows together with the explicit exclusive-stop Freqtrade execution timeranges;
3. installs the pinned FreqAI dependency profile;
4. restores only the Phase 6 `v2` historical cache namespace or downloads Kraken history through the exclusive `20260701` boundary, thereby covering the complete June 30 session;
5. runs the frozen LightGBM and XGBoost backtests from the same checked-out commit through the exclusive `20260701` execution boundary;
6. locates each canonical backtest archive;
7. performs strict historical-OOS extraction for both models, restricted to the consumed `20260501-20260630` semantic scoring window;
8. recomputes the deterministic predeclared model-selection decision from those two extractions;
9. binds materialization, runtime provenance, exact backtest archives, exact extraction artifacts, and the exact selection decision through the Phase 6 provenance binder;
10. assembles the final comparison result only from successfully bound evidence;
11. uploads the evidence chain as a GitHub Actions artifact.

A failure in either model run or any later extraction, selection, provenance, or assembly gate prevents successful evidence publication. Failure diagnostics are uploaded separately when available.

## Evidence handling

Successful workflow artifacts include the assembled evidence directory and the materialized comparison tree. The workflow artifact is temporary execution evidence, not a durable repository record by itself.

After a real run completes, the result must be reviewed and, when appropriate, persisted through a separate evidence pull request. That later work package must preserve exact artifact hashes and the existing Phase 6 provenance contracts. The run-request trigger pull request must not be treated as model promotion and does not need to be merged merely because its workflow completed.

## Safety boundary

This workflow does not permit:

- access to `20260801-20260930`;
- threshold retuning;
- model-parameter changes;
- feature changes;
- adding a third Phase 6 candidate;
- changing the predeclared selection policy;
- promotion to dry-run or live trading;
- live-capital changes;
- profitability claims.

The canonical request explicitly keeps `final_holdout_used`, `retuning_allowed`, `model_parameter_changes_allowed`, `feature_changes_allowed`, `promotion_allowed`, `live_trading_allowed`, and `profitability_claim_allowed` false.
