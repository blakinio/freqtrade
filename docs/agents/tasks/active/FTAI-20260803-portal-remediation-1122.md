# FTAI-20260803 Portal Remediation — Issue 1122

```yaml
task_id: FTAI-20260803-portal-remediation-1122
programme_id: FTAI-20260803-portal-remediation
issue: 1122
repository: blakinio/freqtrade
lane: freqtrade-portal
task_kind: implementation
phase: discovery
status: active
priority: high
prompting_standard_version: 2.1
execution_policy_version: 2
context_pressure: high
decomposition_decision: phased
execution_mode: github_only
run_scope: autonomous_task
continuation_policy: continue_until_real_stop
task_completion_policy: finalize_archive_and_continue
user_communication: terminal_only
feature_scope:
  type: contract_producer
  user_facing: false
  backend_required: true
  frontend_required: false
  integration_required: true
  e2e_required: true
  completion_claim: partial_producer
branch: fix/portal-1122-migration-schema-integrity
base_branch: develop
base_head: 1c7044e9699727732928dcdf71e0fe4e1a159108
implementation_head: 1c7044e9699727732928dcdf71e0fe4e1a159108
pr: pending
pr_state: pending
related_prs: []
owned_paths:
  - ai_platform/portal/control_plane/database.py
  - ai_platform/portal/identity/public_runtime.py
  - ai_platform/portal/**/models.py
  - ai_platform/portal/**/migrations/**
  - ai_platform/portal/database/**
  - tests/ai_platform/portal/**/test_*migration*.py
  - tests/ai_platform/portal/**/test_*database*.py
  - tests/ai_platform_integration/**
  - docs/ai_platform/portal/**
  - tools/portal_schema/**
  - .github/workflows/portal-schema-integrity.yml
shared_path_leases:
  - production migration ordering and schema revision authority
  - shared SQLAlchemy metadata and relational constraints
  - Portal database readiness contract
repository_work_remaining: true
external_acceptance_remaining: false
live_capital_authorized: false
withdrawals_enabled: false
protected_production_deployment_authorized: false
```

## Objective

Establish one authoritative ordered Portal migration chain and deterministic schema-readiness contract for the supported production dialect, eliminate staging/production `create_all()` mutation, enforce tenant-aware relational integrity, preserve explicitly soft evidence references, and publish exact-head secret-free integrity evidence without protected deployment or live-capital effects.

## Acceptance inventory

- [ ] Staging/production startup never invokes `Base.metadata.create_all()` or otherwise mutates schema outside the migration runner.
- [ ] One explicit migration revision identifies the expected schema and readiness fails closed on pending, divergent or unknown revisions.
- [ ] ORM metadata and migrated schema are deterministically compared for tables, columns, types, nullability, primary/unique/check/foreign-key constraints and indexes.
- [ ] Every durable ORM table has an ordered migration or explicit non-production classification; every migration-owned table has an explicit model/external ownership classification.
- [ ] Required tenant relationships use hard tenant-aware constraints with explicit delete/retention behavior.
- [ ] Intentionally soft historical/external identities are documented and validated at application boundaries without being represented as FKs.
- [ ] SQLite, where retained for local/test use, enables `PRAGMA foreign_keys=ON` on every connection and passes supported-semantic parity tests.
- [ ] The supported production dialect is selected and tested for concurrent duplicates, rollback, connection loss, restart and outbox atomicity boundaries owned by this producer.
- [ ] Existing data receives a read-only integrity scan plus deterministic fail-closed quarantine/repair policy before new constraints.
- [ ] Migration upgrade, rollback and backup/restore revision evidence preserve relational integrity.
- [ ] Exact deployment images boot only after migration/readiness validation and emit a secret-free schema-integrity artifact.
- [ ] Architecture, deployment and programme status documentation matches exact evidence.
- [ ] Fresh independent audit has zero open material findings.
- [ ] Required exact-head CI is green and all review threads are resolved.
- [ ] PR is terminal, task is archived and ownership/leases are released.

## Safety and ownership boundary

This task is the sole producer for Portal migration ordering, schema revisions, shared ORM relational constraints and schema readiness. Other Issues may submit requirements but may not create competing migrations while this task is active. Integrity repair must not silently delete, rewrite, reassign or expose immutable audit, risk, order, trade, model, security or cross-tenant evidence. Protected production deployment, credentials, live trading, withdrawals and live-capital changes are forbidden.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-03T16:10:00Z
status: active
branch: fix/portal-1122-migration-schema-integrity
implementation_head: 1c7044e9699727732928dcdf71e0fe4e1a159108
pr: pending
proven:
  - audit PR 1082 and programme PR 1145 are merged
  - issues 1124, 1126 and 1127 are complete
  - issue 1137 repository work is merged and its ownership is released
  - issue 1122 is the sole READY migration/schema producer and blocks issue 1132
  - exact task base is develop@1c7044e9699727732928dcdf71e0fe4e1a159108
  - no overlapping active migration/schema task or implementation PR was found
  - no protected production, credential, trading, withdrawal or live-capital authority is granted
  - local sandbox cannot resolve github.com; GitHub connector and GitHub Actions are the execution environment
derived:
  - task must begin with a deterministic current-head ORM/migration/startup/deployment inventory before mutation
unknown:
  - exact current table, constraint and migration drift on post-1157 develop
  - complete production startup paths that still create schema
  - exact supported production dialect and deployment topology after current repository evidence is reconciled
conflicts: []
blockers: []
next_action: Inventory current Portal database construction, migration ordering, ORM metadata, deployment startup and schema tests on branch fix/portal-1122-migration-schema-integrity, then implement the smallest complete authoritative migration/readiness foundation.
```
