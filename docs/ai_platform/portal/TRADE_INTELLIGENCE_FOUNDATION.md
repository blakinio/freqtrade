# Trade Intelligence Foundation

## Purpose

P8 separates decision-time evidence from trade outcomes and produces deterministic post-trade diagnosis before any optional AI synthesis.

## Decision black box

`DecisionSnapshot` contains only evidence available at decision time and pins:

- tenant, bot and trade-intent identity;
- risk-decision identity;
- immutable config revision, strategy, model and risk-policy versions;
- source runtime, pair, side and amount;
- immutable evidence object reference and SHA-256 integrity hash.

No realized PNL, exit reason or other post-outcome field is stored in the snapshot.

## Outcome and reconciliation

`TradeOutcome` is stored separately and records normalized realized PNL, fees, exit reason, source runtime and explicit reconciliation status. `PENDING`, `SOURCE_UNAVAILABLE` and `MISMATCH` are never silently treated as synchronized evidence.

## Deterministic diagnosis

Diagnosis runs before optional AI synthesis:

- `PROFITABLE` for synchronized non-negative realized PNL;
- `LOSS_WITHIN_EXPECTED_RISK` for synchronized loss with no evidence of declared risk-budget breach;
- `LOSS_REQUIRES_REVIEW` when the normalized outcome says the risk budget was exceeded;
- `DATA_GAP` when reconciliation is incomplete or inconsistent.

A losing trade is explicitly not classified as a model error by default.

## AI synthesis boundary

An optional `InsightSynthesizer` may append a narrative to deterministic evidence. It cannot change the diagnosis code, reason codes or evidence links. Synthesis exceptions or empty output fall back to deterministic analysis and do not affect execution availability.

## Persistence

Searchable snapshot, outcome and analysis metadata are tenant-scoped in portal PostgreSQL tables. Large evidence remains referenced through immutable object-storage paths and hashes.

## Safety invariants

- analysis imports no execution adapter and cannot submit orders;
- decision-time and outcome-time data are separate;
- tenant attribution is fail-closed;
- mismatched bot/pair/runtime attribution is rejected;
- negative evidence remains durable;
- AI synthesis cannot overwrite deterministic evidence or mutate bot/model configuration.
