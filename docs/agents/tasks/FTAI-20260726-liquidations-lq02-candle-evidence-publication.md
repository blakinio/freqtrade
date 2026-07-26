---
task_id: FTAI-20260726-liquidations-lq02-candle-evidence-publication
status: validating
branch: docs/liquid20-candle-evidence-publication
base_branch: develop
created: 2026-07-26
updated: 2026-07-26
related_pr: "#377"
owned_paths:
  - docs/ai_platform/liquidations/datasets/liquid20-candle-diagnostic-20260724-v1.manifest.json
  - docs/ai_platform/liquidations/datasets/liquid20-candle-diagnostic-20260724-v1.sha256
  - docs/ai_platform/liquidations/datasets/liquid20-candle-diagnostic-20260724-v1.evidence.json
  - tests/ai_platform_integration/test_liquidation_candle_evidence_publication.py
  - docs/agents/tasks/FTAI-20260726-liquidations-lq02-candle-evidence-publication.md
  - docs/agents/tasks/FTAI-20260726-liquidations-lq02-candle-artifact.md
  - docs/agents/tasks/FTAI-20260726-liquidations-lq02-dataset-selection.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260726-liquidations-lq02-candle-artifact.md
  - docs/agents/tasks/FTAI-20260726-liquidations-lq02-dataset-selection.md
  - docs/ai_platform/portal/liquidations-ai-bot-artifact-contracts-v1.json
search_first:
  - current develop and open ownership on LQ-02 evidence paths
  - PR 375 terminal workflow artifact and independent hash verification
  - completed Liquid20 final reports and immutable run-artifact hashes
optional_reads: []
---

# LQ-02 candle evidence publication

## Goal

Publish the exact manifest, checksum index and a self-hashed workflow evidence envelope for the successful source-separated diagnostic candle package. Do not commit the 6.6 MB raw NDJSON files, and do not treat diagnostic candle completeness as acceptance of the failed Liquid20 run.

## Published identity

The bounded Synology workflow run `30205769267` produced artifact `8633031826` with archive digest `d3d25327c1b8f70a89638f26d95aae495b27b96a684add830581f2755e146cfd`. Independent verification confirmed 40 source-symbol files, 576 records each, 23,040 total records, continuous 5-minute coverage and all 41 checksum entries.

The exact manifest and checksum index are copied unchanged into repository evidence. The envelope binds the trigger PR, workflow run, artifact retention, code/request/contract/catalog/universe identities and the explicit no-credential/no-order boundary.

## Decision boundary

This closes the missing candle-identity blocker for diagnostic selection. It does not emit a `DatasetSelectionManifest`, because the target run has `passed: false`, no performance-selectable run has explicit `passed: true`, and exact completed-run source/summaries/manifest/report hashes remain unpublished. The raw workflow artifact expires on `2026-10-24T14:17:16Z`, so durable raw storage remains unproven.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-26T14:40:00Z
head: aefebb4e9b53779d6459cdbbe061f88f910a5078
branch: docs/liquid20-candle-evidence-publication
pr: "#377"
status: validating
context_routes:
  - docs/agents/tasks/FTAI-20260726-liquidations-lq02-candle-artifact.md
  - docs/agents/tasks/FTAI-20260726-liquidations-lq02-dataset-selection.md
  - docs/ai_platform/portal/liquidations-ai-bot-artifact-contracts-v1.json
owned_paths:
  - docs/ai_platform/liquidations/datasets/liquid20-candle-diagnostic-20260724-v1.manifest.json
  - docs/ai_platform/liquidations/datasets/liquid20-candle-diagnostic-20260724-v1.sha256
  - docs/ai_platform/liquidations/datasets/liquid20-candle-diagnostic-20260724-v1.evidence.json
  - tests/ai_platform_integration/test_liquidation_candle_evidence_publication.py
  - docs/agents/tasks/FTAI-20260726-liquidations-lq02-candle-evidence-publication.md
  - docs/agents/tasks/FTAI-20260726-liquidations-lq02-candle-artifact.md
  - docs/agents/tasks/FTAI-20260726-liquidations-lq02-dataset-selection.md
proven:
  - PR 375 closed without merge after dedicated workflow run 30205769267 completed successfully.
  - Workflow artifact 8633031826 has digest d3d25327c1b8f70a89638f26d95aae495b27b96a684add830581f2755e146cfd.
  - Independent verification reproduced the archive digest, manifest file hash, manifest self-hash and all 41 checksum entries.
  - The package contains 40 source-symbol files with 576 records each and 23040 records total.
  - Bybit and Binance source identities remain separate with no cross-exchange deduplication.
  - The interval is complete from 2026-07-24T00:00:00Z through the 2026-07-25T23:55:00Z candle and does not overlap the protected holdout.
  - The manifest records zero orders, no trading credentials and performance_research_authorized false.
derived:
  - Versioned candle identity is no longer the first LQ-02 diagnostic blocker.
  - A failed Liquid20 acceptance report cannot be upgraded by complete candle evidence.
  - Replay and performance research remain unauthorized.
unknown:
  - Final acceptance result of any newer active Liquid20 run.
  - Exact immutable source NDJSON, summary, multi-source manifest and final-report hashes for a passed-true run.
  - Durable raw candle storage after the GitHub artifact expires on 2026-10-24.
conflicts: []
first_failure:
  marker: no-performance-selectable-liquid20-run
  evidence: The bound run liquid20-20260724T170830Z-1 has passed false and failed binance-usdm.maximum_latency_over_threshold_ratio.
rejected_hypotheses:
  - Commit all raw NDJSON files into Git.
  - Treat a 90-day workflow artifact as proven permanent raw storage.
  - Relabel the failed run accepted because candles are complete.
  - Start replay, strategy, model or execution work.
changed_paths:
  - docs/ai_platform/liquidations/datasets/liquid20-candle-diagnostic-20260724-v1.manifest.json
  - docs/ai_platform/liquidations/datasets/liquid20-candle-diagnostic-20260724-v1.sha256
  - docs/ai_platform/liquidations/datasets/liquid20-candle-diagnostic-20260724-v1.evidence.json
  - tests/ai_platform_integration/test_liquidation_candle_evidence_publication.py
  - docs/agents/tasks/FTAI-20260726-liquidations-lq02-candle-evidence-publication.md
  - docs/agents/tasks/FTAI-20260726-liquidations-lq02-candle-artifact.md
  - docs/agents/tasks/FTAI-20260726-liquidations-lq02-dataset-selection.md
validation:
  - command: pytest tests/ai_platform_integration/test_liquidation_candle_evidence_publication.py
    result: NOT_RUN
    evidence: Pending exact-head repository CI.
  - command: python tools/agents/checkpoint.py docs/agents/tasks/FTAI-20260726-liquidations-lq02-candle-evidence-publication.md --require-checkpoint
    result: NOT_RUN
    evidence: Pending exact-head repository CI.
  - command: repository pre-commit, documentation, AI Platform CI and zizmor
    result: NOT_RUN
    evidence: Pending pull-request checks.
blockers:
  - No completed performance-selectable Liquid20 run has explicit passed true.
  - Exact completed-run source, summary, multi-source manifest and final-report hashes are not published to the selector.
  - Durable raw candle storage beyond workflow artifact expiry is not proven.
next_action: Publish exact immutable completed-run source, summary, multi-source manifest and final-report hashes, then re-evaluate only if a final acceptance report explicitly contains passed true.
```
