# WickHunter production market evidence capture v1

## Purpose

This package captures the first prospective, immutable market-context evidence that can be joined to production Liquid20 liquidation archives without fabricating historical spread, rolling volume or completed-candle state.

It is intentionally separate from WH-01 materialization. The materialization operator remains no-network and unchanged. This capture package grants no replay, model-training, strategy-research, execution, order or live-capital authority.

## Frozen interval

The v1 request is fixed before any collection begins:

| Boundary | UTC | Epoch milliseconds |
| --- | --- | ---: |
| Candle pre-roll start | 2026-07-30 06:00 | `1785391200000` |
| Decision interval start | 2026-07-31 06:00 | `1785477600000` |
| Decision interval end, exclusive | 2026-07-31 18:00 | `1785520800000` |
| Protected final holdout start | 2026-08-01 00:00 | `1785542400000` |

The 24-hour pre-roll plus 12-hour decision interval yields 432 completed 5-minute candles per source and symbol. The decision interval yields 144 market-quality observations per source-symbol cohort. The package ends six hours before the protected holdout and cannot be retargeted by editing the trigger request.

## Evidence captured

The frozen `liquid20-v1` cohort is used only as reproducible collection identity. It does not become the WickHunter trading universe.

For each 5-minute decision slot the collector stores exact public response bytes and a normalized, source-separated snapshot for:

- Bybit Linear perpetual tickers;
- Binance USD-M 24-hour tickers;
- Binance USD-M best bid and ask;
- last price, bid, ask, spread in basis points and rolling 24-hour quote volume;
- scheduled and actual availability timestamps.

After all 144 decision slots complete, the collector downloads and freezes 5-minute completed candles for each of the 20 symbols from both sources. Candle availability is derived as `close_time_ms_exclusive`; an incomplete or missing candle is never treated as zero.

Every accepted package contains exact raw and normalized file hashes, source and symbol identities, request URLs, row counts, source-separation policy, request identity, collector commit and a self-hashed manifest plus checksum index.

## Runtime lifecycle

The implementation PR contains no run request and performs no public market acquisition.

A separately reviewed exact-one-file trigger PR adds:

```text
ai_platform/wickhunter/run-requests/
  wickhunter-production-market-evidence-20260730-v1.json
```

Opening that PR initializes one durable run on `freqtrade-synology-staging`. The request PR is then closed without merge. A scheduled workflow on `develop` takes at most one due sample every five minutes and uses a self-hashed active pointer, self-hashed state, Linux file lock, atomic writes and no-overwrite run identity.

The terminal package remains on durable Synology storage. GitHub receives bounded metadata evidence only; bulk raw responses and normalized candles are not committed to the repository.

## Fail-closed acceptance

The package is accepted only when all conditions hold:

- exactly 144 market-quality samples pass;
- every sample contains all 20 symbols for both sources;
- all 40 source-symbol candle files contain exactly 432 contiguous rows;
- each market snapshot and completed candle obeys its availability-time rule;
- every referenced file, size and SHA-256 identity independently verifies;
- source labels remain separate and cross-exchange deduplication remains disabled;
- no recognized trading credential or proxy environment is present;
- the request preserves all false authority flags and `orders_submitted = 0`;
- the interval remains strictly before the protected holdout.

A late, interrupted, malformed, redirected, missing-symbol, missing-candle, tampered or duplicate run is rejected. Existing run roots are never overwritten.

## Downstream boundary

An accepted package supplies real completed-candle, spread and rolling-volume evidence. It does not itself create `DynamicUniverseSnapshot` history or a WH-01 dataset.

The next bounded package must combine this immutable evidence with a contemporaneous closed Liquid20 archive, derive source-aware historical universe decisions, freeze split geometry and run the unchanged WH-01 materialization preflight. WH-02 remains blocked until that process creates a non-empty independently verified dataset.
