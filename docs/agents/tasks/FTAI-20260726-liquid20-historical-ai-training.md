---
task_id: FTAI-20260726-liquid20-historical-ai-training
status: blocked
branch: feat/liquid20-historical-provider-preflight-v1
base_branch: develop
created: 2026-07-26
updated: 2026-07-26
related_pr: "#336"
owned_paths:
  - docs/ai_platform/LIQUID20_HISTORICAL_PROVIDER_PREFLIGHT.md
  - ai_platform/research/liquidations/historical/liquid20-provider-decision-v1.json
  - ai_platform/research/liquidations/historical/provider-decision-v1.schema.json
  - tests/ai_platform_integration/test_liquidation_historical_provider_preflight.py
  - docs/agents/tasks/FTAI-20260726-liquid20-historical-ai-training.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/ARCHITECTURE.md
  - docs/ai_platform/ROADMAP.md
  - docs/ai_platform/LIQUIDATION_REVERSAL_RESEARCH.md
  - docs/ai_platform/LIQUIDATION_DATA_ONLY_STAGING.md
  - docs/ai_platform/LIQUID20_HISTORICAL_AI_TRAINING_ARCHITECTURE.md
  - docs/agents/tasks/FTAI-20260724-liquidation-reversal-foundation.md
  - docs/agents/tasks/FTAI-20260724-liquidation-data-only-staging.md
  - docs/agents/tasks/FTAI-20260725-portal-liquidations-synology.md
search_first:
  - current develop HEAD, open Liquid20 PRs and CI
  - Oteryn-Platform issue 148 and active Liquid20 Synology task
  - current provider documentation, licensing, coverage and timestamp semantics
optional_reads: []
---

# Liquid20 Historical Backfill and AI Training

## Goal

Prepare and then execute a bounded, reproducible path from historical liquidation data to source-aware FreqAI
features and later RL observations without reopening completed Phase 6, changing frozen thresholds, using the
protected final holdout, or authorizing execution.

## Declared result of this planning package

The durable architecture is defined in:

`docs/ai_platform/LIQUID20_HISTORICAL_AI_TRAINING_ARCHITECTURE.md`

The architecture selects:

- Tardis as the first event-level historical-provider preflight candidate;
- CoinGlass only as a separate aggregated-feature fallback or comparison source;
- Bybit and Binance as the first model feature sources;
- OKX as the first later live shadow-source candidate;
- LightGBM feature ablation before XGBoost confirmation, RL, or sequence models;
- atomic 5-minute feature partitions with deterministic derived 15-minute FreqAI features;
- a separate historical acceptance policy and provenance model;
- no relocation or mutation of current Synology live evidence.

## Required bounded work packages

### H0 — Provider and source preflight

Verify current official exchange and provider contracts, inspect free samples where available, and freeze a
coverage, timestamp, semantic-era, license, storage, and cost decision record. No bulk download, purchase,
training, or model execution.

### H1 — Provider-neutral contracts

Implement historical envelopes, manifests, semantic eras, acceptance schemas, deterministic identities,
decimal normalization, provider interface, and synthetic tests. No network access is required.

### H2 — Tardis sample importer

Implement and validate a local-file or free-sample importer, immutable hashes, normalized records, rejection
summaries, and sample acceptance. Provider credentials remain optional and secret-backed.

### H3 — Bulk backfill

After explicit owner confirmation of provider access and license, run an exact-date immutable Synology import
through an exact-SHA image. Preserve raw files, manifests, acceptance, quarantine, and hashes. Do not train in
the same work package.

### H4 — Feature dataset

Build deterministic availability-time joins, source-specific quality masks, atomic 5-minute features, derived
15-minute features, dataset manifests, and no-lookahead evidence.

### H5 — LightGBM ablation

Prospectively freeze and compare baseline, baseline plus Bybit, baseline plus Binance, and baseline plus both
sources. Use separate declaration, inert infrastructure, exact-one-file execution, evidence, and interpretation
PRs.

### H6 — Optional XGBoost and RL

Proceed only after H5 interpretation. XGBoost confirmation and RL observation-only variants are independent
prospective tasks. Existing Phase 6 and RL-v2 evidence remain immutable.

### H7 — OKX shadow source

Add OKX only through an isolated adapter, staging policy, acceptance, feature namespace, and ablation. It must
not be coupled to the initial backfill or model execution.

## Acceptance criteria for the programme

- [x] Current provider coverage and timestamp semantics are independently verified.
- [ ] Paid access and license decisions are explicit owner decisions.
- [ ] Raw history is immutable and SHA-256 bound.
- [x] Historical acceptance is separate from live collector acceptance.
- [x] Bybit and Binance semantic eras remain explicit.
- [x] Event availability uses provider capture time where available.
- [x] Missing intervals are not fabricated as zero-volume observations.
- [ ] Source-specific features and quality masks exist before cross-source features.
- [ ] Atomic 5-minute and derived 15-minute datasets reproduce exactly.
- [ ] No-lookahead and deterministic repeated-generation tests pass.
- [ ] A chronological split contract is merged before model execution.
- [ ] The first model experiment is a LightGBM feature ablation.
- [x] Existing Phase 6, PyTorch, RL-v2, portal, live collector, and protected-holdout boundaries remain unchanged.
- [x] No live-capital or promotion claim is made.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-26T08:10:00Z
head: 12b77e491a741ea1796c7280de9fe63664201a74
branch: feat/liquid20-historical-provider-preflight-v1
pr: "#336"
status: blocked
context_routes:
  - docs/ai_platform/LIQUID20_HISTORICAL_AI_TRAINING_ARCHITECTURE.md
  - docs/ai_platform/LIQUID20_HISTORICAL_PROVIDER_PREFLIGHT.md
  - ai_platform/research/liquidations/historical/liquid20-provider-decision-v1.json
  - ai_platform/research/liquidations/historical/provider-decision-v1.schema.json
owned_paths:
  - docs/ai_platform/LIQUID20_HISTORICAL_PROVIDER_PREFLIGHT.md
  - ai_platform/research/liquidations/historical/liquid20-provider-decision-v1.json
  - ai_platform/research/liquidations/historical/provider-decision-v1.schema.json
  - tests/ai_platform_integration/test_liquidation_historical_provider_preflight.py
  - docs/agents/tasks/FTAI-20260726-liquid20-historical-ai-training.md
proven:
  - Declaration PR 332 merged as 541cedb61ad0fdc9943d4981ee10217e17f903f5 before H0 began.
  - Tardis public metadata lists BTCUSDT and ETHUSDT liquidation coverage for Bybit and Binance futures through 2026-07-26.
  - Four public 2025-03-01 Tardis samples passed gzip, schema, timestamp, side, positive-value, malformed-row and duplicate inspection with exact hashes recorded.
  - Every inspected row contained provider local_timestamp; no row had local_timestamp before exchange timestamp; every liquidation id was empty.
  - Bybit introduced allLiquidation on 2025-02-20, while inspected Tardis mapper commit 3e3f4d704d66d1187037d2e2c48f68b82441e808 switches on 2025-02-26.
  - Binance forceOrder in the requested range is a maximum-one-snapshot-per-symbol-per-1000ms source, not a complete event ledger.
  - Tardis terms permit licensed internal Customer-System retention and prohibit raw redistribution; bulk dates require paid access and an API key.
  - Oteryn issue 148 still reported the unchanged second live acceptance run in progress; this does not block historical H0.
derived:
  - Tardis is adequate as the first event-level provider, with CoinGlass retained only as aggregate comparison or fallback.
  - The first common import window must start at 2025-02-26 unless Tardis resolves the preceding six-day semantic conflict.
  - The exact request contains 2056 daily gzip CSV files and has a sample-scaled estimate of 39835514 compressed and 204142810 uncompressed bytes.
  - Historical provider local_timestamp maps to provider_captured_at_ms and must never populate first-party received_at_ms.
  - H1 remains a separate provider-neutral contract task and PR; H3 paid access remains owner-gated.
unknown:
  - Exact Tardis quote and whether one-off purchase or subscription is preferred.
  - Owner acceptance of Tardis license and raw redistribution restrictions.
  - Owner decision on 2025-02-26 start versus provider clarification for 2025-02-20 through 2025-02-25.
  - Future Tardis API key value and secret provisioning, which are intentionally absent from Git.
  - Final result of the unchanged second 24-hour live Liquid20 acceptance attempt.
conflicts:
  - Bybit official allLiquidation era starts 2025-02-20, but inspected Tardis normalized mapper switches 2025-02-26.
first_failure:
  marker: bybit-allLiquidation-provider-boundary-conflict
  evidence: The requested 2025-02-20 start cannot be accepted without silently mixing six days of provider semantics.
rejected_hypotheses:
  - Use 2025-02-20 without resolving the Tardis mapper boundary.
  - Treat Binance forceOrder as a complete event ledger.
  - Fabricate event IDs, missing events, zero-volume intervals or provider arrival timestamps.
  - Convert CoinGlass aggregate candles into individual events.
  - Commit public or licensed raw data to Git or upload it as normal artifacts.
  - Purchase provider access, request credentials, train models or change live acceptance during H0.
changed_paths:
  - docs/ai_platform/LIQUID20_HISTORICAL_PROVIDER_PREFLIGHT.md
  - ai_platform/research/liquidations/historical/liquid20-provider-decision-v1.json
  - ai_platform/research/liquidations/historical/provider-decision-v1.schema.json
  - tests/ai_platform_integration/test_liquidation_historical_provider_preflight.py
  - docs/agents/tasks/FTAI-20260726-liquid20-historical-ai-training.md
validation:
  - command: GitHub Actions public metadata and free-sample preflight run 30193642455 job 89771204983
    result: PASS
    evidence: Exact metadata and four sample hashes, sizes and aggregate inspections were emitted; no raw artifact was uploaded.
  - command: python -m pytest -q tests/ai_platform_integration/test_liquidation_historical_provider_preflight.py
    result: PASS
    evidence: 7 passed in 0.03s.
  - command: JSON Schema Draft 2020-12 validation
    result: PASS
    evidence: Contract validates against provider-decision-v1.schema.json.
  - command: python -m compileall tests/ai_platform_integration/test_liquidation_historical_provider_preflight.py
    result: PASS
    evidence: Test module compiled successfully.
blockers:
  - Owner must approve Tardis commercial access and exact quote.
  - Owner must accept the license classification and raw redistribution restriction.
  - Owner must choose the 2025-02-26 start or request provider clarification for the excluded six-day interval.
  - Owner must authorize future Oteryn-only API-key provisioning before any H3 bulk access.
next_action: Owner records the Tardis commercial, license, date-boundary and future secret-provisioning decisions before any paid bulk access.
```
