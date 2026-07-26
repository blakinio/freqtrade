---
task_id: FTAI-20260726-liquid20-h3-paid-backfill-deferred
status: blocked
branch: docs/liquid20-h3-purchase-deferred
base_branch: develop
created: 2026-07-26
updated: 2026-07-26
related_pr: pending
owned_paths:
  - docs/agents/tasks/FTAI-20260726-liquid20-h3-paid-backfill-deferred.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260726-liquid20-h2-tardis-importer.md
  - docs/ai_platform/LIQUID20_HISTORICAL_AI_TRAINING_ARCHITECTURE.md
  - docs/ai_platform/LIQUID20_HISTORICAL_CONTRACTS.md
  - docs/ai_platform/LIQUID20_TARDIS_LOCAL_IMPORTER.md
search_first:
  - current develop HEAD and open Liquid20 historical ownership
optional_reads: []
---

# Liquid20 H3 paid backfill deferred

## Owner decision

The owner decided on 2026-07-26 to postpone purchasing historical liquidation data and the associated Tardis licence. No purchase, subscription, one-off order, provider credential provisioning or paid backfill is authorized at this time.

This is an intentional pause, not a technical failure.

## Completed work

The following work is complete and merged:

1. Historical provider preflight and dataset selection.
2. CoinAPI authenticated trial and rejection as a replacement for event-level Tardis history.
3. H1 provider-neutral historical contracts, including:
   - deterministic event and manifest identities;
   - provider occurrence and availability provenance;
   - semantic-era registry;
   - duplicate, holdout-overlap, latency and semantic mismatch rejection;
   - Draft 2020-12 schemas and tests.
4. H2 local-only Tardis normalized liquidation CSV importer, including:
   - Bybit and Binance Futures support;
   - immutable input size and SHA-256 verification;
   - preservation of exchange and provider-local timestamps;
   - side mapping to the liquidated position;
   - malformed-row and semantic-era rejection accounting;
   - deterministic event ordering and JSON artifacts;
   - atomic publication and no-overwrite behavior.
5. Public free-sample validation for four datasets:
   - Bybit BTCUSDT;
   - Bybit ETHUSDT;
   - Binance Futures BTCUSDT;
   - Binance Futures ETHUSDT.
6. Public sample result: 5,585 records accepted and 0 parser rejections.
7. Exact-head AI Platform CI, Freqtrade CI including CI Gate, pre-commit, Mypy, Ruff, documentation build and zizmor passed.

Key merged references:

- H1 implementation: PR #360.
- H1 checkpoint closure: PR #365.
- H2 implementation: PR #370, merge commit `dc3df608362e75ee30f4e50b4ffb3cc5ceeb05bf`.
- H2 checkpoint closure: PR #378, merge commit `b807029a308127e68079d684cfa634cc7068fa87`.

## Current boundary

Do not perform any of the following while this checkpoint is blocked:

- purchase Tardis or another historical provider;
- accept a licence or commercial quote on behalf of the owner;
- provision a provider API key;
- place provider credentials in chat, repository files, workflow logs or general GitHub secrets;
- download the paid full-history dataset;
- mutate the Synology historical-data area;
- generate production features from paid history;
- train, backtest, promote or execute a liquidation model based on the deferred dataset;
- access or modify the protected final holdout.

Work not requiring paid history may continue only if it remains isolated from H3 and does not pretend that full historical evidence exists.

## Proposed paid scope when resumed

The currently preferred request is a one-off Tardis purchase rather than an annual subscription:

- provider: Tardis normalized downloadable liquidation CSV;
- exchanges: Binance USDT Futures and Bybit derivatives;
- symbols: BTCUSDT and ETHUSDT;
- data type: liquidation events only;
- start: `2025-02-26T00:00:00Z` inclusive;
- end: `2026-07-25T00:00:00Z` exclusive;
- expected daily files: 2,056;
- intended use: internal research and model development without raw-data redistribution.

The commercial quote, licence, retention rights, VAT treatment and Bybit semantic coverage must be confirmed before purchase.

## Resume conditions

H3 may resume only after the owner explicitly approves all of the following:

1. provider and purchase model;
2. final price and licence terms;
3. exact historical date range;
4. credential provisioning through the approved restricted path, currently Oteryn-only;
5. storage location and execution window for the paid backfill.

After approval, the next technical sequence is:

1. create the H3 execution task from current `develop`;
2. provision the key without exposing it;
3. download the exact daily file inventory;
4. verify size, SHA-256, completeness and date coverage;
5. run the existing H2 importer into a new immutable output directory;
6. reject duplicates, gaps, timestamp anomalies, semantic mismatches and holdout overlap;
7. publish the acceptance report;
8. proceed to feature generation and training only after acceptance passes.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-26T16:40:00Z
head: pending
branch: docs/liquid20-h3-purchase-deferred
pr: pending
status: blocked
blocker: owner intentionally deferred historical data purchase and licence
context_routes:
  - docs/agents/tasks/FTAI-20260726-liquid20-h2-tardis-importer.md
  - docs/ai_platform/LIQUID20_TARDIS_LOCAL_IMPORTER.md
  - docs/ai_platform/LIQUID20_HISTORICAL_CONTRACTS.md
proven:
  - H1 provider-neutral historical contracts are merged and validated.
  - H2 local Tardis importer is merged and validated.
  - Four frozen public samples produced 5,585 accepted events and zero parser rejections.
  - Paid historical data is not required for the completed H1 and H2 work.
derived:
  - The repository is technically ready to begin H3 after owner authorization and credential provisioning.
unknown:
  - Final provider price and licence terms.
  - Final purchased historical coverage.
  - Date when the owner will resume the purchase decision.
conflicts: []
first_failure: null
rejected_hypotheses:
  - Start a paid backfill without explicit owner approval.
  - Treat CoinAPI aggregate history as an event-level Tardis replacement.
  - Continue to feature generation or training without an accepted full-history dataset.
changed_paths:
  - docs/agents/tasks/FTAI-20260726-liquid20-h3-paid-backfill-deferred.md
validation:
  - command: documentation-only repository CI
    result: PENDING
    evidence: Run on the exact PR head before merge.
blockers:
  - Owner intentionally postponed the provider purchase and licence.
next_action: Wait. Resume only after the owner explicitly authorizes the historical data purchase and H3 execution.
```
