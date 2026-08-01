---
task_id: FTAI-20260801-wickhunter-wh05-bounded-optimizer-v1
project_lane: freqtrade-wickhunter
status: validating
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
updated_at: 2026-08-01T22:33:00+02:00
project_lane: freqtrade-wickhunter
phase: validate
session_id: wh05-20260801-002
session_role: implementer
execution_mode: chat
execution_reason: exact-head validation of the bounded baseline and model-aware walk-forward package
status: validating
branch: feat/wickhunter-wh05-bounded-optimizer-v1-clean
head: 6937ec9685328e812404afd3b923eb9f17942af3
base_branch: develop
related_pr: 962
context_pressure: high
context_growth: stable
decomposition_decision: phased
decomposition_reason: baseline and model-aware phases share one finite search-space and candidate package contract
validation_level: repository
heavy_validation_runs: 5
proven:
  - WH-03 merged as 03810d0c82072d642946ce1d274c86a577ec5349 and freezes the shared evaluation interface
  - WH-04 merged as 6697bf0a1412fa1b91f0aa0d12a5ed501ee899d3 and freezes deterministic advisory LightGBM training, calibration and comparison
  - PR 962 changes exactly the four declared WH-05 paths
  - the finite search is deterministic, bounded and input-order independent
  - rolling folds contain explicit train, calibration, validation and test splits with purge and embargo barriers
  - ranking uses validation evidence only and test evidence is created only after top-k selection
  - model-aware folds bind exact WH-04 model hashes and WH-03/WH-02 replay identities
  - global, regime and symbol-cluster packages are deterministic
  - sparse scopes inherit a broader package instead of fitting unsupported independent parameters
  - local perturbation evidence is deterministic and remains inside immutable hard bounds
  - protected holdout, test-based selection, automatic promotion, profitability claims, execution, order submission and live-capital authority fail closed
  - AI Platform CI run 3672 passed 1063 tests with 71 skips; Ruff, formatting, codespell and contract validations passed
  - security analysis run 4439 passed on 6937ec9685328e812404afd3b923eb9f17942af3
derived:
  - WH-07 may consume a selected candidate package only as versioned advisory evidence; WH-05 grants no runtime or live authority
unknown: []
conflicts: []
first_relevant_error: null
changed_paths:
  - ai_platform/wickhunter/bounded_optimizer.py
  - tests/ai_platform_integration/test_wickhunter_bounded_optimizer.py
  - docs/ai_platform/WICKHUNTER_BOUNDED_OPTIMIZER.md
  - docs/agents/tasks/FTAI-20260801-wickhunter-wh05-bounded-optimizer-v1.md
validation:
  - command: baseline exact-head CI
    result: PASS
    evidence: AI Platform 3664, Freqtrade 4766 and security 4426 passed before model-aware extension
  - command: local model-aware structural harness
    result: PASS
    evidence: validation-only selection, identical model hashes, perturbation evidence and sparse-scope inheritance were reproduced
  - command: AI Platform CI run 3672
    result: PASS, 1063 tests and 71 skips
    evidence: compile, full tests, Ruff, formatting, codespell and JSON validations passed
  - command: Freqtrade CI run 4779
    result: PASS
    evidence: pre-commit, documentation, Python 3.11, Python 3.12 coverage, Python 3.13, Python 3.14, generated files, smoke tests and mypy passed
  - command: GitHub Actions Security Analysis run 4439
    result: PASS
    evidence: exact head 6937ec9685328e812404afd3b923eb9f17942af3
blockers: []
next_action: validate the checkpoint-only head and merge PR 962 with expected-head protection
```
