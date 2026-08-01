---
task_id: FTAI-20260801-wickhunter-wh02-deterministic-replay-v1
project_lane: freqtrade-wickhunter
status: validating
branch: feat/wickhunter-wh02-deterministic-replay-v1
base_branch: develop
created: 2026-08-01
updated: 2026-08-01
related_pr: 955
depends_on:
  - FTAI-20260731-wickhunter-wh01-production-materialization-v1
  - FTAI-20260801-wickhunter-wh02-replay-price-path-v1
owned_paths:
  - ai_platform/wickhunter/deterministic_replay.py
  - tests/ai_platform_integration/test_wickhunter_deterministic_replay.py
  - docs/ai_platform/WICKHUNTER_DETERMINISTIC_REPLAY.md
  - docs/agents/tasks/FTAI-20260801-wickhunter-wh02-deterministic-replay-v1.md
required_reads:
  - docs/agents/EXECUTION_PROTOCOL.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_WICKHUNTER_LIQUIDATION_BOT_PROGRAM.md
  - docs/agents/tasks/FTAI-20260801-wickhunter-wh02-replay-price-path-v1.md
  - docs/ai_platform/WICKHUNTER_REPLAY_PRICE_PATH.md
---

# WH-02 deterministic replay and event labels

## Objective

Bind the immutable WH-01 dataset and verified exact trade path into deterministic replay labels and independently verifiable replay evidence without accessing the protected holdout or authorizing trading.

## Phases

1. `WH02-DESIGN` — freeze entry, delay, fees, slippage, TP/SL ordering, timeout, MFE, MAE, time-to-outcome, purge/embargo and parity contracts.
2. `WH02-IMPLEMENT` — implement replay clock, labels, atomic publication, hashes and verifier.
3. `WH02-VALIDATE` — fresh exact-head validator session.

## Acceptance

- deterministic TP-first, SL-first and timeout outcomes;
- explicit delayed/missing-entry behavior;
- decimal-safe fees and slippage;
- returns, MFE, MAE and time-to-outcome;
- purged/embargoed walk-forward geometry;
- immutable self-hashed output and independent verification;
- replay/shadow parity fixture;
- protected holdout refused;
- no performance, model, execution, order or live-capital authority.

## Invocation

`Uruchom WickHunter WH-02.` resumes the exact current phase. `Zweryfikuj WickHunter WH-02.` is valid only when the checkpoint identifies a coherent candidate head.

## Context checkpoint

```yaml
checkpoint_version: 1
policy_version: 2
updated_at: 2026-08-01T19:09:31+02:00
project_lane: freqtrade-wickhunter
phase: validate
session_id: wh02-20260801-001
session_role: implementer
execution_mode: chat
execution_reason: direct GitHub implementation with exact-head GitHub Actions validation
status: validating
branch: feat/wickhunter-wh02-deterministic-replay-v1
head: da0224d2989db8a2f3162a5e16d6834be9da1597
base_branch: develop
related_pr: 955
context_pressure: high
context_growth: stable
decomposition_decision: phased
decomposition_reason: contract design, implementation and validation share one immutable replay output
validation_level: repository
heavy_validation_runs: 2
proven:
  - live ownership preflight found no existing WH-02 deterministic replay branch or overlapping writer
  - the branch was created from develop at e5601c640d9f53f878645caca356762c71dfdf06
  - PR 955 changes exactly the four declared WH-02 owned paths
  - the replay policy freezes exact entry, costs, TP/SL ordering, timeout, excursions, split geometry and parity
  - the implementation emits deterministic long and short labels, atomic evidence and an independent verifier
  - isolated replay validation passes all 7 focused tests
  - both completed AI Platform CI attempts passed all 1057 repository tests
  - the first AI CI lint findings were repaired and the second attempt passed Ruff check
  - the second AI CI formatting diff was applied exactly
  - protected holdout, model, performance, execution, order and live-capital authority remain disabled
derived:
  - the same pure replay_event_label function is the WH-07 replay/shadow parity seam
unknown:
  - exact-head CI result after the formatting and checkpoint commits
conflicts:
  - open readiness remediation PR 950 owns collector/runtime paths and does not overlap this task
first_relevant_error: null
changed_paths:
  - ai_platform/wickhunter/deterministic_replay.py
  - tests/ai_platform_integration/test_wickhunter_deterministic_replay.py
  - docs/ai_platform/WICKHUNTER_DETERMINISTIC_REPLAY.md
  - docs/agents/tasks/FTAI-20260801-wickhunter-wh02-deterministic-replay-v1.md
validation:
  - command: isolated Python syntax and functional replay suite
    result: PASS, 7 tests
    evidence: long TP, short SL ordering, timeout, missing entry, holdout, embargo, atomic build and tamper rejection
  - command: AI Platform CI run 3635
    result: 1057 tests PASS; Ruff reported 9 bounded findings
    evidence: all findings repaired in deterministic_replay.py
  - command: AI Platform CI run 3638
    result: 1057 tests PASS; Ruff check PASS; Ruff format supplied one-file diff
    evidence: formatter diff applied exactly in da0224d2989db8a2f3162a5e16d6834be9da1597
blockers: []
next_action: wait only for automatically running exact-head PR checks, inspect any concrete failure, then perform fresh validation and merge PR 955 when all required checks are green
```
