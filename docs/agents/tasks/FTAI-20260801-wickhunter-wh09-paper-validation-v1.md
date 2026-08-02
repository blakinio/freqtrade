---
task_id: FTAI-20260801-wickhunter-wh09-paper-validation-v1
project_lane: freqtrade-wickhunter
status: validating
branch: feat/wickhunter-wh09-paper-validation-v1
base_branch: develop
created: 2026-08-01
updated: 2026-08-02
related_pr: 983
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
updated_at: 2026-08-02T12:32:00+02:00
project_lane: freqtrade-wickhunter
phase: validate
session_id: wh09-20260802-004
session_role: implementer
execution_mode: chat
execution_reason: final owner-authored exact-head validation after semantic and mypy hardening
status: validating
branch: feat/wickhunter-wh09-paper-validation-v1
head: e06392bcac5188a91f75d0b7f79579328568907f
base_branch: develop
related_pr: 983
context_pressure: medium
context_growth: stable
decomposition_decision: phased
decomposition_reason: merge the bounded implementation independently from the later real 24-hour observation and evidence analysis
validation_level: final_owner_exact_head_pending
heavy_validation_runs: 3
proven:
  - WH-07 merged as bde362801d18ca2abf2615f4d1233b9b0f8f618a after exact-head checks passed
  - WH-08 merged as cfa0eae53d6ff54f5ef39b34a00e1cf09a9f1916 after Portal, E2E, repository and security checks passed
  - PR 983 contains exactly the four declared WH-09 implementation, test and documentation paths
  - the default terminal policy cannot be weakened below 24 hours, 96 snapshots, 99 percent fresh-source coverage, the canonical safety-exercise set or the drawdown ceiling
  - activation requests are bound to their policy identity and cannot declare a shorter window
  - published evidence verification reconstructs request, observations, parity, exercises, report and candidate review instead of trusting rewritten manifests or checksums alone
  - request and replay-shadow parity identities are recomputed through their canonical domain payloads
  - final self-removing validation run 30743603723 passed Ruff, formatting and all focused WH-09 tests
  - owner-authored AI Platform CI and security validation passed at 7ffc99f7be9cdb9074839612f56f93f2ce75c8ef
  - pre-commit identified one missing local annotation and commit e06392bcac5188a91f75d0b7f79579328568907f repaired it while removing the helper workflow
  - all temporary workflows were removed and helper PRs 999, 1001, 1003, 1005, 1006, 1007, 1008, 1009 and 1011 were closed without merge
  - activation, evidence evaluation and candidate review remain read-only with zero credentials, orders, execution and live-capital authority
derived:
  - implementation and synthetic contract validation may merge after final owner-authored exact-head repository CI and independent diff audit pass
  - terminal sustained evidence remains incomplete until a real immutable activation request and observation window satisfy the declared policy
unknown:
  - exact production model, parameter, dataset and rollback identities selected for the immutable activation request
  - terminal evidence result after the real observation window
conflicts: []
first_relevant_error: null
changed_paths:
  - ai_platform/wickhunter/paper_validation.py
  - tests/ai_platform_integration/test_wickhunter_paper_validation.py
  - docs/ai_platform/WICKHUNTER_PAPER_VALIDATION.md
  - docs/agents/tasks/FTAI-20260801-wickhunter-wh09-paper-validation-v1.md
validation:
  - command: original PR exact-head Freqtrade CI
    result: FAIL — WH-09 enum aliases and typing errors identified; unrelated Telegram age-string boundary also observed
  - command: bounded self-removing repair and hardening workflows
    result: PASS — enum, typing, terminal-policy and formatting defects repaired without leaving workflow files
  - command: final semantic verification run 30743603723
    result: PASS
    evidence: Ruff check and format passed; all focused WH-09 tests passed; temporary workflows removed
  - command: owner-authored AI Platform CI and security checks at 7ffc99f7be9cdb9074839612f56f93f2ce75c8ef
    result: PASS
  - command: pre-commit at 7ffc99f7be9cdb9074839612f56f93f2ce75c8ef
    result: FAIL — one missing annotation repaired at e06392bcac5188a91f75d0b7f79579328568907f
blockers:
  - final owner-authored exact-head AI Platform, Freqtrade and security workflows must pass
  - independent final diff audit must report zero material findings
next_action: run final owner-authored exact-head CI and independent audit, merge PR 983 if green, then materialize exact production model and parameter identities and publish the immutable WH09-ACTIVATE package
```
