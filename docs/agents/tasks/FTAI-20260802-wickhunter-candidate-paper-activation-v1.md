---
task_id: FTAI-20260802-wickhunter-candidate-paper-activation-v1
project_lane: freqtrade-wickhunter
status: validating
branch: feat/wickhunter-candidate-paper-activation-v1
base_branch: develop
created: 2026-08-02
updated: 2026-08-02
related_pr: null
depends_on:
  - FTAI-20260802-wickhunter-production-evaluation-loader-v1
  - FTAI-20260801-wickhunter-wh09-paper-validation-v1
owned_paths:
  - ai_platform/wickhunter/candidate_activation.py
  - tests/ai_platform_integration/test_wickhunter_candidate_activation.py
  - docs/ai_platform/WICKHUNTER_CANDIDATE_ACTIVATION.md
  - docs/agents/tasks/FTAI-20260802-wickhunter-candidate-paper-activation-v1.md
---

# WickHunter candidate paper activation

## Objective

Add the missing fail-closed boundary that independently verifies the real candidate model/parameter package and publishes an immutable WH-09 paper run request without granting execution authority.

## Acceptance

- exact package, checksum, manifest and artifact verification;
- semantic model and parameter identity reconstruction;
- validation-only/test-descriptive and rollback binding checks;
- coordinated tampering rejection;
- immutable paper activation using the existing WH-09 contracts;
- no holdout access, automatic promotion, credentials, order adapter, orders, execution or live capital.

## Checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-02T14:05:00+02:00
phase: validation
status: validating
branch: feat/wickhunter-candidate-paper-activation-v1
base_branch: develop
proven:
  - WH-09 immutable paper request and package verifier are merged
  - production EvaluationCase loader is merged
  - candidate materialization operation is queued after exact replay evidence
next_action: run focused tests, Ruff, mypy and exact-head repository CI; repair findings; merge only on unchanged green SHA
```
