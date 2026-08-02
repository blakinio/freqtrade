---
task_id: FTAI-20260802-wickhunter-candidate-paper-runtime-journal-v1
repository: blakinio/freqtrade
status: validating
phase: validation
owner: autonomous-agent
created_at: 2026-08-02
updated_at: 2026-08-02
related_pr: 1051
blocked_by: []
next_action: complete retained exact-head CI, independently audit the final diff, and merge when terminal gates pass
---

# WickHunter candidate PAPER runtime journal v1

## Objective

Provide the durable, restart-safe execution boundary between the verified candidate/PAPER runtime binding and the prospective WH-09 evidence package.

## Scope

- atomically commit each `ShadowRuntime` generation with state, portal snapshot, canonical paper observation and full decision evidence;
- recover only a contiguous, checksum-verified generation chain;
- seed and preserve candidate model, parameter, dataset and code identities before the first directional decision;
- freeze the runtime policy in the journal identity and reject policy substitution;
- record parity and safety exercises as immutable identity-addressed evidence;
- publish WH-09 evidence from canonical observations only after the prospective window elapsed and every policy blocker is cleared;
- add focused recovery, empty-decision, policy substitution, tamper and early-finalization tests.

## Out of scope

- live trading or capital;
- credentials or order adapters;
- automatic promotion;
- market/liquidation acquisition and Synology deployment;
- shortening or fabricating the 24-hour observation window.

## Safety invariants

- `protected_holdout_accessed=false`
- `automatic_promotion_enabled=false`
- `trading_credentials_present=false`
- `order_adapter_present=false`
- `execution_enabled=false`
- `orders_submitted=0`
- `live_capital_authorized=false`

## Validation checkpoint — 2026-08-02

- The deterministic v9 integrity repair passed formatting, Ruff, mypy, the existing paper-validation tests, and the candidate PAPER runtime journal tests.
- Generation recovery now verifies the full previous-manifest chain, frozen runtime-policy identity, and canonical observation identity before accepting any state.
- Coordinated manifest substitutions are covered by focused regressions.
- Every temporary paper-runtime-journal integrity workflow was removed before this checkpoint commit.
- Retained repository exact-head CI remains the final pre-merge gate.
