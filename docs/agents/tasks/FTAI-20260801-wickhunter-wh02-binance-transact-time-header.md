# FTAI-20260801 — WickHunter WH-02 Binance `transact_time` header

## Status

Completed by the implementation PR.

## Trigger

The trusted WH-02 materialization run parsed the official Binance USD-M daily `aggTrades` archive header as data because the provider uses `transact_time` while the importer canonicalized only `timestamp`.

## Scope

- Canonicalize the official `transact_time` header token to `timestamp`.
- Preserve strict seven-column header recognition and all archive safety checks.
- Add an end-to-end regression test using the official header spelling.
- Do not change request geometry, data rows, authority, execution, or holdout rules.

## Acceptance

- The official Binance header is skipped exactly once as a header.
- Existing canonical-header and headerless inputs remain supported.
- Focused tests and repository CI pass.
- Replay/model/performance/trading/live-capital authority remains false; orders remain zero.
