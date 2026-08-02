---
task_id: FTAI-20260802-wickhunter-production-evaluation-loader-v1
project_lane: freqtrade-wickhunter
status: validating
branch: feat/wickhunter-production-evaluation-loader-v1
base_branch: develop
created: 2026-08-02
updated: 2026-08-02
related_pr: 1019
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
updated_at: 2026-08-02T13:01:00+02:00
phase: validation
status: validating
branch: feat/wickhunter-production-evaluation-loader-v1
head: ef56eabf87264027aec7961aaf6c209f761c8b5d
base_branch: develop
related_pr: 1019
proven:
  - WH-01 production dataset contains 919 accepted rows
  - exact WH-02 price path contains coverage for all 919 decisions
  - existing WH-04 and WH-05 APIs consume EvaluationCase
  - no production loader previously joined DatasetRow and CandidateLabel contracts
  - loader independently invokes both immutable package verifiers before reading rows
  - DatasetRow, LiquidationFeatureVector, source aggregate, market metric and CandidateLabel contracts are reconstructed and their identities rechecked
  - the join requires exactly one LONG and one SHORT label for every feature row
  - missing labels, extra labels, duplicate identities, altered rows and unsafe authority fail closed
  - result exposes deterministic evaluation_sha256 and zero execution or live-capital authority
  - self-removing validation run 30744787078 passed Ruff, formatting, mypy and all focused loader tests
  - PR 1019 contains exactly the four declared implementation, test and documentation paths
validation:
  - command: ruff check and ruff format --check on production_evaluation.py and focused tests
    result: PASS
  - command: mypy ai_platform/wickhunter/production_evaluation.py
    result: PASS
  - command: pytest -q tests/ai_platform_integration/test_wickhunter_production_evaluation.py
    result: PASS
blockers:
  - owner-authored exact-head AI Platform, Freqtrade and security CI must pass
  - independent final diff audit must report zero material findings
next_action: run owner-authored exact-head CI and independent audit; merge PR 1019 only on unchanged green SHA
```
