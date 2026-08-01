# WickHunter deterministic replay and event labels

## Purpose

WH-02 converts the verified immutable WH-01 decision rows and the verified exact Binance USD-M aggregate-trade price path into deterministic, independently verifiable event labels. It does not evaluate strategy profitability, fit or promote a model, submit orders, access the protected holdout, or authorize live capital.

```text
verified WH-01 decision row
  + verified exact aggregate-trade sequence
  + frozen replay policy
  -> one deterministic event label
  -> immutable replay package and independent verification
```

## Frozen v1 policy

The policy schema is `wickhunter-deterministic-replay-policy-v1`.

### Decision and entry clock

- Each replay key is the exact `(symbol, decision_timestamp_ms, dataset_row_sha256)` from WH-01.
- The eligible entry clock starts at `decision_timestamp_ms + entry_delay_ms`.
- The entry observation is the first verified aggregate trade whose `(occurred_at_ms, aggregate_trade_id)` is not earlier than that clock.
- Entry is rejected as `missing_entry` when no such trade occurs by `decision_timestamp_ms + maximum_entry_delay_ms` or before the label deadline.
- No candle alignment, interpolation, synthetic tick, backward fill, midpoint, spread guess, or future observation is permitted.

### Executed prices and costs

- Long entry price is `raw_entry_price * (1 + slippage_ratio)`.
- Short entry price is `raw_entry_price * (1 - slippage_ratio)`.
- Long exit price is `raw_exit_price * (1 - slippage_ratio)`.
- Short exit price is `raw_exit_price * (1 + slippage_ratio)`.
- Entry and exit fees are charged independently using `fee_ratio`.
- Net return is calculated from decimal-safe directional executed prices and then reduced by both fee legs. Values are quantized only for serialized evidence, never through binary floating point.

### TP, SL and timeout ordering

- Long TP is `entry_price * (1 + take_profit_ratio)` and long SL is `entry_price * (1 - stop_loss_ratio)`.
- Short TP is `entry_price * (1 - take_profit_ratio)` and short SL is `entry_price * (1 + stop_loss_ratio)`.
- Aggregate trades are processed strictly by `(occurred_at_ms, aggregate_trade_id)`.
- The first observed trade that reaches a barrier determines the outcome. Exact aggregate-trade order therefore resolves same-millisecond TP/SL ordering without candle assumptions.
- The label deadline is `decision_timestamp_ms + label_horizon_ms`. If no barrier is reached, the last trade at or before the deadline is the timeout exit.
- A path that does not reach the exact deadline fails verification instead of silently shortening the label.

### Excursions and duration

- MFE and MAE use the executed entry price and all raw observed prices from entry through the selected exit, inclusive.
- Excursions are directional ratios: favorable values are non-negative MFE; adverse values are non-negative MAE.
- `time_to_outcome_ms` is `exit_timestamp_ms - entry_timestamp_ms` for TP, SL and timeout and is absent for `missing_entry`.

### Split geometry

- Every label binds the WH-01 split name and the exact label interval `[decision_timestamp_ms, decision_timestamp_ms + label_horizon_ms]`.
- Labels may not cross the protected holdout.
- A split manifest must prove that purge and embargo gaps are at least the maximum label horizon between adjacent train, validation and test windows.
- Replay never changes WH-01 split membership and never mixes overlapping label windows across a declared embargo boundary.

## Label schema

`wickhunter-candidate-label-v1` records at least:

- dataset, market-evidence, price-path, policy and code identities;
- dataset row hash, symbol, decision time, split and side;
- raw and executed entry/exit prices and aggregate-trade identities;
- `take_profit`, `stop_loss`, `timeout`, or `missing_entry`;
- gross and net return, MFE, MAE and time to outcome;
- TP/SL ratios, fees, slippage, delay and horizon;
- exact source trade hashes used by entry and exit;
- all safety and authority fields.

The label hash is the canonical hash of the complete label payload. Re-running the same immutable inputs and policy must reproduce the same label and package identities.

## Replay/shadow parity

WH-02 exposes one pure event-ordering function. Replay and the later WH-07 shadow runtime must call that same function with the same side, policy and ordered trade observations. A parity fixture proves identical entry, barrier ordering, outcome, exit, returns, excursions and duration.

## Atomic package

```text
<replay-root>/
  request.json
  policy.json
  manifest.json
  verification-report.json
  artifact-sha256.txt
  labels/
    <split>/<SYMBOL>.jsonl
```

Publication uses a temporary sibling directory and atomic rename. Existing roots are verified but never overwritten. Independent verification re-verifies WH-01 and price-path packages, every row/trade/label hash, ordering, coverage, split geometry, artifact checksums and disabled authority fields.

## Safety boundary

Every request, manifest and report records:

```text
protected_holdout_accessed = false
immutable_inputs_mutated = false
model_execution_authorized = false
performance_research_authorized = false
execution_enabled = false
live_capital_authorized = false
trading_credentials_present = false
orders_submitted = 0
```

WH-02 produces event labels and deterministic replay evidence only. Baseline strategy evaluation begins in WH-03, model work begins in WH-04, and all execution authority remains absent.
