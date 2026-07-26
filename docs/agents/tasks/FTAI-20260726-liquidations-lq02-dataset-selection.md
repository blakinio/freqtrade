---
task_id: FTAI-20260726-liquidations-lq02-dataset-selection
status: blocked
branch: docs/liquid20-candle-evidence-publication
base_branch: develop
created: 2026-07-26
updated: 2026-07-26
related_pr: pending
owned_paths:
  - ai_platform/research/liquidations/datasets/
  - ai_platform/scripts/liquidation_dataset_selector.py
  - tests/ai_platform_integration/test_liquidation_dataset_selection.py
  - docs/ai_platform/liquidations/datasets/
  - docs/agents/tasks/FTAI-20260726-liquidations-lq02-dataset-selection.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/LIQUIDATION_REVERSAL_RESEARCH.md
  - docs/ai_platform/LIQUIDATION_MULTI_SOURCE.md
  - docs/ai_platform/portal/LIQUIDATIONS_AI_BOT_IMPLEMENTATION_BLUEPRINT.md
  - docs/ai_platform/portal/liquidations-ai-bot-artifact-contracts-v1.json
  - docs/agents/tasks/FTAI-20260726-liquidations-lq02-candle-evidence-publication.md
search_first:
  - current develop and open ownership on LQ-02 paths
  - completed Liquid20 reports with explicit passed true
  - exact source, summary, manifest and report hashes
  - published candle evidence envelope and artifact retention
optional_reads: []
---

# LQ-02 Liquid20 dataset selection

## Goal

Determine whether immutable Liquid20 run evidence and source-separated candles permit a `DatasetSelectionManifest`. Replay, strategy tuning, AI training, execution, DCA, leverage and live capital remain out of scope.

## Current contract decision

No `DatasetSelectionManifest` is emitted. The candle evidence gap is resolved for the diagnostic interval by:

- `docs/ai_platform/liquidations/datasets/liquid20-candle-diagnostic-20260724-v1.manifest.json`;
- `docs/ai_platform/liquidations/datasets/liquid20-candle-diagnostic-20260724-v1.sha256`;
- `docs/ai_platform/liquidations/datasets/liquid20-candle-diagnostic-20260724-v1.evidence.json`.

The package binds 40 source-symbol files, 576 records each, continuous 5-minute coverage, exact pair mapping and SHA-256 identities. It remains `diagnostic_only` and explicitly sets `performance_research_authorized: false`.

The selection entry gate still fails because completed run `liquid20-20260724T170830Z-1` has `passed: false` and failed `binance-usdm.maximum_latency_over_threshold_ratio`. Exact completed-run source NDJSON, summaries, multi-source manifest and final-report hashes are also not published to the selector. Complete candles cannot upgrade failed liquidation acceptance.

## Stop condition

Do not start replay while any required performance interval lacks a final `passed: true` report, immutable run-file hashes, or durable candle availability. The GitHub raw candle artifact expires on `2026-10-24T14:17:16Z`; only its exact manifest, checksum index and evidence envelope are repository-durable today.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-26T14:30:00Z
head: PENDING
branch: docs/liquid20-candle-evidence-publication
pr: NOT_OPEN
status: blocked
context_routes:
  - docs/agents/tasks/FTAI-20260726-liquidations-lq02-candle-evidence-publication.md
  - docs/ai_platform/portal/LIQUIDATIONS_AI_BOT_IMPLEMENTATION_BLUEPRINT.md
  - docs/ai_platform/portal/liquidations-ai-bot-artifact-contracts-v1.json
  - docs/ai_platform/LIQUIDATION_MULTI_SOURCE.md
owned_paths:
  - ai_platform/research/liquidations/datasets/
  - ai_platform/scripts/liquidation_dataset_selector.py
  - tests/ai_platform_integration/test_liquidation_dataset_selection.py
  - docs/ai_platform/liquidations/datasets/
  - docs/agents/tasks/FTAI-20260726-liquidations-lq02-dataset-selection.md
proven:
  - Completed run liquid20-20260724T170830Z-1 has passed false and failed binance-usdm.maximum_latency_over_threshold_ratio.
  - Trigger PR 375 closed without merge after Synology workflow run 30205769267 produced verified source-separated candles.
  - Workflow artifact 8633031826 has digest d3d25327c1b8f70a89638f26d95aae495b27b96a684add830581f2755e146cfd.
  - The published candle manifest binds 40 files, 576 records each, 23040 records total and continuous 5-minute coverage.
  - Bybit and Binance are preserved separately with no missing-candle zero fill or cross-exchange deduplication.
  - The candle interval does not overlap the protected 2026-08-01 through 2026-10-01 holdout.
  - Performance research remains explicitly unauthorized.
derived:
  - Versioned candle identity is resolved for diagnostic use.
  - Failed run acceptance and unpublished immutable run hashes independently block dataset selection.
  - Replay, strategy and model work remain illegal next steps.
unknown:
  - Whether any newer completed Liquid20 run has a final passed true report.
  - Exact source NDJSON, summary, multi-source manifest and final-report hashes for a performance-selectable run.
  - Durable raw candle availability after 2026-10-24.
conflicts: []
first_failure:
  marker: no-passed-true-liquid20-run
  evidence: The only bound completed run has passed false; candle completeness does not satisfy the acceptance gate.
rejected_hypotheses:
  - Treat complete candles as a substitute for passed true.
  - Treat the failed interval as strict OOS or performance-selectable.
  - Invent or omit exact run artifact hashes.
  - Start replay, strategy, AI or execution while blocked.
changed_paths:
  - docs/ai_platform/liquidations/datasets/liquid20-candle-diagnostic-20260724-v1.manifest.json
  - docs/ai_platform/liquidations/datasets/liquid20-candle-diagnostic-20260724-v1.sha256
  - docs/ai_platform/liquidations/datasets/liquid20-candle-diagnostic-20260724-v1.evidence.json
  - tests/ai_platform_integration/test_liquidation_candle_evidence_publication.py
  - docs/agents/tasks/FTAI-20260726-liquidations-lq02-candle-evidence-publication.md
  - docs/agents/tasks/FTAI-20260726-liquidations-lq02-candle-artifact.md
  - docs/agents/tasks/FTAI-20260726-liquidations-lq02-dataset-selection.md
validation:
  - command: independent archive, manifest, checksum and 23040-record verification
    result: PASS
    evidence: All 40 files had 576 contiguous records and all 41 checksum entries reproduced.
  - command: repository evidence coherence tests
    result: NOT_RUN
    evidence: Pending exact-head repository CI.
  - command: checkpoint, pre-commit, documentation and zizmor
    result: NOT_RUN
    evidence: Pending pull-request checks.
blockers:
  - No completed performance-selectable Liquid20 run has explicit passed true.
  - Exact completed-run source, summary, multi-source manifest and final-report hashes are not published.
  - Durable raw candle storage after GitHub artifact expiry is not proven.
next_action: Publish exact immutable completed-run source, summary, multi-source manifest and final-report hashes, then re-evaluate only a run whose final report explicitly contains passed true.
```
