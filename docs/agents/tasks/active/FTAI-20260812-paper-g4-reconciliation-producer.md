---
task_id: FTAI-20260812-paper-g4-reconciliation-producer
status: ready
branch: codex/g4-reconciliation-producer
base_branch: develop
created: 2026-08-12
updated: 2026-08-12
related_pr: "1498"
project_lane: freqtrade-portal
feature_scope: contract_producer
complete_user_facing_feature: false
owned_paths:
  - ai_platform/portal/reconciliation/**
  - tests/ai_platform/portal/reconciliation/**
  - docs/agents/tasks/active/FTAI-20260812-paper-g4-reconciliation-producer.md
required_reads:
  - AGENTS.md
  - docs/agents/AGENTS.md
  - docs/ai_platform/portal/PAPER_PLATFORM_IMPLEMENTATION_PLAN.md
  - docs/ai_platform/portal/ARCHITECTURE_DECISIONS.md#ADR-020
search_first:
  - G4 reconciliation producer
optional_reads: []
---

# G4 dependency-independent reconciliation producer

## Goal

Produce the isolated PAPER command/reconciliation state-machine core and narrow future
Supervisor/Gateway ports without claiming G4 or a user-facing vertical slice complete.

## Acceptance criteria

- Transport acknowledgement cannot become reconciled success.
- Replay, stale identity/version/fence, observed ordering, restart, retry and poison isolation are deterministic.
- Persistence is represented by a versioned durable snapshot/CAS port without a shared migration.
- Focused tests, type/lint and a fresh independent audit pass.
- One unmerged PR targets `develop` and states the missing Supervisor/Gateway/PostgreSQL integration.

## Context checkpoint

```yaml
checkpoint_version: 1
policy_version: 2
updated_at: 2026-08-12T08:46:39Z
head: 906b05082a84cf2ec98f66a3691fc5601512cf6f
branch: codex/g4-reconciliation-producer
pr: 1498
status: ready
phase: integrate
session_id: codex-20260812-g4-producer
session_role: implementer
execution_mode: codex
execution_reason: isolated multi-file state-machine implementation and focused test loop
project_lane: freqtrade-portal
context_routes:
  - docs/ai_platform/portal/PAPER_PLATFORM_IMPLEMENTATION_PLAN.md#G4
context_pressure: medium
context_growth: stable
context_score: 7
decomposition_decision: single
decomposition_reason: one isolated producer with one contract and test boundary
owned_paths:
  - ai_platform/portal/reconciliation/**
  - tests/ai_platform/portal/reconciliation/**
  - docs/agents/tasks/active/FTAI-20260812-paper-g4-reconciliation-producer.md
proven:
  - live develop resolved to ec41d2542bff57f74cd10856b7dc22265213d991
  - no existing bounded G4 reconciliation producer task was found
  - issues 1092, 1093 and 1099 remain open and are future consumers/integration dependencies
derived:
  - no shared RuntimeGeneration migration is needed for this producer
unknown:
  - final Supervisor and Gateway transport contracts
conflicts: []
first_failure:
  marker: none
  evidence: none
rejected_hypotheses: []
changed_paths:
  - ai_platform/portal/reconciliation/__init__.py
  - ai_platform/portal/reconciliation/README.md
  - ai_platform/portal/reconciliation/engine.py
  - ai_platform/portal/reconciliation/models.py
  - ai_platform/portal/reconciliation/ports.py
  - ai_platform/portal/reconciliation/store.py
  - docs/agents/tasks/active/FTAI-20260812-paper-g4-reconciliation-producer.md
  - tests/ai_platform/portal/reconciliation/test_engine.py
validation:
  - command: python -m pytest -q tests/ai_platform/portal/reconciliation tests/ai_platform/portal/bot_operations/test_command_persistence.py tests/ai_platform/portal/events/test_outbox.py tests/ai_platform/portal/control_plane/test_runtime_generation_isolation_binding.py
    result: PASS
    evidence: 42 passed in 2.25s
  - command: python -m ruff check ai_platform/portal/reconciliation tests/ai_platform/portal/reconciliation
    result: PASS
    evidence: All checks passed
  - command: python -m mypy ai_platform/portal/reconciliation
    result: PASS
    evidence: Success, no issues found in 5 source files
  - command: python -m compileall -q ai_platform/portal/reconciliation
    result: PASS
    evidence: exit 0
  - command: git diff --check
    result: PASS
    evidence: exit 0
blockers: []
next_action: Bind PR 1498 to the finalized G3 Supervisor/Gateway and PostgreSQL adapter in the coordinator integration task without changing this producer's state authority.
```

## Delivery boundary

```yaml
implementation_status: producer_complete
user_facing_feature_complete: false
missing_consumers:
  - G3 Runtime Supervisor lifecycle observation binding
  - G3 Gateway authoritative runtime read binding
  - PostgreSQL migration/repository integration
  - API/UI/audit composition
follow_up_tasks:
  - Issue #1099 desired-state lifecycle composition
  - Issue #1092 authoritative runtime reads/reconciliation
  - Issue #1093 authoritative valuation composition
```

## Live-capital boundary

This task is PAPER-only. It does not authorize model or strategy promotion, production deployment,
live trading, capital allocation, withdrawals, exchange-credential changes or a LIVE transition.
