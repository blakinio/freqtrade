# Phase 6 Historical Model Comparison Execution v1

This work package provides guarded one-shot execution infrastructure for the frozen Phase 6
`LightGBMRegressor` versus `XGBoostRegressor` historical comparison.

It does **not** include the run-request file and therefore does not execute either model when the
infrastructure PR is opened or merged.

## Trigger boundary

The workflow is `.github/workflows/ai-platform-phase6-historical-comparison.yml` and reacts only when
a new pull request against `develop` is opened with the exact path:

`ai_platform/model_comparison/run-requests/historical-comparison-v1.json`

The trigger PR must change that file and no other file. The workflow checks out the exact pull-request
head commit and compares the base/head file list before dependency installation, cache access, or
market-data access.

There is no `workflow_dispatch` trigger.

The exact request payload is generated from tracked frozen sources with:

```bash
python -m ai_platform.scripts.model_comparison_execution_request --print-template
```

A later trigger-only PR must add the printed JSON unchanged at the reserved request path. The runtime
validator requires exact equality with the generated template, including exact-byte SHA-256 values of
the tracked comparison contract, selection policy, and frozen strategy source.

## Frozen pre-data checks

Before any dependency cache or historical data is touched, the request validator requires:

- comparison id `freqai-lightgbm-vs-xgboost-v1`;
- exactly `LightGBMRegressor` and `XGBoostRegressor`;
- `freqai_model` as the only primary variable under test;
- strategy `AiPhase52ExitStrategy`;
- the strategy source still declares frozen entry `0.006`;
- the strategy `DecimalParameter` runtime default is the selected frozen exit `-0.009`;
- exact SHA-256 of `AiPhase52ExitStrategy.py` is bound into the run request;
- training window `20251201-20260228`;
- tuning window `20260301-20260430`;
- consumed historical OOS scoring window `20260501-20260630`;
- historical download range exactly `20250801-20260630`;
- joint model-parameter tuning forbidden;
- feature changes forbidden;
- protected final holdout exactly `20260801-20260930` and forbidden for model comparison;
- the final-holdout declaration still marks that window unused;
- retuning, promotion, live trading, profitability claims, and unseen-final-evidence claims forbidden.

Any drift fails before market-data access.

## Execution chain

After the request-only and frozen-contract gate passes, the workflow:

1. installs the normal FreqAI runtime;
2. materializes the canonical Phase 6 config/manifest pair for each model;
3. checks the materialized download and scoring windows;
4. restores only the dedicated Phase 6 historical-comparison Kraken cache namespace;
5. on a cache miss, downloads Kraken trades only for the declared historical range ending
   `2026-06-30` and converts them to the required timeframes;
6. runs the LightGBM and XGBoost backtests sequentially from the exact checked-out request commit;
7. requires both run-provenance files to report that same request-head commit;
8. requires both run-provenance files to report the exact strategy SHA-256 bound by the request;
9. applies the strict fully-contained historical-OOS extractor to both backtest archives;
10. evaluates the already-predeclared deterministic selection policy;
11. binds exact-byte materialization, run provenance, archive, extraction, and selection evidence;
12. assembles the completed model-comparison result through the tracked final result schema;
13. verifies final-holdout, promotion, and profitability-claim flags remain false;
14. uploads the request, materialized comparison tree, and completed evidence as a durable artifact.

The workflow does not retune strategy thresholds, model parameters, or features. The selected
Phase 5.2 exit threshold is frozen as the strategy's runtime default, so the strategy file hash recorded
by `run_experiment` cryptographically identifies the threshold-bearing source used by both backtests.

## Data isolation

The dedicated data-cache namespace is not shared with Phase 5 final-holdout workflows. The only
allowed download timerange ends on `20260630`. The protected final holdout `20260801-20260930` is not
part of the request, materialization, download, training, tuning, extraction, selection, provenance,
or result-assembly path.

The `20260501-20260630` scoring window is explicitly consumed historical OOS. A result from this
workflow is historical model-selection evidence and must never be represented as unseen final
evidence.

## Evidence boundary

A successful trigger run uploads:

- the exact canonical run request;
- canonical materialized configs and manifests;
- canonical `materialization.json`;
- per-model run provenance and run summaries;
- per-model backtest archives and logs stored under the materialized run roots;
- strict-OOS extraction JSON for each model;
- deterministic selection-decision JSON;
- bound result-provenance JSON;
- completed model-comparison result JSON.

These artifacts do not authorize model promotion, live trading, or a profitability claim.

## Next work package

After this infrastructure is merged, create a **separate trigger-only PR** containing exactly the
canonical generated request file. Opening that PR is the action that executes the historical
comparison. The resulting workflow artifact must be reviewed and preserved as durable evidence in a
separate evidence work package before any later Phase 6 conclusion is treated as repository state.
