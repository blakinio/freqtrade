---
task_id: FTAI-20260728-wickhunter-live-archive-acceptance-bridge
status: in_progress
branch: feat/wickhunter-live-archive-acceptance-v1
base_branch: develop
created: 2026-07-28
updated: 2026-07-28
related_pr: null
depends_on:
  - FTAI-20260727-wickhunter-wh01-dataset-builder
owned_paths:
  - ai_platform/wickhunter/live_archive.py
  - ai_platform/wickhunter/__init__.py
  - tests/ai_platform_integration/test_wickhunter_live_archive_acceptance.py
  - docs/ai_platform/WICKHUNTER_LIVE_ARCHIVE_ACCEPTANCE.md
  - docs/agents/programs/FTAI_WICKHUNTER_LIQUIDATION_BOT_PROGRAM.md
  - docs/agents/tasks/FTAI-20260728-wickhunter-live-archive-acceptance-bridge.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_WICKHUNTER_LIQUIDATION_BOT_PROGRAM.md
  - docs/ai_platform/WICKHUNTER_DATASET_BUILDER.md
  - docs/ai_platform/LIQUID20_TARDIS_LOCAL_IMPORTER.md
  - deploy/synology/liquid20/LIVE_STREAM.md
  - ai_platform/scripts/liquidation_live_stream.py
  - ai_platform/research/liquidations/historical/acceptance.py
  - ai_platform/research/liquidations/historical/manifests.py
---

# WickHunter first-party live archive acceptance bridge

## Goal

Convert an immutable completed Liquid20 live run into the existing provider-neutral accepted historical package consumed by WH-01, preserving first-party receive time and exact source provenance without changing the collector, historical contracts, portal or any execution path.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-28T14:00:00+02:00
validated_code_head: null
branch: feat/wickhunter-live-archive-acceptance-v1
pr: null
status: in_progress
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_WICKHUNTER_LIQUIDATION_BOT_PROGRAM.md
  - docs/ai_platform/WICKHUNTER_DATASET_BUILDER.md
  - docs/ai_platform/LIQUID20_TARDIS_LOCAL_IMPORTER.md
owned_paths:
  - ai_platform/wickhunter/live_archive.py
  - ai_platform/wickhunter/__init__.py
  - tests/ai_platform_integration/test_wickhunter_live_archive_acceptance.py
  - docs/ai_platform/WICKHUNTER_LIVE_ARCHIVE_ACCEPTANCE.md
  - docs/agents/programs/FTAI_WICKHUNTER_LIQUIDATION_BOT_PROGRAM.md
  - docs/agents/tasks/FTAI-20260728-wickhunter-live-archive-acceptance-bridge.md
proven:
  - WH-01 accepts any provider-neutral immutable package with exact manifest, artifact and accepted-event hashes; it is not restricted to Tardis.
  - The historical semantic-era registry already contains first-party Bybit and Binance Liquid20 eras from 2026-07-25.
  - The production Liquid20 collector stores source-separated append-only NDJSON with occurred_at_ms, received_at_ms, exact collector commit, source summaries and daily/restart run closure.
  - Production proof established connected Bybit/Binance subscriptions and real exchange events while execution and trading authorization remain false.
  - Active portal, Bot Management, ASE, market-data smoke and OKX work does not own the declared WickHunter paths.
derived:
  - A completed live run can satisfy the real immutable dataset gate after deterministic conversion and unchanged WH-01 verification.
  - Tardis can remain optional backfill for broader regimes instead of blocking technical replay on newly collected real history.
  - The bridge must reject active, changing, malformed, duplicate, parser-error or protected-holdout input and publish nothing on failure.
unknown:
  - The identity and event counts of the first production closed run selected for operational conversion.
  - Whether the first converted production run alone has enough duration and market-regime diversity for any strategy-quality conclusion.
conflicts: []
first_failure: null
rejected_hypotheses:
  - Treat active live files as immutable historical evidence.
  - Copy live NDJSON directly into WH-01 without manifest, acceptance and artifact identities.
  - Weaken the zero-rejection, duplicate, availability-time or protected-holdout gates.
  - Modify the Liquid20 collector or Synology deployment from this WickHunter-owned package.
  - Claim replay performance, model quality, profitability or live authority from conversion alone.
changed_paths:
  - ai_platform/wickhunter/live_archive.py
  - tests/ai_platform_integration/test_wickhunter_live_archive_acceptance.py
  - docs/ai_platform/WICKHUNTER_LIVE_ARCHIVE_ACCEPTANCE.md
validation:
  - command: python syntax compilation
    result: PASS
    evidence: New module and focused test were syntax-compiled before repository upload.
  - command: AI Platform CI
    result: NOT_RUN
    evidence: Required on exact PR head.
  - command: Freqtrade CI
    result: NOT_RUN
    evidence: Required on exact PR head.
  - command: GitHub Actions Security Analysis with zizmor
    result: NOT_RUN
    evidence: Required on exact PR head.
blockers:
  - No production closed run has yet been converted; this implementation package must merge before a separate read-only operational conversion.
next_action: Complete exact-head CI and review for this bridge, merge it, then convert one eligible closed production Liquid20 run read-only into a new immutable accepted root and verify it with load_accepted_import before opening WH-02.
```
