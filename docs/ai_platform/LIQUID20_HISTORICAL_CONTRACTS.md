# Liquid20 provider-neutral historical contracts

This package implements H1 of the Liquid20 historical programme. It is deliberately independent of any paid provider account and performs no network access.

## Frozen provenance rules

Historical vendor arrival time is represented by `available_at_ms` with `available_at_semantics`. It never populates the first-party live `received_at_ms` field. Original provider timestamps remain in microseconds and millisecond conversion uses deterministic floor division.

Every normalized event carries:

- source and exact symbol;
- liquidated-position side;
- occurrence and availability timestamps;
- decimal-safe price, quantity and exact notional;
- provider, exchange, native channel and semantic era;
- import run, immutable raw-file hash and row number;
- a semantic fingerprint for duplicate detection;
- a deterministic source event ID bound to the immutable file and row.

## Import identity

The manifest identity binds the requested interval, symbols, parser revision, source commit, provider-decision hash, license classification, storage root and raw-file descriptors. The wall-clock creation timestamp is recorded but excluded from the deterministic identity.

The manifest refuses any interval that extends into the protected final holdout beginning `2026-08-01T00:00:00Z`.

## Semantic eras

The registry freezes the currently accepted boundaries:

- Tardis-normalized Bybit `allLiquidation`: from `2025-02-26T00:00:00Z` until the first-party live boundary;
- Tardis Binance `forceOrder` snapshot semantics: from `2021-04-27T00:00:00Z` until the first-party live boundary;
- first-party Liquid20 live sources: from `2026-07-25T00:00:00Z`.

The excluded Bybit interval from 2025-02-20 through 2025-02-25 remains unresolved and is not silently assigned.

## Historical acceptance

Acceptance is separate from the live collector gates. The implementation checks the import run, provider, symbols, requested window, holdout boundary, semantic era, negative availability latency and exact duplicate fingerprints. It emits a deterministic report and accepted-event identity hash.

## Boundaries

This work does not download data, use credentials, modify Synology, build model features, train models, touch the protected holdout, or authorize execution. Provider-specific parsing belongs to H2 adapters behind the provider interface.
