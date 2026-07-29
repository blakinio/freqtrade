# ASE-01 TradingView Strategy Lab

## Purpose

ASE-01 delivers the first research-only strategy laboratory vertical slice:

```text
versioned Strategy DSL declaration
→ closed-bar deterministic feature replay
→ next-bar-open backtest
→ tenant-scoped durable experiment result
→ Portal Experiment API
→ Testy / Laboratorium UI
```

It does not place orders, resolve exchange credentials, expose Freqtrade to the browser, promote a strategy, tune the protected final holdout, or claim profitability.

## Strategy catalog

The catalog contains exactly two clean-room declarations:

- `tv_supertrend_v1@1.0.0`;
- `tv_squeeze_momentum_v1@1.0.0`.

Each declaration records display metadata, source and license provenance, features, entry and exit rules, parameter types and bounds, timeframe semantics, warm-up, confirmation policy, risk defaults and supported directions. The embedded canonical Strategy DSL is validated by the ASE-00 validator. No Pine Script or proprietary indicator source is included and no 1:1 parity is claimed.

The catalog is intentionally extensible for future `tv_macd_mtf_v1` and `tv_support_resistance_breakout_v1` declarations without changing simulator authority boundaries.

## Deterministic replay

The simulator reuses ASE-00 `supertrend_features()` and `squeeze_features()` implementations. It accepts only candles that:

- match the requested pair and timeframe;
- are unique and timestamp ordered;
- are closed and confirmed;
- fall inside the declared timerange.

Signals are evaluated after candle close and filled at the next candle open. Signal and trade identifiers are stable SHA-256 identities. Every signal records the strategy identity, decision, matched conditions, feature values, parameter values and stable reason codes. Future candles do not alter prior non-terminal decisions.

The first slice supports one long position, explicit fees and slippage, deterministic end-of-range liquidation, equity curve, exposure, trades and drawdown. It is a research simulator behind the Strategy DSL boundary, not a second live execution engine.

## Experiment storage and API

Results are stored in the shared Portal SQLAlchemy metadata under `portal_strategy_lab_experiments`. The composite tenant key and tenant-scoped idempotency uniqueness preserve isolation and replay safety. Stored payloads are canonical JSON protected by a result hash; corrupt payloads fail closed.

Endpoints:

```text
GET  /v1/strategy-lab/strategies
POST /v1/strategy-lab/experiments
GET  /v1/strategy-lab/experiments
GET  /v1/strategy-lab/experiments/{id}
GET  /v1/strategy-lab/experiments/{id}/trades
GET  /v1/strategy-lab/experiments/{id}/equity
GET  /v1/strategy-lab/experiments/{id}/signals
GET  /v1/strategy-lab/experiments/compare
```

Creation requires `model.train`, an `Idempotency-Key`, `execution_mode=backtest`, bounded parameters and a timerange outside protected final holdout v2. Reads require `model.read`. Trade and signal responses are paginated; equity and candle counts are bounded. Errors use stable Strategy Lab reason codes. No credential field exists in the request contract.

## Data boundary

The default research dataset is a small deterministic synthetic `BTC/USDT` 15-minute fixture for January 1, 2026. A repository-local JSON data provider can be redirected with `STRATEGY_LAB_DATA_ROOT`. It performs no network access and accepts no exchange credentials. Real historical-data integration remains a separate bounded package.

## Portal UI

`/ai/experiments` becomes the Bot Management `Testy / Laboratorium` surface. It contains:

- strategy, pair, timeframe, timerange, capital and parameter form;
- experiment status and metrics table;
- result metrics and exact parameters;
- equity curve;
- entry and exit signal markers;
- trades and signal rationale tables;
- baseline-versus-variant comparison.

The browser calls a same-origin server action/BFF. It never contacts Freqtrade or an exchange.

## Explicit limitations

- synchronous bounded execution only;
- one pair/timeframe dataset per request;
- long-only, one open position;
- no funding, partial fills, intrabar stop model or portfolio simulation;
- no Optuna or automatic mass generation;
- no MACD MTF or support/resistance strategy yet;
- no real exchange data or live/dry-run promotion;
- protected final holdout v2 remains unavailable.
