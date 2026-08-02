---
task_id: FTAI-20260802-wickhunter-production-evaluation-loader-v1
project_lane: freqtrade-wickhunter
status: validating
branch: feat/wickhunter-production-evaluation-loader-v1
base_branch: develop
created: 2026-08-02
updated: 2026-08-02
related_pr: null
depends_on:
  - FTAI-20260801-wickhunter-wh01-dataset-builder-v1
  - FTAI-20260801-wickhunter-wh02-deterministic-replay-v1
owned_paths:
  - ai_platform/wickhunter/production_evaluation.py
  - tests/ai_platform_integration/test_wickhunter_production_evaluation.py
  - docs/ai_platform/WICKHUNTER_PRODUCTION_EVALUATION.md
  - docs/agents/tasks/FTAI-20260802-wickhunter-production-evaluation-loader-v1.md
---

# WickHunter production evaluation loader

## Objective

Create the missing fail-closed adapter between the real WH-01 feature dataset, real WH-02 deterministic replay labels and the existing WH-04/WH-05 evaluation interfaces.

## Acceptance

- independently verify both immutable input packages;
- reconstruct domain objects instead of trusting untyped JSON;
- require an exact row-to-label join;
- require one LONG and one SHORT label per feature row;
- reject tampering, duplicates, omissions and unsafe authority;
- expose deterministic evaluation identity;
- no protected holdout, model promotion, execution, credentials, orders or live capital.

## Checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-02T12:50:00+02:00
phase: implementation
status: validating
branch: feat/wickhunter-production-evaluation-loader-v1
base_branch: develop
proven:
  - WH-01 production dataset contains 919 accepted rows
  - exact WH-02 price path contains coverage for all 919 decisions
  - existing WH-04 and WH-05 APIs consume EvaluationCase
  - no production loader previously joined DatasetRow and CandidateLabel contracts
next_action: run focused tests, Ruff, mypy and exact-head repository CI; independently audit the four declared paths; merge only on unchanged green SHA
```
