# TradingView Futures Historical Preflight

## Purpose

This work package proves that the three merged candle-only TradingView research strategies have one common, reproducible futures market-data path before any comparative historical backtest is authorized.

The preflight covers exactly:

- `TVDonchianBreakoutStrategy`;
- `TVSupertrendStrategy`;
- `TVBollingerMeanReversionStrategy`.

The Wick Hunter Multi-VWAP helper remains excluded because VWAP distance is only a gate. A complete Wick Hunter research candidate still requires trustworthy, time-aligned historical liquidation observations.

## Runtime market contract

The target runtime is:

- exchange: `krakenfutures`;
- trading mode: `futures`;
- margin mode: `isolated`;
- stake/settlement currency: `USD`;
- timeframe: `15m`;
- research config: `dry_run: true`.

The repository does not hard-code BTC and ETH futures symbols in the tracked config template. The preflight loads the markets exposed by the installed CCXT runtime and requires exactly one active contract/swap with `quote=USD` and `settle=USD` for each base (`BTC`, `ETH`). The resolved unified symbols are persisted in the workflow evidence and inserted into the materialized runtime config.

This fails closed when a required base is missing or when more than one eligible perpetual matches the declared contract.

## Historical boundary

The frozen preflight geometry is:

```text
semantic research window: 20260301-20260630
Freqtrade execution range: 20260301-20260701
historical download range: 20260201-20260701
Freqtrade stop semantics: end-exclusive
maximum startup candles: 120
minimum warm-up timestamp: 2026-02-27T18:00:00Z
```

The earlier download start supplies the maximum declared strategy warm-up without changing the performance window that a later benchmark may score.

The preflight verifies that both resolved futures pairs have 15m candles beginning no later than the minimum warm-up timestamp and extending through the final expected candle at `2026-06-30T23:45:00Z`.

The previously consumed platform OOS period `20260501-20260630` may be used only as historical research evidence. It is not unseen final evidence and later observed results cannot be used to retune these fixed v1 strategy implementations against the same reported window.

## Cost assumption

A later comparison must use the same declared fee assumption for all three candidates:

```text
fee = 0.002
```

The preflight records the assumption but produces no performance metric and does not rank strategies.

## Protected final holdout

The prospective final holdout remains:

```text
20260801-20260930
```

The preflight contract rejects overlap with this range. The data workflow stops at the exclusive `20260701` boundary, before the protected period begins.

Nothing in this work package authorizes final-holdout access, Phase 5 retuning, Phase 6 modification, promotion, live trading, a profitability claim, or a superiority claim.

## Workflow

`.github/workflows/ai-platform-tradingview-futures-preflight.yml` performs two stages.

### Static contract stage

Before any network or market-data access it:

1. validates the active task checkpoint;
2. validates the tracked machine-readable preflight contract;
3. validates the inert futures dry-run config template;
4. statically validates that all three canonical strategy classes remain `can_short=True`, use `15m`, and do not exceed the frozen startup-candle budget.

### Data-only runtime stage

After the static stage succeeds it:

1. installs the repository runtime;
2. proves all three strategy classes can be loaded through Freqtrade strategy discovery;
3. discovers exact eligible BTC and ETH USD-settled Kraken Futures perpetual symbols;
4. materializes the dry-run futures config using only those discovered symbols;
5. downloads bounded 15m historical futures data through the exclusive `20260701` stop;
6. verifies warm-up and full end-of-window coverage;
7. uploads market identity, materialized config, strategy-loading and data-coverage evidence.

The workflow does not invoke `freqtrade backtesting`, Hyperopt, model training, or any selection/ranking process.

## Follow-up boundary

A successful preflight establishes data-path readiness only. The next separately declared work package may define a one-shot historical benchmark for the three candle-only candidates under identical pairs, timeframe, timerange, fee, startup treatment and execution semantics.

That later benchmark must preserve results as historical research evidence only and must not silently promote a candidate or reuse the protected final holdout.
