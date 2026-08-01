# WickHunter exact replay price path

## Purpose

The accepted WH-01 production dataset is immutable and decision-time safe, but its Market Evidence candles are 5-minute aggregates. The WH-02 trusted-runner preflight inspected all 919 dataset rows and proved that every decision occurs inside an already-open candle. The same package therefore cannot determine the post-decision intrabar price order required for exact entry, TP-before-SL, MFE, MAE or time-to-outcome labels.

This package adds only the missing source-evidence boundary:

```text
official public Binance USD-M daily aggTrades ZIP + CHECKSUM
  -> local immutable source verification
  -> deterministic aggregate-trade normalization
  -> exact WH-01 symbol/decision/horizon coverage
  -> atomic no-overwrite price-path package
```

It does not generate labels, run replay, evaluate a strategy, fit a model or authorize performance research.

## Source boundary

The accepted source is the public Binance Data Collection USD-M futures daily `aggTrades` archive. The official public-data repository documents that:

- futures aggregate-trade files correspond to the public `/fapi/v1/aggTrades` contract;
- every row contains aggregate trade ID, price, quantity, first trade ID, last trade ID, timestamp and buyer-maker state;
- daily files become available after the source day;
- every ZIP is accompanied by a `.CHECKSUM` file.

The operational path for a symbol is:

```text
https://data.binance.vision/data/futures/um/daily/aggTrades/<SYMBOL>/<SYMBOL>-aggTrades-<YYYY-MM-DD>.zip
https://data.binance.vision/data/futures/um/daily/aggTrades/<SYMBOL>/<SYMBOL>-aggTrades-<YYYY-MM-DD>.zip.CHECKSUM
```

The core importer contains no network client. Downloading exact source archives is a separate request-only operation after this implementation is reviewed and merged.

## Request contract

`wickhunter-replay-price-path-request-v1` binds:

- immutable package ID;
- exact WH-01 materialization root identity;
- exact dataset and Market Evidence manifest hashes;
- exact implementation Git SHA;
- one UTC source date;
- requested start/end and label horizon;
- protected-holdout start;
- the exact sorted dataset symbol set;
- one ZIP and matching `.CHECKSUM` path per symbol;
- public-only and all disabled authority fields.

The request is rejected when its interval leaves the UTC source date, reaches the protected holdout, differs from the dataset symbols or enables replay/model/performance/execution/live-capital authority.

## Archive acceptance

For every symbol the importer requires:

- regular confined files with no symlink traversal;
- exact `<SYMBOL>-aggTrades-<DATE>.zip` and matching checksum filename;
- exactly one safe CSV member, including a safe nested member when the basename remains exact;
- no encryption, bounded compressed/uncompressed size and bounded compression ratio;
- ZIP SHA-256 matching the official checksum file;
- exactly seven aggregate-trade columns, with or without a recognized header;
- positive finite price and quantity;
- valid aggregate/raw trade IDs and buyer-maker boolean;
- strict `(timestamp_ms, aggregate_trade_id)` ordering;
- source-day coverage spanning the requested interval.

The accepted normalized rows preserve source archive hash and raw row number. No missing row is synthesized and no archive is rewritten.

## Dataset binding and coverage

The importer independently verifies the WH-01 production materialization and every dataset partition/row hash. It derives the exact unique `(symbol, decision_timestamp_ms)` keys and requires:

- request symbols equal dataset symbols;
- every decision plus label horizon remains before the protected holdout;
- the source interval covers the earliest decision through the latest horizon;
- a first aggregate trade exists at or after every decision;
- at least one aggregate trade exists within every decision horizon;
- the sequence reaches every exact horizon boundary.

`maximum_entry_delay_ms` is factual evidence only. This package does not decide whether the first post-decision aggregate trade, a later trade, spread adjustment or another execution convention becomes the replay entry contract.

## Atomic output

```text
<price-path-root>/
  request.json
  manifest.json
  verification-report.json
  artifact-sha256.txt
  trades/
    <SYMBOL>.jsonl
```

Every trade has a canonical `trade_sha256`. Every partition and source archive/checksum identity is bound in a self-hashed manifest. Publication uses a temporary sibling directory and atomic rename; existing roots are verified but never overwritten.

Independent verification checks request/manifest identity, WH-01 hashes, normalized trade hashes and ordering, exact decision coverage, source file hashes when supplied, complete artifact checksum coverage and all authority fields.

## Safety and remaining gates

The package records:

```text
protected_holdout_accessed = false
immutable_inputs_mutated = false
replay_authorized = false
model_execution_authorized = false
performance_research_authorized = false
execution_enabled = false
live_capital_authorized = false
trading_credentials_present = false
orders_submitted = 0
```

A successful price-path import removes only `BLOCKED_EXACT_REPLAY_PRICE_PATH_ABSENT`. WH-02 still requires a separately reviewed entry convention, TP/SL ordering policy, costs/slippage model, label schema and deterministic replay implementation.

The current compatibility prior also generated zero non-ignore candidates across all 919 real dataset rows. That is retained as factual preflight evidence and must not be hidden by changing parameters inside this source-import package.
