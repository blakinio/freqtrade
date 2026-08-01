---
task_id: FTAI-20260801-wickhunter-wh09-paper-validation-v1
project_lane: freqtrade-wickhunter
status: implementing
branch: feat/wickhunter-wh09-paper-validation-v1
base_branch: develop
created: 2026-08-01
updated: 2026-08-01
related_pr: null
depends_on:
  - FTAI-20260801-wickhunter-wh07-shadow-runtime-v1
  - FTAI-20260801-wickhunter-wh08-portal-observability-v1
owned_paths:
  - ai_platform/wickhunter/paper_validation.py
  - tests/ai_platform_integration/test_wickhunter_paper_validation.py
  - docs/ai_platform/WICKHUNTER_PAPER_VALIDATION.md
  - docs/agents/tasks/FTAI-20260801-wickhunter-wh09-paper-validation-v1.md
required_reads:
  - docs/agents/EXECUTION_PROTOCOL.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_WICKHUNTER_LIQUIDATION_BOT_PROGRAM.md
  - docs/agents/tasks/FTAI-20260801-wickhunter-wh07-shadow-runtime-v1.md
  - docs/agents/tasks/FTAI-20260801-wickhunter-wh08-portal-observability-v1.md
---

# WH-09 paper validation and promotion evidence

## Objective

Produce sustained shadow/paper evidence, replay-to-runtime reconciliation, rollback identity and explicit model/parameter promotion-candidate packages without granting live-capital authority.

## Phases

1. `WH09-ACTIVATE` — freeze code/model/parameter/dataset identities and publish one immutable request-only shadow/paper run package. Checkpoint `waiting` and exit after activation evidence.
2. `WH09-EVIDENCE` — a later fresh session verifies the exact run and analyzes the declared evidence window.
3. `WH09-VALIDATE` — independent validation of reconciliation and candidate packages.

## Acceptance

- immutable run identity and no-overwrite evidence;
- sustained source, candidate, risk and simulated-position evidence;
- replay-to-runtime decision reconciliation;
- stale-data, drift and circuit-breaker evidence;
- model and parameter candidate packages only;
- explicit rollback identity;
- explicit owner decision point;
- no automatic promotion, credentials, order submission or live-capital authority.

## Invocation

`Uruchom WickHunter WH-09.` resolves activation versus evidence analysis from the live checkpoint. A worker never remains active during the observation window.

## Context checkpoint

```yaml
checkpoint_version: 1
policy_version: 2
updated_at: 2026-08-01T23:58:00+02:00
project_lane: freqtrade-wickhunter
phase: implement
session_id: wh09-20260801-001
session_role: implementer
execution_mode: chat
execution_reason: direct GitHub implementation of bounded immutable activation and evidence contracts
status: implementing
branch: feat/wickhunter-wh09-paper-validation-v1
head: cfa0eae53d6ff54f5ef39b34a00e1cf09a9f1916
base_branch: develop
related_pr: null
context_pressure: high
context_growth: stable
decomposition_decision: phased
decomposition_reason: activation and later sustained evidence analysis share one immutable run identity and candidate-review contract
validation_level: ownership_preflight
heavy_validation_runs: 0
proven:
  - WH-07 merged as bde362801d18ca2abf2615f4d1233b9b0f8f618a after all exact-head checks passed
  - WH-08 merged as cfa0eae53d6ff54f5ef39b34a00e1cf09a9f1916 after Portal, E2E, repository and security checks passed
  - the WH-09 branch was created from terminal WH-08 develop head
  - the default evidence policy requires at least 24 hours and 96 snapshots and must not be shortened for terminal claims
  - activation, evidence evaluation and candidate review remain read-only with zero credentials, orders, execution and live-capital authority
derived:
  - implementation and synthetic contract validation can merge now, while terminal sustained evidence must remain incomplete until the real observation window is satisfied
unknown:
  - exact production model, parameter, dataset and rollback identities selected for the immutable activation request
  - terminal evidence result after the real observation window
conflicts: []
first_relevant_error: null
changed_paths:
  - docs/agents/tasks/FTAI-20260801-wickhunter-wh09-paper-validation-v1.md
validation:
  - command: live dependency and ownership preflight
    result: PASS
blockers: []
next_action: implement and validate immutable activation, observation, parity, safety-exercise, candidate-review and tamper-evident evidence packages
```
