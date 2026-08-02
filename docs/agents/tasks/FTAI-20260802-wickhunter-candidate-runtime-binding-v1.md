---
task_id: FTAI-20260802-wickhunter-candidate-runtime-binding-v1
project_lane: freqtrade-wickhunter
status: validating
branch: feat/wickhunter-candidate-runtime-binding-v1
base_branch: develop
created: 2026-08-02
updated: 2026-08-02
related_pr: null
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

## Checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-02T15:20:00+02:00
phase: validation
status: validating
branch: feat/wickhunter-candidate-runtime-binding-v1
base_branch: develop
head_sha_before_checkpoint: d385ba1338002bcd60f6adcdcbcbd6ecb2372c17
proven:
  - exact candidate activation boundary merged as d385ba1338002bcd60f6adcdcbcbd6ecb2372c17
  - WH-07 read-only SHADOW/PAPER runtime is already merged
  - risk engine candidate PAPER authorization remains default-off and preserves all other vetoes
next_action: complete exact-head repository CI; audit the final diff and merge only on an unchanged green SHA
```
