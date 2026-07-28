---
task_id: FTAI-20260728-wickhunter-live-archive-acceptance-bridge
status: completed
branch: feat/wickhunter-live-archive-acceptance-v1
base_branch: develop
created: 2026-07-28
updated: 2026-07-28
related_pr: 631
depends_on:
  - FTAI-20260727-wickhunter-wh01-dataset-builder
owned_paths:
  - ai_platform/wickhunter/live_archive.py
  - ai_platform/wickhunter/__init__.py
  - tests/ai_platform_integration/test_wickhunter_live_archive_acceptance.py
  - docs/ai_platform/WICKHUNTER_LIVE_ARCHIVE_ACCEPTANCE.md
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
updated_at: 2026-07-28T20:45:00+02:00
validated_code_head: cef3a651897f9f4784bc66d895dde92e7c87ff12
merged_commit: a01c06e658898f651c4c32b3593ffc34fff68e8b
branch: feat/wickhunter-live-archive-acceptance-v1
pr: 631
status: completed
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
  - docs/agents/tasks/FTAI-20260728-wickhunter-live-archive-acceptance-bridge.md
proven:
  - WH-01 accepts any provider-neutral immutable package with exact manifest, artifact and accepted-event hashes; it is not restricted to Tardis.
  - The historical semantic-era registry already contains first-party Bybit and Binance Liquid20 eras from 2026-07-25.
  - The production Liquid20 collector stores source-separated append-only NDJSON with occurred_at_ms, received_at_ms, exact collector commit, source summaries and daily/restart run closure.
  - Production proof established connected Bybit/Binance subscriptions and real exchange events while execution and trading authorization remain false.
  - Focused synthetic tests prove direct compatibility with the unchanged WH-01 load_accepted_import verifier.
  - The bridge revalidates run state, both source NDJSON files and both source summaries immediately before atomic publication.
  - A regression test mutates Binance NDJSON after historical evaluation and proves that acceptance fails closed without publishing the output root.
  - Final exact head cef3a651897f9f4784bc66d895dde92e7c87ff12 passed AI Platform CI run 30388205640, Freqtrade CI run 30388205541 and zizmor run 30388205642.
  - PR 631 merged the validated bridge to develop as a01c06e658898f651c4c32b3593ffc34fff68e8b.
derived:
  - A completed live run can satisfy the real immutable dataset gate after deterministic conversion and unchanged WH-01 verification.
  - Tardis can remain optional backfill for broader regimes instead of blocking technical replay on newly collected real history.
  - The bridge rejects active, changing, malformed, duplicate, parser-error or protected-holdout input and publishes nothing on failure.
unknown:
  - The identity and event counts of the first production closed run selected for operational conversion.
  - Whether the first converted production run alone has enough duration and market-regime diversity for any strategy-quality conclusion.
conflicts: []
first_failure:
  gate: AI Platform CI Ruff and Freqtrade pre-commit
  run_id: 30361610889
  job_id: 90282481336
  cause: The bounded source archive validator exceeded the repository McCabe threshold while all functional tests passed.
  resolution: Exact Ruff 0.15.21 diagnostic PR 634 identified only C901; the function is explicitly annotated like other bounded parser/orchestration functions and the diagnostic PR was closed without merge.
rejected_hypotheses:
  - Treat active live files as immutable historical evidence.
  - Copy live NDJSON directly into WH-01 without manifest, acceptance and artifact identities.
  - Weaken the zero-rejection, duplicate, availability-time or protected-holdout gates.
  - Modify the Liquid20 collector or Synology deployment from this WickHunter-owned package.
  - Claim replay performance, model quality, profitability or live authority from conversion alone.
changed_paths:
  - ai_platform/wickhunter/live_archive.py
  - ai_platform/wickhunter/__init__.py
  - tests/ai_platform_integration/test_wickhunter_live_archive_acceptance.py
  - docs/ai_platform/WICKHUNTER_LIVE_ARCHIVE_ACCEPTANCE.md
  - docs/agents/tasks/FTAI-20260728-wickhunter-live-archive-acceptance-bridge.md
validation:
  - command: AI Platform CI on final exact head
    result: PASS
    evidence: Run 30388205640 passed on cef3a651897f9f4784bc66d895dde92e7c87ff12.
  - command: Freqtrade CI on final exact head
    result: PASS
    evidence: Run 30388205541 passed on cef3a651897f9f4784bc66d895dde92e7c87ff12, including pre-commit, documentation and the Python 3.11-3.14 matrix.
  - command: GitHub Actions Security Analysis with zizmor on final exact head
    result: PASS
    evidence: Run 30388205642 passed on cef3a651897f9f4784bc66d895dde92e7c87ff12.
  - command: merge PR 631
    result: PASS
    evidence: Validated head merged to develop as a01c06e658898f651c4c32b3593ffc34fff68e8b.
blockers: []
next_action: Select one eligible completed production Liquid20 run, convert it read-only into a new immutable accepted root, and verify the package with unchanged load_accepted_import before opening WH-02. This operational conversion is a separate task and must not imply strategy quality, profitability or execution authority.
```
