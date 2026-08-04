# FTAI-20260803 Portal Remediation — Issue 1122 (Archived)

```yaml
task_id: FTAI-20260803-portal-remediation-1122
programme_id: FTAI-20260803-portal-remediation
issue: 1122
repository: blakinio/freqtrade
lane: freqtrade-portal
task_kind: implementation
phase: closeout
status: completed
priority: high
prompting_standard_version: 2.1
execution_policy_version: 2
execution_mode: github_only
branch: fix/portal-1122-migration-schema-integrity
base_branch: develop
base_head: 1c7044e9699727732928dcdf71e0fe4e1a159108
validated_product_head: 408c1d30c688a960eb6daba892d6c7241cd12ddf
pr: 1159
superseded_prs:
  - 1158
ownership_released_on_merge: true
shared_path_leases: []
repository_work_remaining: false
external_acceptance_remaining: false
live_capital_authorized: false
withdrawals_enabled: false
protected_production_deployment_authorized: false
```

## Result

Portal schema construction now has one repository-owned revision and readiness authority. Production requires PostgreSQL and never mutates schema from application startup. The migration command serializes creation, records the exact dialect-bound schema fingerprint, rejects unversioned or divergent databases, and produces value-free integrity evidence. SQLite remains local/test-only with foreign-key enforcement on every connection.

The durable model manifest covers all 41 Portal tables. Required tenant-aware relations are enforced in ORM metadata and the authoritative revision, intentionally soft historical/external references are documented, the missing Bot Operations tables are included, and command parent rows are flushed before dependent history rows.

## Acceptance evidence

- production/staging startup calls readiness only and contains no `Base.metadata.create_all()` path;
- exact revision `20260803_01_portal_authoritative` binds sequence, dialect and deterministic schema fingerprint;
- inventory compares tables, columns, types, nullability, defaults, primary/unique/check/foreign-key constraints and indexes;
- ORM and migration inventories both contain 41 tables with no duplicate owner or unclassified table drift;
- required bot, identity, risk, model-control and Bot Operations relations reject orphan and tenant-mismatched rows;
- Trade Intelligence uniqueness is tenant-scoped;
- SQLite enables and verifies `PRAGMA foreign_keys=ON` for memory and file-backed connections;
- PostgreSQL tests prove concurrent migration convergence, exactly one winner for duplicate command mutations, transactional DDL rollback, restart readiness, active-connection termination with fail-closed operation and readiness recovery, and audit/outbox atomicity;
- unversioned existing data fails closed to backup, scan, quarantine, rebuild and owner-approved restore rather than silent mutation;
- exact-image migration, readiness and API boot run against ephemeral PostgreSQL before traffic acceptance;
- PostgreSQL backup/restore preserves the exact revision and readiness fingerprint;
- generated artifacts are secret-free and explicitly do not claim protected deployment or live-capital authority.

## Exact-head validation

Validated product head: `408c1d30c688a960eb6daba892d6c7241cd12ddf`.

- Portal Schema Integrity `30884475933`: PASS, including PostgreSQL concurrency, duplicate mutation, connection-loss, rollback and restore tests.
- AI Platform CI `30884475926`: PASS.
- Portal Schema Exact Image `30884475927`: PASS.
- Portal OIDC State Claim `30884475928`: PASS.
- Portal OIDC State Claim PostgreSQL `30884475938`: PASS.
- Portal Completeness Audit `30884476018`: PASS.
- GitHub Actions Security Analysis `30884475985`: PASS.

Repository-wide closeout workflows must pass again on the exact final archive head before merge.

## Fresh audit

The continuation audit challenged the draft completion claim, recovered the first-failure traceback from an exact-head diagnostic artifact, fixed the Bot Operations parent/history flush ordering, removed the temporary diagnostic workflow, and added the two missing production-dialect proofs for duplicate domain mutations and connection loss. The final changed-path review found no unresolved material finding. All inline security threads are resolved and outdated; PR #1158 is closed as superseded, leaving PR #1159 as the sole implementation owner.

## Terminal checkpoint

```yaml
checkpoint_version: 2
updated_at: 2026-08-04T06:50:00Z
head: 408c1d30c688a960eb6daba892d6c7241cd12ddf
branch: fix/portal-1122-migration-schema-integrity
pr: 1159
status: completed
proven:
  - application startup is migration/readiness-only and production is PostgreSQL-only
  - deterministic 41-table model and migration inventory has zero drift
  - required tenant-aware hard relations and documented soft-reference boundaries are enforced
  - SQLite local/test and PostgreSQL production-dialect integrity semantics pass
  - duplicate mutation, connection loss, rollback, restart, outbox and backup/restore boundaries pass on PostgreSQL
  - exact-image and secret-free evidence gates pass
  - duplicate PR 1158 is closed and all review threads are resolved
derived:
  - the task becomes archived on develop only through merge of PR 1159
unknown: []
conflicts: []
blockers: []
next_action: Remove the active task record, pass required checks on the exact final closeout head, mark PR #1159 ready, merge it, verify Issue #1122 closes and verify post-merge develop state.
```
