---
task_id: FTAI-20260726-liquidations-lq02-candle-evidence-publication
status: blocked
branch: docs/lq02-h3-deferral-sync-20260726
base_branch: develop
created: 2026-07-26
updated: 2026-07-26
related_pr: pending
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
  - docs/agents/tasks/FTAI-20260726-liquidations-lq02-dataset-selection.md
  - docs/ai_platform/portal/liquidations-ai-bot-artifact-contracts-v1.json
search_first:
  - current develop and open ownership on LQ-02 evidence paths
  - completed Liquid20 reports with explicit passed true
  - exact immutable run-artifact hashes and durable raw candle storage
optional_reads: []
---

# LQ-02 candle evidence publication

## Result

PR `#377` published durable repository identity for the successful source-separated diagnostic candle package without committing the raw NDJSON payload. The candle-publication package is complete, but LQ-02 dataset selection remains blocked. PR `#381` records the owner's explicit decision to postpone Tardis purchase, licence acceptance, credential provisioning and H3 paid backfill; no newer accepted Liquid20 final report or immutable completed-run package has been published.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-26T18:23:00Z
head: 0693c9f7bad2c5f68000c256e11a60603827bd9c
branch: docs/lq02-h3-deferral-sync-20260726
pr: pending
status: blocked
context_routes:
  - docs/agents/tasks/FTAI-20260726-liquidations-lq02-dataset-selection.md
  - docs/agents/tasks/FTAI-20260726-liquid20-h3-paid-backfill-deferred.md
  - docs/agents/tasks/FTAI-20260726-liquidations-lq02-candle-artifact.md
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
  - PR 377 merged by squash as c859f127706f663b4401a3efbee05b1c04ceca7c.
  - Workflow run 30205769267 produced artifact 8633031826 with archive digest d3d25327c1b8f70a89638f26d95aae495b27b96a684add830581f2755e146cfd.
  - Independent verification confirmed 40 source-symbol files, 576 records each, 23040 total records and all 41 checksum entries.
  - Bybit and Binance remain source-separated with continuous 5-minute coverage, no protected-holdout overlap, zero orders and performance_research_authorized false.
  - PR 380 merged the prior live-state refresh as 5d09e00bd270046394a189ae36b8aa2fb9a2474f after exact-head Freqtrade CI and zizmor passed.
  - PR 381 merged as 93f044075f2362c83d77fcdf1fa3cfbab680bdcb and explicitly deferred provider purchase, licence, credentials and H3 paid backfill.
  - Current develop is 0693c9f7bad2c5f68000c256e11a60603827bd9c after Market Data Fabric PR 368, whose declared boundary does not modify Liquid20.
  - No open PR owns the LQ-02 evidence or dataset-selector paths; open PR 339 remains an isolated OKX shadow source outside liquid20-v1.
derived:
  - The versioned candle-identity blocker remains closed only for diagnostic LQ-02 use.
  - Complete candle evidence cannot upgrade the failed repository-bound Liquid20 acceptance report.
  - The owner-deferred H3 path cannot produce a new performance-selectable report until explicitly resumed.
  - Dataset selection, replay, strategy, model and execution work remain unauthorized.
unknown:
  - Whether Synology contains a newer completed Liquid20 run with an explicit passed true final report; no such evidence is repository-published.
  - Exact immutable source, summary, multi-source manifest and final-report hashes for a performance-selectable run.
  - Durable raw candle availability after the GitHub artifact expires on 2026-10-24.
conflicts: []
first_failure:
  marker: no-performance-selectable-liquid20-run
  evidence: The only repository-bound completed run liquid20-20260724T170830Z-1 has passed false and failed binance-usdm.maximum_latency_over_threshold_ratio; no newer accepted run evidence is published.
rejected_hypotheses:
  - Commit the raw NDJSON payload into Git.
  - Treat the expiring workflow artifact as proven permanent raw storage.
  - Treat H2 public sample validation as a Liquid20 passed true final report.
  - Treat a generic continuation instruction as approval to purchase data, accept a licence or provision credentials.
  - Relabel the failed run accepted because candle evidence is complete.
  - Start dataset selection, replay or performance work before all independent entry gates pass.
changed_paths:
  - docs/agents/tasks/FTAI-20260726-liquidations-lq02-candle-evidence-publication.md
validation:
  - command: pytest tests/ai_platform_integration/test_liquidation_candle_evidence_publication.py
    result: PASS
    evidence: AI Platform CI 1616 passed exact manifest, checksum and envelope coherence tests on PR 377.
  - command: live GitHub develop, Liquid20 report and open-path ownership review
    result: PASS
    evidence: Develop is 0693c9f7bad2c5f68000c256e11a60603827bd9c; PR 381 defers H3 and no published passed true report or conflicting LQ-02 ownership was found.
  - command: python tools/agents/checkpoint.py docs/agents/tasks/FTAI-20260726-liquidations-lq02-candle-evidence-publication.md --require-checkpoint
    result: NOT_RUN
    evidence: The sandbox has no repository checkout and outbound DNS prevents cloning; exact-head GitHub CI is required for this refresh.
blockers:
  - No completed performance-selectable Liquid20 run has an explicit passed true final report in published evidence.
  - Exact completed-run source, summary, multi-source manifest and final-report hashes are not published.
  - Durable raw candle storage after GitHub artifact expiry is not proven.
  - The owner explicitly postponed provider purchase, licence acceptance, credential provisioning and H3 execution in PR 381.
next_action: Wait for explicit owner authorization that reverses the H3 deferral and approves provider, price and licence, date range, Oteryn-only credentials, storage and execution window; only then run H3 and continue through dataset selection after a passed true report with exact hashes and durable candles is published.
```
