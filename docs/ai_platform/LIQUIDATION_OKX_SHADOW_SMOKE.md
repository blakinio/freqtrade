# OKX Liquidation Shadow Smoke v1

## Purpose

This package freezes a short public transport smoke for the isolated `okx-usdt-swap` source. It verifies current
public endpoint access, subscription acknowledgement, instrument metadata, clock probes, parser compatibility and
artifact integrity without adding OKX to `liquid20-v1`.

Passing this smoke does not establish representative activity, 24-hour reliability or performance suitability.

## Frozen request

The trigger request must declare exactly:

```text
source: okx-usdt-swap
symbols: BTCUSDT, ETHUSDT
duration: 120 seconds
host: github-hosted-ubuntu-24.04
execution_enabled: false
performance_research_authorized: false
orders_submitted: 0
```

Endpoints are frozen in
`ai_platform/research/liquidations/okx-liquidation-shadow-smoke-policy-v1.json`.

## Prospective gates

The policy is merged before the operational trigger. It requires:

- the exact source, ordered symbols, duration and public endpoints;
- a 40-character collector commit and new output directory;
- no recognized exchange or Freqtrade trading credentials;
- execution disabled, zero orders and no performance authorization;
- synchronized OKX clock probes at the start and end;
- exactly two valid live linear USDT-settled instrument contracts;
- at least one WebSocket message, one control message and one connection;
- at least 110 seconds of measured collection and 90% connection availability;
- zero parser failures, no more than one disconnect and at most 1% duplicates;
- valid event semantics whenever events occur;
- exact SHA-256, byte size and line-count agreement for every artifact.

The event and observed-symbol minimums are both zero. A quiet two-minute market must not be relabelled as a transport
failure. The separate long-run acceptance package must set activity thresholds before it runs.

## Trigger lifecycle

The infrastructure workflow is inert until a pull request adds exactly:

`ai_platform/research/liquidations/run-requests/okx-shadow-smoke-20260726-v1.json`

The trigger pull request:

1. changes exactly that one file;
2. runs against `develop` with read-only repository permissions;
3. uses public endpoints and no credentials;
4. uploads bounded success or failure evidence for 30 days;
5. closes without merge after terminal evidence is captured.

A failed smoke remains failed evidence. A rerun requires a new prospectively declared request and run identity.

## Evidence package

The artifact directory contains:

- `okx-usdt-swap.ndjson`;
- `okx-usdt-swap-summary.json`;
- `okx-usdt-swap-instruments.json`;
- `okx-shadow-smoke-manifest.json`;
- `okx-shadow-smoke-report.json`;
- `artifact-sha256.txt`.

The manifest and report are self-hashed. The evaluator reopens the event, summary and instrument files and recomputes
their identities rather than trusting producer metadata.

## Boundary

Even a passing smoke authorizes only transport compatibility evidence. It does not authorize:

- membership in `liquid20-v1` or a future `liquid20-v2`;
- a 24-hour OKX acceptance claim;
- LQ-02 dataset selection or the deferred Tardis H3 path;
- replay, strategy tuning, model training or protected-holdout access;
- dry-run, shadow execution, orders, DCA, leverage or live capital.

The next package after a passing smoke is a separate prospective OKX long-run acceptance policy and execution task.
