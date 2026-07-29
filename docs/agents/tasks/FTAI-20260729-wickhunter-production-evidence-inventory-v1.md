---
task_id: FTAI-20260729-wickhunter-production-evidence-inventory-v1
status: blocked
branch: preflight/wickhunter-production-evidence-inventory-v1
base_branch: develop
created: 2026-07-29
updated: 2026-07-29
related_pr: null
depends_on:
  - FTAI-20260729-wickhunter-real-dataset-materialization-operator-v1
owned_paths:
  - docs/ai_platform/WICKHUNTER_PRODUCTION_EVIDENCE_INVENTORY.md
  - docs/agents/tasks/FTAI-20260729-wickhunter-production-evidence-inventory-v1.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_WICKHUNTER_LIQUIDATION_BOT_PROGRAM.md
  - docs/agents/tasks/FTAI-20260729-wickhunter-real-dataset-materialization-operator-v1.md
  - docs/ai_platform/WICKHUNTER_DATASET_BUILDER.md
  - docs/ai_platform/WICKHUNTER_DATASET_MATERIALIZATION_OPERATOR.md
  - docs/ai_platform/WICKHUNTER_REAL_DATASET_MATERIALIZATION_PREFLIGHT.md
---

# WickHunter production evidence inventory v1

## Goal

Inventory immutable production evidence that could supply WH-01 market context and historical dynamic-universe rows for the first accepted Liquid20 import, bind only truthful compatible inputs, and stop before operator execution when exact hashes or prospective split geometry are absent.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-29T20:56:00+02:00
head: ded06b946b0e68fab63336aa1026971723364792
branch: preflight/wickhunter-production-evidence-inventory-v1
pr: none
status: blocked
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_WICKHUNTER_LIQUIDATION_BOT_PROGRAM.md
  - docs/agents/tasks/FTAI-20260729-wickhunter-real-dataset-materialization-operator-v1.md
  - docs/ai_platform/WICKHUNTER_DATASET_BUILDER.md
  - docs/ai_platform/WICKHUNTER_DATASET_MATERIALIZATION_OPERATOR.md
  - docs/ai_platform/WICKHUNTER_REAL_DATASET_MATERIALIZATION_PREFLIGHT.md
owned_paths:
  - docs/ai_platform/WICKHUNTER_PRODUCTION_EVIDENCE_INVENTORY.md
  - docs/agents/tasks/FTAI-20260729-wickhunter-production-evidence-inventory-v1.md
proven:
  - Current develop was d7fc27211e5e6391704d5db732fb7f72d267e6e6 when this fresh branch was created.
  - The accepted import at wickhunter-production-live-archive-20260729-v4 contains 29253 accepted records and covers [1785283200052, 1785328080435).
  - Liquid20 production live archives contain liquidation events and source state but no immutable WH-01 completed-candle market-context or historical universe-quality package.
  - The published source-separated 5m candle diagnostic covers 2026-07-24 through 2026-07-26 only, is diagnostic-only and has no proven durable Synology raw archive.
  - Binance Spot instrument acceptance v2 was cancelled after five observations without a terminal outcome; its market type is incompatible with Binance USD-M and Bybit Linear accepted events.
  - No reviewed path was found that supplies exact as-of derivative instrument identity, spread, volume, completed-candle availability, history depth, source health and risk evidence for every intended decision timestamp.
  - The merged materialization request requires exact market-context and universe-history hashes plus prospectively frozen split geometry.
derived:
  - A current catalog or live subscription universe cannot be backdated to the accepted interval.
  - The accepted interval cannot provide its own complete quote_volume_24h_usd context and requires pre-roll evidence.
  - A truthful production materialization request cannot yet be constructed, so invoking the operator with placeholders or guessed geometry would violate the fail-closed boundary.
unknown:
  - Whether unindexed immutable Binance USD-M or Bybit Linear candle and market-quality bytes exist outside the reviewed production paths.
  - Which prospective capture interval, pre-roll, decision cadence and metric lookbacks should be frozen for the first real WH-01 package.
conflicts: []
first_failure:
  marker: REAL_WH01_MARKET_AND_UNIVERSE_EVIDENCE_ABSENT
  evidence: No compatible immutable market-context stream, derivative instrument history, universe-quality history or frozen split geometry exists for the accepted interval.
rejected_hypotheses:
  - Reuse the July 24-26 diagnostic candles for the July 29 accepted interval.
  - Substitute incomplete Binance Spot catalog observations for Binance USD-M and Bybit Linear instrument history.
  - Treat the current Liquid20 dynamic subscription universe as historical WickHunter selection evidence.
  - Invent placeholder hashes, synthetic rows or split geometry solely to invoke preflight.
changed_paths:
  - docs/ai_platform/WICKHUNTER_PRODUCTION_EVIDENCE_INVENTORY.md
  - docs/agents/tasks/FTAI-20260729-wickhunter-production-evidence-inventory-v1.md
validation:
  - command: Repository and durable-path evidence audit
    result: PASS
    evidence: Accepted-import, Liquid20 live archive, published candle diagnostic, Binance instrument acceptance and WH-01 operator contracts were compared directly on current develop.
  - command: Authority and temporal compatibility review
    result: PASS
    evidence: No current-state backfill, synthetic fixture, cross-market substitution, replay, model or trading authority was introduced.
blockers:
  - Missing immutable source-separated Binance USD-M and Bybit Linear candle and market-quality evidence covering the decision interval and required pre-roll.
  - Missing immutable as-of derivative instrument and universe-quality history.
  - Missing prospectively frozen WH-01 decision cadence, lookbacks and split geometry.
next_action: Implement a separately reviewed no-network production evidence-capture package that freezes source-separated Binance USD-M and Bybit Linear completed-candle and market-quality evidence with sufficient pre-roll and exact hashes; only after that package is immutable may a successor derive universe history, freeze split geometry and invoke the unchanged WH-01 operator preflight.
```
