---
task_id: FTAI-20260726-liquidations-lq02-candle-evidence-publication
status: blocked
branch: docs/lq02-candle-evidence-live-state-20260726
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

PR `#377` is merged. Repository evidence binds the successful source-separated diagnostic candle package without committing the raw NDJSON payload. The publication task is complete, but the routed LQ-02 dataset-selection action remains blocked: newer Liquid20 H2 importer work does not publish an accepted final report, completed-run artifact hashes or durable raw candle storage.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-26T16:34:42Z
head: b807029a308127e68079d684cfa634cc7068fa87
branch: docs/lq02-candle-evidence-live-state-20260726
pr: pending
status: blocked
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
  - Current develop is b807029a308127e68079d684cfa634cc7068fa87 after PR 378 merged the Liquid20 H2 importer checkpoint closure.
  - H2 verifies immutable local input hashes and validated four public samples, but commits or uploads no raw sample files and defers paid bulk backfill to owner-gated H3.
  - No open PR was found owning the LQ-02 evidence, dataset-selector or liquidation dataset paths; open PR 368 explicitly excludes Liquid20 modification.
derived:
  - The versioned candle-identity blocker is closed for diagnostic LQ-02 use.
  - Complete candle evidence cannot upgrade a failed Liquid20 acceptance report.
  - The H2 importer capability does not satisfy the passed-true, completed-run hash or durable-storage entry gates.
  - Replay, strategy, model and execution work remain unauthorized.
unknown:
  - Whether Synology contains any newer completed Liquid20 run with an explicit passed true final report.
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
    evidence: Exact PR 377 head passed Freqtrade CI 1944, AI Platform CI 1616 and zizmor 1809 before merge.
  - command: live GitHub develop, recent Liquid20 PR and open-path ownership review
    result: PASS
    evidence: Develop advanced to b807029a308127e68079d684cfa634cc7068fa87 through PR 378; no published accepted run or conflicting open LQ-02 ownership was found.
  - command: python tools/agents/checkpoint.py docs/agents/tasks/FTAI-20260726-liquidations-lq02-candle-evidence-publication.md --require-checkpoint
    result: NOT_RUN
    evidence: The supplied local checkout path is absent in this sandbox; GitHub CI is authoritative for the documentation branch.
blockers:
  - No completed performance-selectable Liquid20 run has an explicit passed true final report in published evidence.
  - Exact completed-run source, summary, multi-source manifest and final-report hashes are not published.
  - Durable raw candle storage after GitHub artifact expiry is not proven.
  - H3 paid historical backfill remains owner-gated by purchase, license, historical-window and Oteryn credential decisions.
next_action: Do not enter dataset selection; first publish one completed Liquid20 final report with passed true, exact immutable source, summary, multi-source manifest and final-report hashes, and durable candle storage, then continue only through docs/agents/tasks/FTAI-20260726-liquidations-lq02-dataset-selection.md.
```
