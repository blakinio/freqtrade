---
task_id: FTAI-20260802-wickhunter-candidate-runtime-binding-v1
project_lane: freqtrade-wickhunter
status: done
branch: feat/wickhunter-candidate-runtime-binding-v1
base_branch: develop
created: 2026-08-02
updated: 2026-08-02
related_pr: 1043
depends_on:
  - FTAI-20260802-wickhunter-candidate-paper-activation-v1
  - FTAI-20260801-wickhunter-wh07-shadow-runtime-v1
owned_paths:
  - ai_platform/wickhunter/candidate_activation.py
  - ai_platform/wickhunter/candidate_runtime_binding.py
  - ai_platform/wickhunter/paper_validation.py
  - tests/ai_platform_integration/test_wickhunter_candidate_runtime_binding.py
  - docs/ai_platform/WICKHUNTER_CANDIDATE_RUNTIME_BINDING.md
  - docs/agents/tasks/FTAI-20260802-wickhunter-candidate-runtime-binding-v1.md
---

# WickHunter candidate runtime binding

## Objective

Bind an independently verified candidate package and immutable WH-09 activation request to WH-07 decision requests without introducing any execution or order authority.

## Acceptance

- one verification pass returns the exact candidate identity, parameters and frozen WH-04 model artifact;
- one typed verification pass returns the exact WH-09 request and policy;
- model, parameter, dataset, code, bot, mode, policy and activation-window identities must match;
- only SHADOW/PAPER requests using the frozen parameter bounds are accepted;
- pre-authorized, out-of-window, drifted-identity and non-frozen requests fail closed;
- the seam installs the verified scorer and enables only the candidate PAPER risk exception;
- credentials, private exchange access, order adapter, execution, orders, automatic promotion and live capital remain absent.

## Terminal checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-02T15:55:00+02:00
phase: done
status: done
branch: feat/wickhunter-candidate-runtime-binding-v1
base_branch: develop
related_pr: 1043
validated_head_sha: 65e3f9f4fadbe6995e4919670ba96f44de35e22b
merge_sha: 09d3d2e6d237e557d57d04cb48657a40f2e0b7f0
validation_level: exact_head_repository_ci_and_independent_diff_audit
proven:
  - typed candidate loading reconstructs the exact WH-04 artifact after full package verification
  - typed activation loading reconstructs the exact WH-09 request and policy while preserving the compatibility verifier API
  - model, selected parameters, rollback identities, dataset, code, bot, mode, policy and activation window fail closed on mismatch
  - only the verified advisory scorer and the existing default-off candidate PAPER authorization bit are installed
  - focused validation passed ruff, formatting, mypy and candidate activation, PAPER validation and runtime-binding tests
  - exact-head AI Platform CI, security analysis, pre-commit, documentation, Python 3.11 through 3.14, coverage, build, ruff and mypy passed
  - final compare contained exactly six declared product, test and documentation paths and no temporary workflow
  - independent final diff audit found no material defect and no unresolved review thread
  - PR 1043 was squash-merged as 09d3d2e6d237e557d57d04cb48657a40f2e0b7f0
  - protected holdout, automatic promotion, trading credentials, order adapter, execution, orders and live capital remain absent or false
blockers: []
next_action: continue the existing request-only WH-02 replay materialization; after terminal verified evidence, close PR 1026 without merge and resume the queued candidate and activation operations
```
