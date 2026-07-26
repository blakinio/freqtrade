---
task_id: FTAI-20260726-liquid20-historical-ai-training
status: planned
branch: docs/liquid20-historical-ai-training-20260726
base_branch: develop
created: 2026-07-26
updated: 2026-07-26
related_pr: TBD
owned_paths:
  - docs/ai_platform/LIQUID20_HISTORICAL_AI_TRAINING_ARCHITECTURE.md
  - docs/ai_platform/LIQUIDATION_REVERSAL_RESEARCH.md
  - docs/ai_platform/ARCHITECTURE.md
  - docs/ai_platform/ROADMAP.md
  - docs/agents/tasks/FTAI-20260726-liquid20-historical-ai-training.md
  - docs/agents/prompts/FTAI-20260726-liquid20-historical-ai-training.md
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

- [ ] Current provider coverage and timestamp semantics are independently verified.
- [ ] Paid access and license decisions are explicit owner decisions.
- [ ] Raw history is immutable and SHA-256 bound.
- [ ] Historical acceptance is separate from live collector acceptance.
- [ ] Bybit and Binance semantic eras remain explicit.
- [ ] Event availability uses provider capture time where available.
- [ ] Missing intervals are not fabricated as zero-volume observations.
- [ ] Source-specific features and quality masks exist before cross-source features.
- [ ] Atomic 5-minute and derived 15-minute datasets reproduce exactly.
- [ ] No-lookahead and deterministic repeated-generation tests pass.
- [ ] A chronological split contract is merged before model execution.
- [ ] The first model experiment is a LightGBM feature ablation.
- [ ] Existing Phase 6, PyTorch, RL-v2, portal, live collector, and protected-holdout boundaries remain unchanged.
- [ ] No live-capital or promotion claim is made.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-26T08:30:00Z
head: 184b3c3bdc5d8706312fd2b63494e7e864967efa
branch: docs/liquid20-historical-ai-training-20260726
pr: none
status: planned
context_routes:
  - docs/ai_platform/ARCHITECTURE.md
  - docs/ai_platform/ROADMAP.md
  - docs/ai_platform/LIQUIDATION_REVERSAL_RESEARCH.md
  - docs/ai_platform/LIQUIDATION_DATA_ONLY_STAGING.md
  - docs/ai_platform/LIQUID20_HISTORICAL_AI_TRAINING_ARCHITECTURE.md
  - docs/agents/tasks/FTAI-20260724-liquidation-data-only-staging.md
  - docs/agents/tasks/FTAI-20260725-portal-liquidations-synology.md
owned_paths:
  - docs/ai_platform/LIQUID20_HISTORICAL_AI_TRAINING_ARCHITECTURE.md
  - docs/ai_platform/LIQUIDATION_REVERSAL_RESEARCH.md
  - docs/ai_platform/ARCHITECTURE.md
  - docs/ai_platform/ROADMAP.md
  - docs/agents/tasks/FTAI-20260726-liquid20-historical-ai-training.md
  - docs/agents/prompts/FTAI-20260726-liquid20-historical-ai-training.md
proven:
  - The current Liquid20 collector uses Bybit linear and Binance USD-M public liquidation sources.
  - The first immutable 24-hour run completed and failed exactly binance-usdm.maximum_latency_over_threshold_ratio.
  - The failed evidence remains immutable and one unchanged retry is running through Oteryn-Platform.
  - Portal read-only Synology integration is completed and independent of collector acceptance.
  - Phase 6 is completed with selected_model = null and cannot be reopened by this track.
  - The protected final holdout is 20260801-20260930 and remains forbidden before its one-shot evaluation.
  - Bybit introduced allLiquidation on 2025-02-20 and deprecated the one-per-second legacy topic.
  - Tardis documents normalized liquidation records with exchange and local capture timestamps for Bybit and Binance futures.
derived:
  - A historical vendor can accelerate research only through separate provenance, acceptance, and semantic-era contracts.
  - The first useful model test is a supervised source-aware feature ablation, not RL training.
  - Five-minute atomic partitions can serve Wick Hunter replay and deterministic 15-minute FreqAI aggregation.
  - Existing live run directories must remain unchanged; historical imports require a sibling storage tree.
unknown:
  - Final result of the unchanged second 24-hour Liquid20 acceptance attempt.
  - Exact observed Binance latency ratio and distribution from the first failed run.
  - Current provider price, license, export quota, incident coverage and exact requested-symbol availability.
  - Owner choice and credentials for any paid historical provider.
  - Exact chronological model split to freeze after accepted coverage is known.
conflicts: []
first_failure:
  marker: none
  evidence: This planning package has not executed importer, data, feature, or model paths.
rejected_hypotheses:
  - Weaken the live Binance latency gate to unblock AI training.
  - Treat failed or incomplete live acceptance evidence as accepted data.
  - Move existing live run directories into a new layout.
  - Convert aggregated vendor candles into fabricated individual events.
  - Sum exchanges into one feature while hiding source semantics.
  - Train RL before a supervised feature-ablation baseline.
  - Purchase provider access or expose credentials from an autonomous documentation task.
changed_paths:
  - docs/ai_platform/LIQUID20_HISTORICAL_AI_TRAINING_ARCHITECTURE.md
  - docs/agents/tasks/FTAI-20260726-liquid20-historical-ai-training.md
validation:
  - command: repository and live-state documentation preflight
    result: PASS
    evidence: Current Freqtrade and Oteryn Liquid20 records, issue 148, completed portal task, Phase 6 boundary, and official/provider documentation were inspected.
blockers: []
next_action: After this declaration PR merges, create feat/liquid20-historical-provider-preflight-v1 and execute H0 only.
```
