---
task_id: FTAI-20260727-wickhunter-wh01-dataset-builder
status: validating
branch: feat/wickhunter-wh01-dataset-builder-v1
base_branch: develop
created: 2026-07-27
updated: 2026-07-27
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
updated_at: 2026-07-27T23:59:00+02:00
head: 1b2a2647168339b37450c9caf96b81831d703b00
branch: feat/wickhunter-wh01-dataset-builder-v1
pr: 542
status: validating
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
  - Focused AI-platform tests passed before the Ruff-only repair.
  - Exact Ruff 0.15.21 repair and format completed successfully and all temporary workflow files were removed.
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
  resolution: Applied Ruff 0.15.21 check --fix and format to the three Python files, then removed temporary workflows.
rejected_hypotheses:
  - Train a model in WH-01.
  - Read raw provider files directly and bypass historical acceptance artifacts.
  - Use occurred_at as availability when a provider availability timestamp exists.
  - Write partial dataset partitions into the final output directory.
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
    evidence: Draft implementation and focused test module compile in isolation.
  - command: AI Platform CI / Run AI platform tests
    result: PASS
    evidence: run 30307439318, job 90114968306; Ruff was the only failing step.
  - command: ruff 0.15.21 check --fix and ruff format on WH-01 Python paths
    result: PASS
    evidence: temporary WH-01 Ruff repair run 30307962786, job 90116652427.
blockers: []
next_action: Validate all exact-head CI and review/path gates for PR #542, then close the package without starting WH-02 unless real accepted data exists.
```
