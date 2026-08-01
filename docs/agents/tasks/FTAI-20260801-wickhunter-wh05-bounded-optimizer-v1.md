---
task_id: FTAI-20260801-wickhunter-wh05-bounded-optimizer-v1
project_lane: freqtrade-wickhunter
status: implementing
branch: feat/wickhunter-wh05-bounded-optimizer-v1-clean
base_branch: develop
created: 2026-08-01
updated: 2026-08-01
related_pr: 962
depends_on:
  - FTAI-20260801-wickhunter-wh03-baseline-strategy-v1
  - FTAI-20260801-wickhunter-wh04-lightgbm-scorer-v1
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
  - docs/agents/tasks/FTAI-20260801-wickhunter-wh04-lightgbm-scorer-v1.md
---

# WH-05 bounded walk-forward optimizer

## Objective

Produce reproducible candidate-only global, regime and symbol-cluster parameter packages
inside immutable bounds. Selection uses purged/embargoed walk-forward validation,
WH-03 baseline evidence and the frozen WH-04 advisory LightGBM interface.

## Phases

1. `WH05-BASELINE` — finite bounded search, seeded surrogate, validation-only ranking and
   descriptive top-k test evidence.
2. `WH05-MODEL-AWARE` — purged/embargoed folds, WH-04 model validation, perturbations,
   global/regime/cluster packages and sparse-scope inheritance.
3. `WH05-VALIDATE` — fresh exact-head repository validation.

## Acceptance

- immutable hard bounds and deterministic seeds;
- explicit finite search space;
- rolling walk-forward geometry with purge and embargo;
- reproducibility and local perturbation checks;
- global, regime and symbol-cluster candidates;
- sparse-scope inheritance;
- protected holdout refusal;
- WH-04 model hashes and identical WH-03/WH-02 evaluation evidence;
- validation-only selection and post-selection descriptive test evidence;
- candidate-only output with no automatic promotion or execution authority.

## Context checkpoint

```yaml
checkpoint_version: 1
policy_version: 2
updated_at: 2026-08-01T21:45:00+02:00
project_lane: freqtrade-wickhunter
phase: implement
session_id: wh05-20260801-002
session_role: implementer
execution_mode: chat
execution_reason: resume baseline package after WH-04 terminal merge and add the frozen model-aware seam
status: implementing
branch: feat/wickhunter-wh05-bounded-optimizer-v1-clean
base_branch: develop
related_pr: 962
context_pressure: high
context_growth: stable
decomposition_decision: phased
decomposition_reason: baseline and model-aware phases share one finite search-space and candidate package contract
validation_level: focused
heavy_validation_runs: 3
proven:
  - baseline finite search is deterministic, bounded and input-order independent
  - baseline selection uses validation evidence only and creates test evidence after ranking
  - baseline exact-head AI Platform, Freqtrade and security CI passed before model-aware work
  - WH-04 terminal package freezes deterministic LightGBM training, calibration and comparison APIs
  - model-aware design keeps WH-04 outputs advisory and candidate-only
derived:
  - each walk-forward fold can train one deterministic model per candidate on training/calibration evidence and evaluate validation/test through the WH-03 interface
  - sparse scopes must inherit a broader global package instead of fitting independent parameters
unknown:
  - exact-head model-aware CI
conflicts: []
first_relevant_error: null
changed_paths:
  - ai_platform/wickhunter/bounded_optimizer.py
  - tests/ai_platform_integration/test_wickhunter_bounded_optimizer.py
  - docs/ai_platform/WICKHUNTER_BOUNDED_OPTIMIZER.md
  - docs/agents/tasks/FTAI-20260801-wickhunter-wh05-bounded-optimizer-v1.md
validation:
  - command: baseline AI Platform CI run 3664
    result: PASS
    evidence: tests, Ruff, formatting, codespell and JSON validation passed
  - command: baseline Freqtrade CI run 4766
    result: PASS
    evidence: pre-commit, documentation, Python 3.11-3.14, coverage, smoke tests and mypy passed
  - command: baseline security analysis run 4426
    result: PASS
    evidence: exact baseline head f063bb6b31a69230bf40a5ae2cf6ee7a100aaee6
blockers: []
next_action: rebase the four owned paths onto terminal WH-04 develop, add model-aware walk-forward/scoped package contracts and run exact-head CI
```
