---
task_id: FTAI-20260727-wickhunter-wh01-dataset-builder
status: completed
branch: feat/wickhunter-wh01-dataset-builder-v1
base_branch: develop
created: 2026-07-27
updated: 2026-07-28
related_pr: 542
depends_on:
  - FTAI-20260727-wickhunter-wh00-contracts-vertical-slice
owned_paths:
  - ai_platform/wickhunter/dataset.py
  - ai_platform/wickhunter/__init__.py
  - tests/ai_platform_integration/test_wickhunter_dataset_builder.py
  - docs/ai_platform/WICKHUNTER_DATASET_BUILDER.md
  - docs/agents/programs/FTAI_WICKHUNTER_LIQUIDATION_BOT_PROGRAM.md
  - docs/agents/tasks/FTAI-20260727-wickhunter-wh01-dataset-builder.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_WICKHUNTER_LIQUIDATION_BOT_PROGRAM.md
  - docs/agents/tasks/FTAI-20260727-wickhunter-wh00-contracts-vertical-slice.md
  - docs/ai_platform/LIQUID20_HISTORICAL_CONTRACTS.md
  - docs/ai_platform/LIQUID20_TARDIS_LOCAL_IMPORTER.md
  - docs/ai_platform/market_data/ARCHITECTURE.md
---

# WH-01 liquidation dataset builder

## Goal

Select only accepted immutable historical import artifacts and build a deterministic, source-aware WickHunter feature dataset with availability-time joins, dynamic-universe history, explicit purged split geometry, atomic partitions and a self-hashed manifest. This package performs no model fitting, scoring, replay or trading.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-28T00:06:00+02:00
head: 524c55c0cc586b5c520407fceac7f6ace3f110c0
branch: feat/wickhunter-wh01-dataset-builder-v1
pr: 542
status: completed
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_WICKHUNTER_LIQUIDATION_BOT_PROGRAM.md
  - docs/agents/tasks/FTAI-20260727-wickhunter-wh00-contracts-vertical-slice.md
owned_paths:
  - ai_platform/wickhunter/dataset.py
  - ai_platform/wickhunter/__init__.py
  - tests/ai_platform_integration/test_wickhunter_dataset_builder.py
  - docs/ai_platform/WICKHUNTER_DATASET_BUILDER.md
  - docs/agents/programs/FTAI_WICKHUNTER_LIQUIDATION_BOT_PROGRAM.md
  - docs/agents/tasks/FTAI-20260727-wickhunter-wh01-dataset-builder.md
proven:
  - WH-00 is merged and its checkpoint is completed.
  - Existing historical contracts preserve provider, source, occurred-at and availability timestamps and immutable import identities.
  - Existing local importer writes manifest.json, events.jsonl, acceptance.json and artifacts.json with deterministic hashes.
  - Existing accepted Liquid20 evidence remains immutable and separate from the continuous live stream.
  - WH-01 selects only acceptance.status=pass packages with verified manifest, artifact and accepted-event hashes.
  - Historical available_at_ms is preserved as canonical feature-side receive time; future evidence fails closed.
  - Dataset partitions, source selections, universe history and the self-hashed manifest are published atomically without overwrite.
  - Exact Ruff 0.15.21 repair and format completed successfully and all temporary workflow and diagnostic files were removed.
  - Exact code head 524c55c0cc586b5c520407fceac7f6ace3f110c0 passed AI Platform CI, full Freqtrade CI and security analysis.
  - Pre-commit, mypy, Python 3.11 through 3.14, coverage, docs, smoke tests, distribution build and CI Gate passed.
  - Changed-path audit contains exactly the six declared WH-01 paths.
  - All review threads are resolved and outdated; no requested-change review exists.
derived:
  - WH-01 consumes accepted import artifacts without modifying Liquid20, Market Data Fabric, portal, BM, RL-v2 or Synology paths.
  - Dataset construction fails closed on rejected acceptance, hash mismatch, future availability, holdout overlap, duplicate evidence or missing universe eligibility.
  - WH-02 must remain gated until a real accepted immutable bulk import package is selected.
unknown:
  - Exact first accepted bulk Tardis import is still owner/provider-access dependent; the builder accepts any conforming accepted immutable import package and is validated with synthetic fixtures only.
conflicts: []
first_failure:
  gate: AI Platform CI Ruff
  run_id: 30307439318
  job_id: 90114968306
  cause: Ruff check required an exact repair; functional AI-platform tests had already passed.
  resolution: Applied Ruff 0.15.21 check --fix and format, repaired the one exact mypy annotation failure, then removed all temporary workflows and reports.
rejected_hypotheses:
  - Train a model in WH-01.
  - Read raw provider files directly and bypass historical acceptance artifacts.
  - Use occurred_at as availability when a provider availability timestamp exists.
  - Write partial dataset partitions into the final output directory.
  - Start WH-02 with invented, synthetic-only or unaccepted real-history evidence.
changed_paths:
  - ai_platform/wickhunter/dataset.py
  - ai_platform/wickhunter/__init__.py
  - tests/ai_platform_integration/test_wickhunter_dataset_builder.py
  - docs/ai_platform/WICKHUNTER_DATASET_BUILDER.md
  - docs/agents/programs/FTAI_WICKHUNTER_LIQUIDATION_BOT_PROGRAM.md
  - docs/agents/tasks/FTAI-20260727-wickhunter-wh01-dataset-builder.md
validation:
  - command: python -m py_compile ai_platform/wickhunter/dataset.py tests/ai_platform_integration/test_wickhunter_dataset_builder.py
    result: PASS
    evidence: Implementation and focused test module compile in isolation.
  - command: AI Platform CI
    result: PASS
    evidence: exact code head run 30308684986, including compile, AI-platform tests, Ruff, format, codespell and JSON validation.
  - command: Freqtrade CI
    result: PASS
    evidence: exact code head run 30308685006, including pre-commit/mypy, Python 3.11-3.14, coverage, docs, smoke tests, distribution build and CI Gate.
  - command: GitHub Actions Security Analysis with zizmor
    result: PASS
    evidence: exact code head run 30308684933.
  - command: changed paths and review audit
    result: PASS
    evidence: exactly six declared WH-01 files; all five temporary-workflow review threads resolved and outdated; no requested changes.
blockers: []
next_action: Obtain and accept the first real immutable bulk historical import through the existing provider-access process, then open a fresh WH-02 task from current develop. Do not start replay, labels or model work before that evidence exists.
```
