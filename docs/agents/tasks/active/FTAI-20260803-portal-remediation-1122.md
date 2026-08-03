# FTAI-20260803 Portal Remediation Issue 1122

```yaml
task_id: FTAI-20260803-portal-remediation-1122
programme_id: FTAI-20260803-portal-remediation
repository: blakinio/freqtrade
lane: freqtrade-portal
task_kind: implementation
phase: investigate
status: investigating
priority: high
issue: 1122
base_branch: develop
base_head: 1c7044e9699727732928dcdf71e0fe4e1a159108
branch: fix/portal-1122-schema-integrity
head: pending_first_commit
pr: pending
prompting_standard_version: 2.1
execution_policy_version: 2
context_pressure: high
context_growth: stable
context_score: 11
estimate_confidence: high
decomposition_decision: phased
decomposition_reason: one authoritative migration/schema contract with several inseparable validation phases
execution_mode: chat_github_actions
execution_reason: GitHub state, narrow file mutations and remote exact-dialect validation are available without local protected access
run_scope: autonomous_task
continuation_policy: continue_until_real_stop
task_completion_policy: finalize_archive_and_continue
feature_scope:
  type: backend_infrastructure
  user_facing: false
  backend_required: true
  frontend_required: false
  integration_required: true
  e2e_required: true
implementation_authorized: true
live_capital_authorized: false
withdrawals_enabled: false
protected_production_deployment_authorized: false
owned_paths:
  - ai_platform/portal/control_plane/database.py
  - ai_platform/portal/identity/public_runtime.py
  - ai_platform/portal/**/models.py
  - ai_platform/portal/**/migrations/**
  - deploy/synology/portal-oidc/**
  - tools/portal_schema/**
  - tests/ai_platform/portal/**
  - tests/ai_platform_integration/**
  - docs/ai_platform/portal/SCHEMA_RELATION_MATRIX.md
  - docs/ai_platform/portal/SYSTEM_ARCHITECTURE.md
  - .github/workflows/portal-schema-integrity.yml
  - docs/agents/tasks/active/FTAI-20260803-portal-remediation-1122.md
shared_path_leases:
  - production_migrations_schema
```

## Objective

Eliminate the split Portal schema authority. Production and staging must use one ordered versioned migration chain; readiness must prove the exact expected revision and relational integrity on the selected production dialect. ORM metadata remains a validation source only where deterministic parity is proven.

## Trusted finding and acceptance inventory

- Staging/production startup must not call `Base.metadata.create_all()`.
- One exact migration revision must identify the expected schema; pending, divergent and unknown states fail readiness.
- Every ORM/model-owned durable table must have an ordered migration or explicit external ownership classification.
- Columns, types, nullability, primary/unique/check/foreign-key constraints and indexes must be compared deterministically.
- Required references must use tenant-aware hard constraints; intentional evidence/external/soft references must be explicitly classified.
- SQLite, when retained for local/test use, must enable `PRAGMA foreign_keys=ON` for every connection and pass supported-semantic parity tests.
- Existing data must receive a non-destructive integrity scan and deterministic quarantine/fail-closed plan before constraints are enforced.
- Production-dialect validation must cover concurrent duplicate mutations, rollback, outbox atomicity, restart and connection loss.
- Backup/restore and rollback evidence must preserve relational integrity and exact revision state.
- Exact deployment images must boot only after migration/readiness validation and emit secret-free schema-integrity evidence.
- Required exact-head CI, fresh independent audit, applicable API-mode system evidence, terminal PR/Issue state and ownership release are mandatory.

## Initial evidence

```yaml
PROVEN:
  - audit PR 1082 merged and Issue 1122 remains open
  - exact develop head at claim was 1c7044e9699727732928dcdf71e0fe4e1a159108
  - no existing Issue 1122 task, branch or implementation PR existed at claim
  - control_plane.database.create_schema uses Base.metadata.create_all
  - identity.public_runtime.build_public_app uses Base.metadata.create_all in staging/production
  - Issue evidence identifies three bot_operations ORM tables without ordered migrations
  - Issue evidence identifies globally scoped trade_intent_id uniqueness on a tenant-keyed table
DERIVED:
  - migration completeness must be established before removing production create_all
  - Issue 1122 must remain the sole producer of shared migration/schema authority
UNKNOWN:
  - exact post-1137 ORM versus migration inventory
  - complete relation and constraint scope matrix
  - current production-dialect workflow coverage and trusted runner availability for this task
CONFLICT: []
```

## Ordered phases

1. Inventory every ORM table, migration-owned table, constraint, index and runtime schema path on the exact branch head.
2. Define the supported production dialect/topology, ordered migration manifest and relation classification matrix.
3. Add missing migrations and non-destructive integrity preflight/quarantine rules.
4. Replace staging/production `create_all()` with migration plus exact-revision readiness.
5. Add deterministic schema-drift tooling and SQLite foreign-key enforcement/parity.
6. Add PostgreSQL concurrency, rollback, restart, connection-loss and exact-image validation.
7. Run fresh independent audit, final exact-head CI, resolve reviews, merge, close Issue 1122, archive and release the migration lease.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-03T15:35:00Z
session_id: chat-20260803-1122-01
session_role: investigator
session_rotation_count: 0
status: investigating
phase: investigate
branch: fix/portal-1122-schema-integrity
head: pending_first_commit
pr: pending
validation_level: none
heavy_validation_runs: 0
unchanged_state_checks: 0
identical_failure_retries: 0
repair_cycles_for_current_gate: 0
context_reconstruction_attempts: 1
stall_warnings: 0
blockers: []
next_action: Inventory exact ORM tables, ordered migrations, startup schema mutations and tenant-scope constraints on branch fix/portal-1122-schema-integrity.
```
