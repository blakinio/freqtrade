---
task_id: FTAI-20260729-wickhunter-real-dataset-materialization-preflight-v1
status: blocked
branch: preflight/wickhunter-real-dataset-materialization-v1
base_branch: develop
created: 2026-07-29
updated: 2026-07-29
related_pr: null
depends_on:
  - FTAI-20260727-wickhunter-wh01-dataset-builder
  - FTAI-20260728-wickhunter-production-live-archive-conversion-v1
owned_paths:
  - docs/ai_platform/WICKHUNTER_REAL_DATASET_MATERIALIZATION_PREFLIGHT.md
  - docs/agents/tasks/FTAI-20260729-wickhunter-real-dataset-materialization-preflight-v1.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_WICKHUNTER_LIQUIDATION_BOT_PROGRAM.md
  - docs/agents/tasks/FTAI-20260727-wickhunter-wh01-dataset-builder.md
  - docs/agents/tasks/FTAI-20260728-wickhunter-production-live-archive-conversion-v1.md
  - docs/ai_platform/WICKHUNTER_DATASET_BUILDER.md
  - docs/ai_platform/WICKHUNTER_REAL_DATASET_MATERIALIZATION_PREFLIGHT.md
  - docs/ai_platform/market_data/ARCHITECTURE.md
---

# WickHunter real dataset materialization preflight v1

## Goal

Bind the first real accepted immutable Liquid20 import to the existing WH-01 contract, audit the remaining real decision-time inputs, and decide whether a production feature-dataset materialization can begin without inventing market context, universe history, split geometry or replay authority.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-29T17:59:00+02:00
branch: preflight/wickhunter-real-dataset-materialization-v1
head: b7ac4e9d4de30a90579457438832fab86fe9478d
pr: null
status: blocked
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_WICKHUNTER_LIQUIDATION_BOT_PROGRAM.md
  - docs/agents/tasks/FTAI-20260727-wickhunter-wh01-dataset-builder.md
  - docs/agents/tasks/FTAI-20260728-wickhunter-production-live-archive-conversion-v1.md
  - docs/ai_platform/WICKHUNTER_DATASET_BUILDER.md
  - docs/ai_platform/WICKHUNTER_REAL_DATASET_MATERIALIZATION_PREFLIGHT.md
owned_paths:
  - docs/ai_platform/WICKHUNTER_REAL_DATASET_MATERIALIZATION_PREFLIGHT.md
  - docs/agents/tasks/FTAI-20260729-wickhunter-real-dataset-materialization-preflight-v1.md
proven:
  - Production conversion task completed and its checkpoint merged as 9f805cd19087fffada21ab219c3c6198141710ff.
  - Accepted import first-party-live:liquid20-20260729T000000Z-0:7a1a5fc5c22c4d5d passed the unchanged historical acceptance contract and unchanged WH-01 load_accepted_import verification.
  - The accepted package contains 29253 records, zero rejections and zero duplicates, with input identity 7a1a5fc5c22c4d5df37cb3df09889c156e597a2f0bb08be8fad302efac8a88ea.
  - Existing build_wickhunter_dataset requires accepted import roots, MarketContextSnapshot values, DynamicUniverseSnapshot history and a declared DatasetSplitGeometry.
  - Existing WH-01 integration tests construct market context and universe history as synthetic fixtures.
  - Required market context contains nine exact metrics with explicit decision-time availability semantics.
  - Dynamic universe selection requires immutable instrument identity plus quality, candle-history, feature-history, spread, volume, source-health and risk evidence as of each decision timestamp.
  - Reviewed Market Data Fabric instrument adapters provide catalog snapshots but do not by themselves provide historical completed-candle market context or universe-quality history for the accepted interval.
derived:
  - The accepted immutable import is eligible input to WH-01 but is not a wickhunter-dataset-manifest-v1 feature dataset.
  - A current instrument catalog cannot be silently backdated to the accepted interval.
  - The approximately 12.47-hour accepted interval does not prove temporal or regime diversity.
  - WH-02 remains blocked until a real non-empty WH-01 feature dataset is materialized and independently verified.
unknown:
  - Whether immutable completed-candle, spread, volume and market-quality evidence exists for the accepted interval.
  - Whether immutable as-of instrument and universe-quality snapshots exist for every intended decision timestamp.
  - Which prospective decision cadence, history window, purge, embargo and split geometry can produce a useful non-empty dataset without touching the protected holdout.
conflicts: []
first_failure:
  gate: real_wh01_input_completeness
  cause: No accepted real MarketContextSnapshot stream, DynamicUniverseSnapshot history or production split geometry is currently bound to the accepted import.
  resolution: A separate read-only WH-01 input and dataset materialization operator must be reviewed before any execution.
rejected_hypotheses:
  - Treat successful load_accepted_import as a completed WH-01 dataset build.
  - Use synthetic fixture market or universe snapshots with the production accepted import.
  - Infer canonical venue and market identity from symbol text alone.
  - Use a current catalog as historical as-of evidence.
  - Start labels, replay, model fitting or WH-02 in the preflight package.
changed_paths:
  - docs/ai_platform/WICKHUNTER_REAL_DATASET_MATERIALIZATION_PREFLIGHT.md
  - docs/agents/tasks/FTAI-20260729-wickhunter-real-dataset-materialization-preflight-v1.md
validation:
  - command: Repository contract audit
    result: PASS
    evidence: WH-01 builder and feature contracts were read directly from current develop; all required inputs and fail-closed boundaries are documented.
  - command: Production accepted-import evidence review
    result: PASS
    evidence: Operation metadata and immutable hashes from workflow 30467059746 and artifact 8730084102 bind the exact accepted input.
blockers:
  - Missing accepted real decision-time market-context evidence for the selected interval.
  - Missing accepted real dynamic-universe and as-of instrument-quality history for the selected interval.
  - Missing prospectively frozen production split geometry and non-empty immutable WH-01 output.
next_action: Implement a separately reviewed read-only WH-01 materialization operator that accepts only exact immutable market-context, as-of instrument/universe and split-geometry inputs, fails closed with a bounded missing-input report, and never invokes WH-02 in the same package.
```
