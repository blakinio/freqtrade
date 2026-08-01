# WickHunter deterministic baseline evaluation

## Purpose

WH-03 evaluates the existing deterministic WickHunter reversal and continuation hypotheses against immutable WH-02 event labels. It creates descriptive, reproducible comparison evidence. It does not train or promote a model, claim profitability, access the protected holdout, or authorize execution.

```text
WH-01 feature row
  + WH-02 long/short labels and frozen costs
  + bounded WickHunter parameters
  -> deterministic reversal and continuation candidates
  -> shared evaluation decisions
  -> overall and sliced descriptive summaries
```

## Frozen shared interface

The interface version is `wickhunter-evaluation-interface-v1` and is owned by `ai_platform/wickhunter/baseline_strategy.py`.

The public contract consists of:

- `EvaluationCase`: one immutable feature row bound to exactly one long and one short WH-02 label;
- `EvaluationDimensions`: split, symbol, side, liquidity, source, regime and hypothesis dimensions;
- `EvaluationDecision`: candidate identity, explicit reason codes, optional advisory score identity and the exact selected WH-02 result;
- `EvaluationRecordFactory`: protocol used by deterministic and later advisory evaluators;
- `build_evaluation_decision`: the only conversion from a candidate into comparable evaluation evidence;
- `summarize_evaluation`: the shared aggregation path for baseline and later model comparison;
- `BaselineEvaluationReport`: immutable report identity, exact replay/cost binding and descriptive summaries.

WH-04 and WH-05 must import this interface rather than create a competing evaluation schema or cost calculation.

## Baseline hypotheses

WH-03 delegates candidate creation to the previously frozen deterministic strategy contract:

- **reversal**: takes the opposite side after a qualifying liquidation imbalance and VWAP/VWMA displacement;
- **continuation**: follows the qualifying trend after the same liquidation and price-location checks.

All thresholds come from a `WickHunterParameters` object validated against explicit `WickHunterParameterBounds`. Hypotheses are unique and sorted before evaluation.

## Duplicate and cooldown behavior

Each hypothesis has independent deterministic memory.

- a previously consumed feature hash is ignored with `duplicate_feature_evidence`;
- a repeated symbol, side and hypothesis within the configured cooldown is ignored with `symbol_side_cooldown_active`;
- all other strategy rejection reasons remain explicit in the candidate and evaluation decision;
- ignored decisions never receive a replay label result.

Input cases are sorted by split, symbol, decision time and immutable row hash before any memory transition. Reordering the caller input therefore cannot change the report.

## Exact WH-02 parity

WH-03 never recomputes event outcomes or costs. A selected candidate copies the matching long or short WH-02 label fields:

- outcome;
- gross and net return;
- maximum favorable and adverse excursion;
- time to outcome.

Every evaluation requires one shared dataset, market, split geometry, price-path and replay-policy identity. Fees, slippage, take-profit, stop-loss and label horizon must be identical across all cases. Take-profit, stop-loss and horizon must also match the bounded baseline parameters. Any mismatch fails closed.

## Slices

The report always contains an overall summary and deterministic slices for:

- split;
- long, short or ignored side;
- symbol;
- low, medium or high quote-volume liquidity;
- ordered liquidation source signature;
- downtrend, range or uptrend regime;
- reversal or continuation hypothesis.

Summaries contain decision, selected, ignored, executed-label and missing-entry counts, outcome counts, return sums and means, excursion means and mean time to outcome. These are descriptive research statistics only.

## Safety boundary

Every decision and report records:

```text
protected_holdout_accessed = false
model_promoted = false
profitability_claimed = false
execution_enabled = false
live_capital_authorized = false
orders_submitted = 0
```

WH-03 does not contain an order adapter, credentials, execution mode, live-capital switch or automatic promotion path. A report conclusion is fixed to `descriptive_only_no_profitability_or_promotion_claim`.
