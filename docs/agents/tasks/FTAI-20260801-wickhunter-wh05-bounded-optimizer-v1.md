---
task_id: FTAI-20260801-wickhunter-wh05-bounded-optimizer-v1
project_lane: freqtrade-wickhunter
status: validating
branch: feat/wickhunter-wh05-bounded-optimizer-v1-clean
base_branch: develop
created: 2026-08-01
updated: 2026-08-01
related_pr: null
depends_on:
  - FTAI-20260801-wickhunter-wh03-baseline-strategy-v1
owned_paths:
  - ai_platform/wickhunter/bounded_optimizer.py
  - tests/ai_platform_integration/test_wickhunter_bounded_optimizer.py
  - docs/ai_platform/WICKHUNTER_BOUNDED_OPTIMIZER.md
  - docs/agents/tasks/FTAI-20260801-wickhunter-wh05-bounded-optimizer-v1.md
required_reads:
  - docs/agents/EXECUTION_PROTOCOL.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_WICKHUNTER_LIQUIDATION_BOT_PROGRAM.md
  - docs/agents/tasks/FTAI-20260801-wickhunter-wh03-baseline-strategy-v1.md
  - docs/ai_platform/WICKHUNTER_BASELINE_STRATEGY.md
---

# WH-05 bounded validation optimizer

## Objective

Evaluate an explicit finite set of bounded WickHunter parameter candidates through the WH-03 interface, select only from validation evidence and attach descriptive test stability evidence to the final top-k without accessing the protected holdout or authorizing promotion.

## Phases

1. `WH05-DESIGN` — freeze finite search-space, validation objective, surrogate, split-isolation and top-k contracts.
2. `WH05-IMPLEMENT` — deterministic bounded optimizer, trial evidence and stability report.
3. `WH05-VALIDATE` — fresh exact-head repository validation.

## Acceptance

- finite caller-supplied parameter search space;
- every candidate validated against explicit bounds;
- deterministic seeded initial design and RBF surrogate selection;
- maximum trial budget and deterministic tie-breaking;
- WH-03 evaluation and exact WH-02 costs only;
- training/validation/test isolation and protected-holdout refusal;
- validation-only ranking;
- test evidence produced only after selection for top-k;
- top-k validation/test delta and slice-stability evidence;
- no automatic promotion, profitability claim, execution, order or live-capital authority.

## Context checkpoint

```yaml
checkpoint_version: 1
policy_version: 2
updated_at: 2026-08-01T21:15:00+02:00
project_lane: freqtrade-wickhunter
phase: validate
session_id: wh05-20260801-001
session_role: implementer
execution_mode: chat
execution_reason: direct GitHub implementation with exact-head repository validation
status: validating
branch: feat/wickhunter-wh05-bounded-optimizer-v1-clean
base_branch: develop
related_pr: null
context_pressure: high
context_growth: stable
decomposition_decision: phased
decomposition_reason: search policy, surrogate, trials and stability report share one finite search-space identity
validation_level: focused
heavy_validation_runs: 1
proven:
  - WH-03 merged to develop as 03810d0c82072d642946ce1d274c86a577ec5349 after final exact-head checks passed
  - the optimizer accepts only an explicit finite sequence of parameter candidates and validates each candidate against WickHunterParameterBounds
  - candidate and search-space identities are immutable and input-order independent
  - seeded initial trials and the fixed RBF surrogate remain inside the supplied candidate set
  - the objective is computed from WH-03 reports and inherits exact WH-02 labels and costs
  - ranking uses validation objective only; test reports are produced after ranking and only for final top-k candidates
  - protected holdout, test-based selection, model promotion, profitability claims, execution, order and live-capital authority remain disabled
  - AI platform test suite passed with 1059 tests and 71 skips on the pre-cleanup implementation head
  - two Ruff findings were corrected without changing optimizer behavior
  - final candidate is rebuilt from develop with exactly four owned paths and no temporary workflow history
derived:
  - WH-07 may consume only an explicitly selected terminal parameter artifact after downstream integration; WH-05 does not promote it
unknown:
  - exact-head repository CI for the clean candidate
conflicts:
  - WH-04 runs on a separate clean branch and owns disjoint model paths
first_relevant_error: null
changed_paths:
  - ai_platform/wickhunter/bounded_optimizer.py
  - tests/ai_platform_integration/test_wickhunter_bounded_optimizer.py
  - docs/ai_platform/WICKHUNTER_BOUNDED_OPTIMIZER.md
  - docs/agents/tasks/FTAI-20260801-wickhunter-wh05-bounded-optimizer-v1.md
validation:
  - command: AI Platform CI tests on pre-cleanup head
    result: PASS
    evidence: 1059 passed, 71 skipped
  - command: Ruff on pre-cleanup head
    result: repaired
    evidence: C901 and B008 findings corrected in the clean candidate
blockers: []
next_action: run exact-head repository CI on the clean four-path PR, repair only concrete failures, perform fresh validation and merge
```
