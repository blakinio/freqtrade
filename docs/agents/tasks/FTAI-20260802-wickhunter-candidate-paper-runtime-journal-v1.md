---
task_id: FTAI-20260802-wickhunter-candidate-paper-runtime-journal-v1
repository: blakinio/freqtrade
status: implementing
phase: implementation
owner: autonomous-agent
created_at: 2026-08-02
updated_at: 2026-08-02
related_pr: null
blocked_by:
  - FTAI-20260802-wickhunter-candidate-runtime-binding-v1
next_action: complete the observation-native WH-09 publication path; validate atomic journal recovery, tamper rejection and exact-head CI
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
