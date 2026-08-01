---
task_id: FTAI-20260801-wickhunter-wh09-paper-validation-v1
project_lane: freqtrade-wickhunter
status: waiting
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

1. `WH09-ACTIVATE` — freeze code/model/parameter/dataset identities and start one immutable request-only shadow/paper run. Checkpoint `waiting` and exit after activation evidence.
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
updated_at: 2026-08-01T15:23:00+02:00
project_lane: freqtrade-wickhunter
phase: integrate
session_id: unclaimed
session_role: implementer
execution_mode: codex
execution_reason: evidence tooling and bounded request contracts require implementation and tests
status: waiting
branch: feat/wickhunter-wh09-paper-validation-v1
base_branch: develop
related_pr: null
context_pressure: high
context_growth: stable
decomposition_decision: phased
decomposition_reason: activation and later evidence analysis share one immutable paper-validation identity
validation_level: not_started
heavy_validation_runs: 0
proven:
  - WH-09 depends on terminal WH-07 and WH-08
  - the observation window must not keep an agent session active
  - program completion ends at shadow/paper readiness, not live-capital readiness
derived:
  - activation and evidence analysis require separate sessions on the same task
unknown:
  - final runtime, model, parameter and observability identities
  - required evidence-window result
conflicts: []
first_relevant_error: null
changed_paths: []
validation: []
blockers:
  - WH-07 and WH-08 are not terminal
next_action: after WH-07 and WH-08 merge, claim WH-09 paths and implement the bounded immutable paper/shadow activation contract
```
