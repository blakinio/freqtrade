---
task_id: FTAI-20260727-wickhunter-wh01-dataset-builder
status: validating
branch: feat/wickhunter-wh01-dataset-builder-v1
base_branch: develop
created: 2026-07-27
updated: 2026-07-27
related_pr: null
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
updated_at: 2026-07-27T23:55:00+02:00
head: 47cea47461794e8bd47bd4cbc5f8ed4162ba71d6
branch: feat/wickhunter-wh01-dataset-builder-v1
pr: null
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
  - WH-01 implementation selects only acceptance.status=pass packages with verified manifest, artifact and accepted-event hashes.
  - Historical available_at_ms is preserved as canonical feature-side receive time; future evidence fails closed.
  - Dataset partitions, source selections, universe history and the self-hashed manifest are published atomically without overwrite.
derived:
  - WH-01 consumes accepted import artifacts without modifying Liquid20, Market Data Fabric, portal, BM, RL-v2 or Synology paths.
  - Dataset construction fails closed on rejected acceptance, hash mismatch, future availability, holdout overlap, duplicate evidence or missing universe eligibility.
unknown:
  - Exact first accepted bulk Tardis import is still owner/provider-access dependent; the builder accepts any conforming accepted immutable import package and is validated with synthetic fixtures only.
conflicts: []
first_failure: null
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
  - docs/agents/tasks/FTAI-20260727-wickhunter-wh01-dataset-builder.md
validation:
  - command: python -m py_compile ai_platform/wickhunter/dataset.py tests/ai_platform_integration/test_wickhunter_dataset_builder.py
    result: PASS
    evidence: Draft implementation and focused test module compile in isolation.
blockers: []
next_action: Open a draft PR and repair exact-head CI or review failures before closeout.
```
