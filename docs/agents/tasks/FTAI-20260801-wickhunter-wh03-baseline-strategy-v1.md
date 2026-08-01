---
task_id: FTAI-20260801-wickhunter-wh03-baseline-strategy-v1
project_lane: freqtrade-wickhunter
status: validating
branch: feat/wickhunter-wh03-baseline-strategy-v1
base_branch: develop
created: 2026-08-01
updated: 2026-08-01
related_pr: null
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
updated_at: 2026-08-01T19:39:00+02:00
project_lane: freqtrade-wickhunter
phase: validate
session_id: wh03-20260801-001
session_role: implementer
execution_mode: chat
execution_reason: direct GitHub implementation with exact-head repository validation
status: validating
branch: feat/wickhunter-wh03-baseline-strategy-v1
head: acbb9114f4a10b0122398f1710cf7db8cbabc96d
base_branch: develop
related_pr: null
context_pressure: high
context_growth: stable
decomposition_decision: phased
decomposition_reason: implementation and validation share one baseline contract and report
validation_level: focused
heavy_validation_runs: 0
proven:
  - WH-02 merged as 0e986fab05a38b4a2bc1232c8c0821be1367b0cb after all required checks passed
  - live ownership preflight found no WH-03 branch, PR or overlapping writer
  - the WH-03 branch was created from live develop after WH-02 and Portal PR 956 merged
  - EvaluationCase requires exact long and short WH-02 labels bound to one immutable row
  - reversal and continuation use the existing deterministic strategy and independent memory
  - duplicate evidence, symbol-side-hypothesis cooldown and all strategy rejection reasons remain explicit
  - selected decisions copy WH-02 outcomes, costs, returns, excursions and duration without recomputation
  - the shared v1 interface owns evaluation cases, decisions, summaries, record-factory protocol and report schema for WH-04 and WH-05
  - overall and split, side, symbol, liquidity, source, regime and hypothesis summaries are deterministic
  - protected holdout, model promotion, profitability claims, execution, order and live-capital authority remain disabled
derived:
  - WH-04 can provide advisory score_id and model_version through build_evaluation_decision without redefining cost or summary logic
unknown:
  - exact-head repository CI and formatter result
conflicts: []
first_relevant_error: null
changed_paths:
  - ai_platform/wickhunter/baseline_strategy.py
  - tests/ai_platform_integration/test_wickhunter_baseline_strategy.py
  - docs/ai_platform/WICKHUNTER_BASELINE_STRATEGY.md
  - docs/agents/tasks/FTAI-20260801-wickhunter-wh03-baseline-strategy-v1.md
validation:
  - command: Python AST parse for implementation and focused tests
    result: PASS
    evidence: baseline module and five focused test groups parse successfully
blockers: []
next_action: open the exact four-path PR, run focused and repository CI, repair only concrete failures, then perform fresh exact-head validation and merge
```
