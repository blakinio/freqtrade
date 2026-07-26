---
task_id: FTAI-20260726-liquidations-lq02-candle-evidence-publication
status: ready
branch: develop
base_branch: develop
created: 2026-07-26
updated: 2026-07-26
related_pr: "#377 (merged)"
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

PR `#377` is merged. Repository evidence now binds the successful source-separated diagnostic candle package without committing the raw NDJSON payload. This completes the publication task only; dataset selection and performance research remain gated independently.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-26T16:27:00Z
head: c859f127706f663b4401a3efbee05b1c04ceca7c
branch: develop
pr: "#377 (merged)"
status: ready
context_routes:
  - docs/agents/tasks/FTAI-20260726-liquidations-lq02-dataset-selection.md
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
  - Exact head 53bc000a71181dbc58768aa22e058dde7ddf9571 passed AI Platform CI 1616, Freqtrade CI 1944 and zizmor 1809.
  - Workflow run 30205769267 produced artifact 8633031826 with archive digest d3d25327c1b8f70a89638f26d95aae495b27b96a684add830581f2755e146cfd.
  - Independent verification confirmed 40 source-symbol files, 576 records each, 23040 total records and all 41 checksum entries.
  - Bybit and Binance remain source-separated with continuous 5-minute coverage and no protected-holdout overlap.
  - The evidence records zero orders, no trading credentials and performance_research_authorized false.
derived:
  - The versioned candle-identity blocker is closed for diagnostic LQ-02 use.
  - Complete candle evidence cannot upgrade a failed Liquid20 acceptance report.
  - Replay, strategy, model and execution work remain unauthorized.
unknown:
  - Whether any newer completed Liquid20 run has an explicit passed true final report.
  - Exact immutable source, summary, multi-source manifest and final-report hashes for a performance-selectable run.
  - Durable raw candle availability after the GitHub artifact expires on 2026-10-24.
conflicts: []
first_failure:
  marker: no-performance-selectable-liquid20-run
  evidence: The bound run liquid20-20260724T170830Z-1 has passed false and failed binance-usdm.maximum_latency_over_threshold_ratio.
rejected_hypotheses:
  - Commit the raw NDJSON payload into Git.
  - Treat the expiring workflow artifact as proven permanent raw storage.
  - Relabel the failed run accepted because candle evidence is complete.
  - Start replay or performance work before the independent entry gates pass.
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
    result: PASS
    evidence: AI Platform CI 1616 passed exact manifest, checksum and envelope coherence tests.
  - command: repository pre-commit, documentation, full Python matrix and zizmor
    result: PASS
    evidence: Exact PR head passed Freqtrade CI 1944, AI Platform CI 1616 and zizmor 1809 before merge.
  - command: python tools/agents/checkpoint.py docs/agents/tasks/FTAI-20260726-liquidations-lq02-candle-evidence-publication.md --require-checkpoint
    result: PASS
    evidence: Final compact checkpoint validated after merge metadata was applied.
blockers: []
next_action: Continue only through docs/agents/tasks/FTAI-20260726-liquidations-lq02-dataset-selection.md after a completed Liquid20 final report explicitly has passed true and exact immutable run-file hashes are published.
```
