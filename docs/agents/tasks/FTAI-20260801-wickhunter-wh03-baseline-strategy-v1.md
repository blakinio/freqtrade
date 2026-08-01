---
task_id: FTAI-20260801-wickhunter-wh03-baseline-strategy-v1
project_lane: freqtrade-wickhunter
status: waiting
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
updated_at: 2026-08-01T15:23:00+02:00
project_lane: freqtrade-wickhunter
phase: implement
session_id: unclaimed
session_role: implementer
execution_mode: codex
execution_reason: multi-file deterministic baseline implementation and tests required
status: waiting
branch: feat/wickhunter-wh03-baseline-strategy-v1
base_branch: develop
related_pr: null
context_pressure: medium
context_growth: stable
decomposition_decision: phased
decomposition_reason: implementation and validation share one baseline contract and report
validation_level: not_started
heavy_validation_runs: 0
proven:
  - WH-03 depends on a terminal WH-02 replay and label contract
derived:
  - WH-04 and WH-05 must consume, not independently redefine, the WH-03 evaluation interface
unknown:
  - final merged WH-02 identities and exact baseline activity
conflicts: []
first_relevant_error: null
changed_paths: []
validation: []
blockers:
  - WH-02 is not yet terminal
next_action: after WH-02 merges, verify its exact contract and claim WH-03 ownership before implementing the shared baseline evaluation interface
```
