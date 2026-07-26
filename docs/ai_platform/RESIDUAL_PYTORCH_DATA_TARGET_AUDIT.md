# Residual PyTorch P2 data and target audit

## Decision

P2 freezes the development-only geometry and validates the exact `&-future_return` target semantics without accessing historical market data. The current bounded result is `audit_inconclusive` because the FreqAI-expanded feature matrix and historical label distribution are deliberately unavailable to this package.

This is a contract and leakage preflight. It is not model training, backtesting, historical performance evidence, feature selection or promotion evidence.

## Frozen development geometry

| Boundary | Value |
|---|---|
| Semantic start | `2025-12-01T00:00:00Z` |
| Semantic stop, exclusive | `2026-05-01T00:00:00Z` |
| Freqtrade timerange encoding | `20251201-20260501` |
| Training geometry | `20251201-20260228` |
| Tuning/prediction-only geometry | `20260301-20260430` |
| Consumed historical OOS | `20260501-20260630` — forbidden |
| Protected final holdout | `20260801-20260930` — forbidden |

The development stop is exclusive and exactly precedes the already-consumed historical OOS window. P2 cannot extend into May or June 2026 and cannot access the prospective August–September 2026 holdout.

## Frozen data declaration

- pairs: `BTC/USDT`, `ETH/USDT`;
- base timeframe: `15m`;
- included timeframes: `15m`, `1h`, `4h`;
- indicator periods: `14`, `50`;
- shifted candles: `2`;
- strategy startup candles: `200`;
- chronological split: `shuffle = false`;
- liquidation-derived features: forbidden.

The exact post-expansion FreqAI feature count is intentionally not guessed. It must be measured from an authorized historical feature matrix in a later execution package because correlated-pair, timeframe, shifted-candle and FreqAI expansion behavior determines the actual matrix.

## Exact target semantics

The strategy implementation is:

```python
future_average_close = dataframe["close"].shift(-horizon).rolling(horizon).mean()
dataframe["&-future_return"] = future_average_close / dataframe["close"] - 1
```

For `horizon = 12`, the target at candle `t` is therefore:

```text
mean(close[t+1], ..., close[t+12]) / close[t] - 1
```

The synthetic audit proves:

- only future offsets `t+1` through `t+12` influence the numerator;
- the prior candle does not influence the numerator;
- `t+13` does not influence the target;
- the first `11` rows and final `12` rows are unavailable under the exact Pandas shift-and-rolling geometry;
- the strategy expression matches the explicit future-window formula.

## Deliberately unresolved evidence

The following remain unmeasured and must not be inferred:

- FreqAI-expanded feature count;
- historical feature NaN distribution;
- historical feature outlier distribution;
- historical `&-future_return` distribution;
- pair-level and timeframe-level coverage;
- model quality or trading performance.

A later task may move P2 beyond `audit_inconclusive` only with explicit authorization for a frozen development-only historical matrix. That task must still exclude the consumed historical OOS and protected holdout and must not train or backtest unless separately authorized.

## Validation

Run the dependency-light contract and synthetic semantics audit:

```bash
python -m unittest discover -s tests/ai_platform \
  -p 'test_residual_pytorch_data_target_audit.py'
python -m ai_platform.scripts.residual_pytorch_data_target_audit \
  --output residual-pytorch-data-target-audit.json
```

A successful command produces `outcome = audit_inconclusive`. `audit_supported` is not allowed until every required historical data-quality item is measured from authorized inputs.
