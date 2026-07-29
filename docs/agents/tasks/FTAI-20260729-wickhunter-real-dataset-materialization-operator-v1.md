---
task_id: FTAI-20260729-wickhunter-real-dataset-materialization-operator-v1
status: completed
branch: agent/wickhunter-real-dataset-materialization-operator-v1
base_branch: develop
created: 2026-07-29
updated: 2026-07-29
related_pr: 723
depends_on:
  - FTAI-20260729-wickhunter-real-dataset-materialization-preflight-v1
owned_paths:
  - ai_platform/wickhunter/materialization.py
  - ai_platform/scripts/wickhunter_dataset_materialization.py
  - tests/ai_platform_integration/test_wickhunter_dataset_materialization.py
  - docs/ai_platform/WICKHUNTER_DATASET_MATERIALIZATION_OPERATOR.md
  - docs/agents/tasks/FTAI-20260729-wickhunter-real-dataset-materialization-operator-v1.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_WICKHUNTER_LIQUIDATION_BOT_PROGRAM.md
  - docs/agents/tasks/FTAI-20260729-wickhunter-real-dataset-materialization-preflight-v1.md
  - docs/ai_platform/WICKHUNTER_DATASET_BUILDER.md
  - docs/ai_platform/WICKHUNTER_REAL_DATASET_MATERIALIZATION_PREFLIGHT.md
---

# WickHunter real dataset materialization operator v1

## Goal

Implement a deterministic no-network WH-01 operator that validates exact immutable accepted-import, market-context, universe-history and split-geometry inputs, produces a bounded missing-input report, calls the existing dataset builder only after a ready preflight, and independently verifies every output identity.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-29T20:45:00+02:00
head: 110f0c254eccc8bbd75ee768d4d9a8c736fa40e4
branch: develop
pr: none
status: ready
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_WICKHUNTER_LIQUIDATION_BOT_PROGRAM.md
  - docs/agents/tasks/FTAI-20260729-wickhunter-real-dataset-materialization-preflight-v1.md
  - docs/ai_platform/WICKHUNTER_DATASET_BUILDER.md
  - docs/ai_platform/WICKHUNTER_REAL_DATASET_MATERIALIZATION_PREFLIGHT.md
owned_paths:
  - ai_platform/wickhunter/materialization.py
  - ai_platform/scripts/wickhunter_dataset_materialization.py
  - tests/ai_platform_integration/test_wickhunter_dataset_materialization.py
  - docs/ai_platform/WICKHUNTER_DATASET_MATERIALIZATION_OPERATOR.md
  - docs/agents/tasks/FTAI-20260729-wickhunter-real-dataset-materialization-operator-v1.md
proven:
  - PR 723 was squash-merged as 110f0c254eccc8bbd75ee768d4d9a8c736fa40e4 after exact-head AI Platform CI, full Freqtrade CI and zizmor passed.
  - The no-network operator validates immutable accepted imports, canonical market-context and universe-history rows, split geometry, exact SHA-256 identities and false authority flags.
  - Missing inputs return a bounded blocked report without creating a dataset; malformed, tampered, future-data, traversal or authority-bearing inputs fail closed.
  - Ready materialization calls the unchanged WH-01 builder and independently verifies manifest, partitions, rows, temporal bounds, sources, universe history and artifact hashes.
  - Production Liquid20 conversion produced an accepted import with 29253 accepted records and 0 rejected records.
  - WH-02 remains blocked until real immutable market-context and universe-history evidence plus frozen split geometry produce a non-empty verified WH-01 dataset.
derived:
  - The software boundary from exact immutable inputs to a verified WH-01 dataset is complete.
  - The next bounded package must source or package real market and universe evidence without adding network access to materialization or granting model, replay, trading, execution or live-capital authority.
unknown:
  - Which production paths contain suitable immutable market-context and universe-history evidence.
  - Whether the accepted interval yields a non-empty dataset under the first frozen production split geometry.
conflicts: []
first_failure:
  marker: initial_exact_head_pre_commit
  evidence: An unused fixture binding and one Ruff formatting mismatch were corrected without changing behavior.
rejected_hypotheses:
  - Add a production request or Synology workflow before the operator merged.
  - Query live endpoints from the materialization process.
  - Generate synthetic snapshots when production inputs are missing.
  - Start WH-02 before a non-empty verified real dataset exists.
changed_paths:
  - ai_platform/wickhunter/materialization.py
  - ai_platform/scripts/wickhunter_dataset_materialization.py
  - tests/ai_platform_integration/test_wickhunter_dataset_materialization.py
  - docs/ai_platform/WICKHUNTER_DATASET_MATERIALIZATION_OPERATOR.md
  - docs/agents/tasks/FTAI-20260729-wickhunter-real-dataset-materialization-operator-v1.md
validation:
  - command: AI Platform CI 30472371682
    result: PASS
    evidence: Exact PR head 8d1ab1d54fd7846fa95fdc3eb8b65bbfc7ebad52 passed targeted platform tests, compile, Ruff, format, codespell and JSON validation.
  - command: Freqtrade CI 30472371524
    result: PASS
    evidence: Pre-commit, docs, Python 3.11-3.14, Python 3.12 coverage, smoke tests, Ruff, format, mypy, distributions and CI Gate passed.
  - command: GitHub Actions security analysis 30472370393
    result: PASS
    evidence: zizmor passed on the exact PR head.
blockers: []
next_action: Create a fresh bounded WickHunter task from current develop to inventory and package immutable production market-context and dynamic-universe history, then run the merged WH-01 operator preflight; do not start WH-02 until the report is ready and a non-empty verified dataset is materialized.
```
