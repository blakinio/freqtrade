# WickHunter LightGBM advisory scorer

## Purpose

WH-04 trains one deterministic candidate-level LightGBM binary scorer on immutable WH-01 features and exact WH-02 after-cost labels. It consumes the WH-03 evaluation interface and remains advisory-only.

```text
WH-01 decision-time features
  + deterministic WH-03 candidates
  + exact WH-02 matching-side net return labels
  -> deterministic LightGBM candidate scorer
  -> calibrated confidence and expected return after costs
  -> explicit no-trade threshold
  -> WH-03-compatible comparison report
```

## Frozen feature schema

The feature schema is `wickhunter-lightgbm-candidate-features-v1`. It contains only values available at or before the decision timestamp:

- liquidation count, notional, side imbalance, maximum-event, percentile, z-score and burst metrics;
- ingest latency, source coverage and source count;
- decision price, quote volume, trend, volatility, VWAP/VWMA distances and wick ratio;
- candidate side and deterministic hypothesis encodings.

Feature names containing labels, outcomes, returns, future/exit data, MFE, MAE, fees, slippage or time-to-outcome are rejected. Cases with future-available metrics or a protected holdout split fail closed.

## Deterministic training

The training policy fixes:

- training, calibration and validation split names;
- all LightGBM seeds;
- `deterministic=true`;
- `force_col_wise=true`;
- `num_threads=1`;
- tree and learning-rate bounds;
- calibration bins;
- the no-trade confidence threshold.

Input cases and candidate examples are canonically sorted. Both positive and negative after-cost outcomes are required. Repeating training on the same immutable evidence and policy must reproduce the model text, model hash and complete registry artifact.

## Calibration and no-trade behavior

Raw binary probabilities are calibrated on a dedicated calibration split using fixed probability bins, Laplace smoothing and monotonic adjustment. The calibrated confidence is mapped to expected return using the mean positive and negative WH-02 net-return labels from the training split.

A candidate below `no_trade_confidence` is converted to an explicit `IGNORE` decision with reason `model_confidence_below_threshold`. It never receives a selected replay result. A candidate above threshold remains directional and receives the exact matching WH-02 result through the WH-03 `build_evaluation_decision` interface.

## Shared comparison interface

Validation comparison uses WH-03 without redefining costs or summaries:

- deterministic baseline report from `evaluate_deterministic_baselines`;
- model decisions from `build_evaluation_decision`;
- overall and sliced summaries from `summarize_evaluation`.

The model and baseline must share dataset, market, split geometry, price path, replay policy, parameter and after-cost identities.

## Registry and safety boundary

The immutable registry record contains the model text/hash, feature schema hash, training policy hash, input case hashes, calibration curve, class counts and after-cost return means. Its state is always `candidate` and `advisory_only=true`.

Every artifact and report records:

```text
protected_holdout_accessed = false
automatic_promotion_enabled = false
model_promoted = false
profitability_claimed = false
execution_enabled = false
live_capital_authorized = false
orders_submitted = 0
```

WH-04 contains no credentials, order adapter, automatic promotion or live-capital authority.
