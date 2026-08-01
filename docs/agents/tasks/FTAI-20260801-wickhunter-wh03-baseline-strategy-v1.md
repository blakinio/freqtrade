---
task_id: FTAI-20260801-wickhunter-wh03-baseline-strategy-v1
project_lane: freqtrade-wickhunter
status: completed
branch: feat/wickhunter-wh03-baseline-strategy-v1
base_branch: develop
created: 2026-08-01
updated: 2026-08-01
related_pr: 958
depends_on:
  - FTAI-20260801-wickhunter-wh02-deterministic-replay-v1
owned_paths:
  - ai_platform/wickhunter/baseline_strategy.py
  - tests/ai_platform_integration/test_wickhunter_baseline_strategy.py
  - docs/ai_platform/WICKHUNTER_BASELINE_STRATEGY.md
  - docs/agents/tasks/FTAI-20260801-wickhunter-wh03-baseline-strategy-v1.md
required_reads:
  - docs/agents/EXECUTION_PROTOCOL.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_WICKHUNTER_LIQUIDATION_BOT_PROGRAM.md
  - docs/agents/tasks/FTAI-20260801-wickhunter-wh02-deterministic-replay-v1.md
---

# WH-03 configurable deterministic baseline

## Objective

Deliver complete reversal and continuation baselines on the accepted WH-02 replay contract and freeze the common evaluation interface later consumed by WH-04 and WH-05.

## Phases

1. `WH03-IMPLEMENT` — baseline implementation and acceptance report.
2. `WH03-VALIDATE` — fresh exact-head validator session.

## Acceptance

- configurable reversal and continuation baselines;
- bounded parameters only;
- cooldown and duplicate protection;
- explicit ignore/rejection reasons;
- identical WH-02 fees, slippage and labels;
- long/short, symbol, liquidity, source and regime slices;
- frozen shared evaluation interface with exactly one owner;
- no AI promotion or profitability claim.

## Invocation

`Uruchom WickHunter WH-03.` starts only after WH-02 is terminal and merged.

## Context checkpoint

```yaml
checkpoint_version: 1
policy_version: 2
updated_at: 2026-08-01T20:02:00+02:00
project_lane: freqtrade-wickhunter
phase: terminal
session_id: wh03-20260801-001
session_role: implementer
execution_mode: chat
execution_reason: direct GitHub implementation with exact-head repository validation
status: completed
branch: feat/wickhunter-wh03-baseline-strategy-v1
head: 970975036ff6730fa4560c873796dfa73179f360
base_branch: develop
related_pr: 958
context_pressure: high
context_growth: stable
decomposition_decision: phased
decomposition_reason: implementation and validation share one baseline contract and report
validation_level: repository
heavy_validation_runs: 2
proven:
  - WH-02 merged as 0e986fab05a38b4a2bc1232c8c0821be1367b0cb after all required checks passed
  - live ownership preflight found no WH-03 branch, PR or overlapping writer
  - PR 958 changes exactly the four declared WH-03 owned paths
  - EvaluationCase requires exact long and short WH-02 labels bound to one immutable row
  - reversal and continuation use the existing deterministic strategy and independent memory
  - duplicate evidence, symbol-side-hypothesis cooldown and all strategy rejection reasons remain explicit
  - selected decisions copy WH-02 outcomes, costs, returns, excursions and duration without recomputation
  - the shared v1 interface owns evaluation cases, decisions, summaries, record-factory protocol and report schema for WH-04 and WH-05
  - overall and split, side, symbol, liquidity, source, regime and hypothesis summaries are deterministic
  - the first validation run passed 1062 tests and exposed only one bounded Ruff complexity annotation plus pre-commit typing and formatting findings
  - the repaired exact head 970975036ff6730fa4560c873796dfa73179f360 passed AI Platform CI run 3650 and Freqtrade CI run 4752
  - Python 3.11, 3.12 with coverage, 3.13 and 3.14, mypy, Ruff, Ruff format, pre-commit, documentation, distribution build and zizmor all passed
  - protected holdout, model promotion, profitability claims, execution, order and live-capital authority remain disabled
derived:
  - WH-04 can provide advisory score_id and model_version through build_evaluation_decision without redefining cost or summary logic
unknown: []
conflicts: []
first_relevant_error: null
changed_paths:
  - ai_platform/wickhunter/baseline_strategy.py
  - tests/ai_platform_integration/test_wickhunter_baseline_strategy.py
  - docs/ai_platform/WICKHUNTER_BASELINE_STRATEGY.md
  - docs/agents/tasks/FTAI-20260801-wickhunter-wh03-baseline-strategy-v1.md
validation:
  - command: AI Platform CI run 3650
    result: PASS
    evidence: compile, 1062 tests, Ruff, formatter, codespell and contract checks
  - command: Freqtrade CI run 4752
    result: PASS
    evidence: pre-commit, docs, Python 3.11/3.12/3.13/3.14, coverage, mypy, smoke tests and distributions
  - command: GitHub Actions Security Analysis run 4412
    result: PASS
    evidence: zizmor completed successfully
blockers: []
next_action: validate the checkpoint-only final PR head, audit reviews and exact four-path scope, then squash-merge PR 958 with expected-head protection
```
