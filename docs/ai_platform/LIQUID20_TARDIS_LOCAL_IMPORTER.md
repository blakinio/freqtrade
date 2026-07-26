# Liquid20 Tardis local importer

This document implements H2 without paid access. The importer consumes only immutable files already present under a caller-supplied local input root. It performs no provider authentication, network download or Synology mutation.

## Supported normalized CSV

The adapter accepts the canonical Tardis liquidation header:

```text
exchange,symbol,timestamp,local_timestamp,id,side,price,amount
```

Supported exchange identifiers are `bybit` and `binance-futures`. Tardis `buy` means a short position was liquidated; `sell` means a long position was liquidated. Exchange and provider timestamps are retained in microseconds, while normalized occurrence and availability timestamps use deterministic floor conversion to milliseconds.

## Fail-closed parsing

Before parsing, every file must match its manifest size and SHA-256. The parser rejects unsupported exchanges, encodings, headers, row shapes, symbols, sides, non-positive decimals and unresolved semantic eras. Rejected rows are auditable and contribute to the final historical acceptance ratio; they cannot be hidden by accepting only valid rows.

## Deterministic output

The importer:

- verifies adapter and manifest provider identity;
- resolves all raw paths below the input root;
- parses files in manifest path order;
- emits canonical event order and stable JSON serialization;
- writes `manifest.json`, `events.jsonl`, `rejections.json`, `acceptance.json` and `artifacts.json` into a temporary directory;
- atomically renames the completed directory into place;
- refuses to overwrite an existing output directory.

Failed imports remove their temporary directory. A completed import can still have acceptance status `fail`; this preserves quarantine evidence without promoting it as accepted data.

## Public-sample scope

H2 may validate the parser against the free first day of a month made available by Tardis. Raw sample bytes are temporary validation inputs and are not committed or uploaded as workflow artifacts. Full historical acquisition remains H3 and requires explicit owner approval of cost, license and credentials.
