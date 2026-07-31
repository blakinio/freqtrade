# FTAI-20260731-wickhunter-market-evidence-intersection-v3

## Status

`implementing`

## Goal

Produce a new immutable WickHunter Market Evidence package from the exact common, already observed geometry of the verified v1 Binance/Bybit package and the verified v2 OKX supplement, without mutating either source package, inventing observations, backfilling, or accessing the protected holdout.

## Frozen source identities

- base package run: `wickhunter-production-market-evidence-20260730-v1-r1`;
- OKX supplement run: `wickhunter-production-market-evidence-20260801-v2-r1`;
- protected holdout begins: `1785542400000` (`2026-08-01T00:00:00Z`).

## Derived common geometry

The implementation must calculate `max(start)` / `min(end)` from verified manifests rather than trusting these values blindly. The expected result is:

- pre-roll start: `1785398400000` (`2026-07-30T08:00:00Z`);
- decision start: `1785484800000` (`2026-07-31T08:00:00Z`);
- decision end: `1785520800000` (`2026-07-31T18:00:00Z`);
- 24-hour pre-roll;
- 120 decision samples at 5-minute cadence;
- no timestamp at or after the protected holdout.

## Owned paths

- `ai_platform/wickhunter/production_market_evidence_intersection.py`;
- `tests/ai_platform_integration/test_wickhunter_production_market_evidence_intersection.py`;
- this task record.

## Required behavior

1. Independently verify both immutable source packages using their canonical verifiers.
2. Reject equal geometry, non-overlapping geometry, pre-roll shorter than 24 hours, fewer than 120 decision samples, holdout overlap, source identity mismatch, unsafe authority flags, symlinks, missing artifacts, duplicate rows and incomplete 5-minute candle coverage.
3. Filter source health, market quality, instrument history and completed candles only to the common observed geometry.
4. Publish a new no-overwrite immutable package with source manifest/request hashes, a self-hashed binding, a self-hashed lineage record, artifact hashes, checksum index and an independent verifier.
5. Preserve all execution, replay, model, performance-research, credential and live-capital authorities as false and `orders_submitted=0`.
6. Keep WH-01 blocked only on the separate accepted Liquid20/split binding step.

## Acceptance

- focused tests cover successful derivation, geometry rejection and tamper rejection;
- Ruff check and format pass;
- full exact-head CI and security analysis pass;
- implementation merges normally to `develop` before any trusted-runner derivation request;
- real derivation must use a short bounded runner job and must not overwrite or mutate either input package.
