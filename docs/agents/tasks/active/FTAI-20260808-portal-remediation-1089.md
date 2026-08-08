# FTAI-20260808 Portal Remediation — Issue 1089

```yaml
task_id: FTAI-20260808-portal-remediation-1089
programme_id: FTAI-20260803-portal-remediation
issue: 1089
repository: blakinio/freqtrade
lane: freqtrade-portal
task_kind: implementation
phase: validation
status: validating
priority: high
prompting_standard_version: 2.1
execution_policy_version: 2
context_pressure: medium
decomposition_decision: phased_single_issue
execution_mode: github_only
run_scope: single_task
continuation_policy: continue_until_real_stop
task_completion_policy: finalize_archive
user_communication: terminal_only
claim_id: ftai-1089-20260808T194400Z-gpt56sol
feature_scope:
  type: authenticated_deployment_composition
  user_facing: true
  backend_required: true
  frontend_required: true
  integration_required: true
  e2e_required: true
branch: repair/1089-portal-api-mode-deployment
base_branch: develop
base_head: c64df386a4fa3ba739b6eaa1a223ca798a7bcae2
pr: 1393
owned_paths:
  - .github/workflows/portal-api-mode-postgresql.yml
  - ai_platform/portal/database/transfer.py
  - ai_platform/portal/identity/public_runtime.py
  - ai_platform/portal/web/lib/portal-api.ts
  - deploy/synology/portal/Dockerfile
  - deploy/synology/portal-oidc/Dockerfile.control-plane
  - deploy/synology/portal-oidc/control-plane-entrypoint.sh
  - deploy/synology/portal-oidc/deploy.py
  - deploy/synology/portal-oidc/requirements.txt
  - tests/ai_platform/portal/database/test_state_transfer.py
  - tests/ai_platform/portal/deployment/test_portal_oidc_public_deploy.py
  - tests/ai_platform/portal/identity/test_public_runtime_composition.py
  - docs/agents/tasks/active/FTAI-20260808-portal-remediation-1089.md
shared_path_leases: []
conflict_avoidance:
  - PR 1388 owns ai_platform/portal/control_plane/api.py, ai_platform/portal/control_plane/models.py, ai_platform/portal/database/schema.py and related runtime-generation paths; do not edit those paths while that PR is active.
repository_work_remaining: true
external_acceptance_remaining: true
live_capital_authorized: false
withdrawals_enabled: false
protected_production_deployment_authorized: false
```

## Objective

Repair Issue #1089 without inventing a second Portal architecture. Reuse the existing identity-enabled canonical control-plane composition, make staging/production web strictly API-backed, move the public Portal deployment to a private PostgreSQL topology with explicit schema authority, preserve legacy SQLite state during cutover, and fail closed before traffic acceptance.

## Implemented repair candidate

- The public runtime composes identity with the canonical Portal control plane and rejects production SQLite.
- `/healthz` is liveness-only; `/readyz` verifies database connectivity, schema revision and required product-router composition.
- The web image defaults to API mode and refuses fixture data mode, identity fixture mode or a missing control-plane URL in staging/production.
- The control-plane image contains the full runtime dependency set, including `jsonschema==4.26.0`, after exact-image CI exposed the missing package.
- `ai_platform.portal.database.transfer` provides an offline, value-preserving SQLite-to-PostgreSQL transfer path. It accepts only known current/pre-logout schema shapes, runs integrity checks, requires a fresh PostgreSQL target, copies authoritative model tables in dependency order, verifies row counts and records value-free evidence.
- The Synology deployer now provisions only a private, digest-pinned PostgreSQL service with no published database port; writes candidate runtime state separately; quiesces the old Portal before state transition; snapshots legacy SQLite before transfer; runs the authoritative migration CLI before candidate promotion; validates readiness; selects web API mode; and activates the candidate runtime env only after control/web/public probes succeed.
- Existing PostgreSQL deployments receive a protected pre-migration backup before migration/readiness validation.
- A retained non-protected exact-image workflow builds the exact control/web images, migrates PostgreSQL, transfers a persisted synthetic dry-run bot from SQLite, boots API mode, proves unauthorized product access fails closed, restarts the control plane and proves the row survives, and proves production fixture mode is rejected.
- No protected Synology deployment, production secret, live trading, withdrawal, model promotion or live-capital mutation is authorized or performed by this task.

## Acceptance plan

- [x] Public runtime constructs the existing identity-enabled full canonical Portal API.
- [x] Identity/session and representative product routes are present in one app and require identity-derived tenant context.
- [x] `/healthz` is liveness-only and `/readyz` proves database/schema/router composition without exposing secrets.
- [x] Production/staging web startup rejects fixture mode and requires a server-side control-plane URL.
- [x] Synology deployment selects API mode and a private PostgreSQL topology, applies versioned migration explicitly, snapshots legacy SQLite before transfer and gates promotion on readiness.
- [x] Deployment image/process contract keeps public API unprivileged and private providers server-side.
- [ ] New exact-image PostgreSQL workflow passes on the current implementation head.
- [ ] Focused backend/deployment tests pass on the current implementation head.
- [ ] Required repository workflows pass on the exact final implementation head.
- [ ] Fresh independent audit reports zero material findings or all findings are repaired.
- [ ] API-mode E2E acceptance passes at the available non-protected boundary; protected-target acceptance remains separately identified.
- [ ] PR review threads are resolved and no duplicate repair PR owns this Issue.
- [ ] Protected-target acceptance is reported separately and never inferred from CI.

## Validation evidence so far

- Old exact-image run `31275863765` failed after full control-plane composition because the exact image lacked `jsonschema`; the bounded runtime requirements now include the repository-pinned `jsonschema==4.26.0`.
- Old Freqtrade CI `31275863804` failed only because `ruff-format` reformatted `test_public_runtime_composition.py`; that exact formatting change is now committed.
- Those runs are stale evidence after the PostgreSQL implementation and are not final acceptance.

## Recovery checkpoint

```yaml
policy_version: 1
generation: 1
session_id: 20260808T200400Z-owner-continuation
session_started_at: 2026-08-08T20:04:00Z
checkpointed_at: 2026-08-08T20:21:18Z
last_progress_at: 2026-08-08T20:21:18Z
phase: validation
exact_head: 46f98d5666b00a231ac9b999167402fe30a637f0
pull_request: 1393
active_operation: GitHub Actions validation of PostgreSQL API-mode repair
external_run_ids: []
operation_started_at: null
wait_deadline_at: null
check_generation: implementation-postgresql-v1
checks_used: 0
status: active
safe_to_resume: true
resume_condition: current-head GitHub Actions exist or a new actionable validation failure is available
next_action: Inspect one aggregate CI snapshot for the exact current head, isolate the first actionable failure, and perform one focused repair; if the implementation is green, proceed to fresh independent audit and E2E evidence.
```

## Context checkpoint

```yaml
checkpoint_version: 4
updated_at: 2026-08-08T20:21:18Z
status: validating
branch: repair/1089-portal-api-mode-deployment
base_head: c64df386a4fa3ba739b6eaa1a223ca798a7bcae2
head: 46f98d5666b00a231ac9b999167402fe30a637f0
pr: 1393
invocation_started_at: 2026-08-08T20:04:00Z
last_progress_at: 2026-08-08T20:21:18Z
ci_checks_for_current_head: 0
unchanged_state_checks: 0
identical_failure_retries: 0
repair_cycles_for_current_gate: 0
context_reconstruction_attempts: 1
stall_warnings: 0
proven:
  - public runtime composes authenticated canonical product routes and separates liveness/readiness
  - production/staging web fails closed outside API mode
  - public production runtime rejects SQLite
  - Synology deployment candidate now uses a private digest-pinned PostgreSQL topology and explicit schema CLI
  - legacy SQLite state is snapshotted and transferred only through bounded schema/integrity acceptance
  - exact-image PostgreSQL validation workflow is retained on the repair branch
unknown:
  - exact current-head CI outcome for the PostgreSQL implementation
  - independent audit result
  - final non-protected API-mode E2E result
  - protected Synology target acceptance outcome
conflicts:
  - PR 1388 owns control-plane API/schema/model paths; those paths remain untouched
blockers: []
next_action: Inspect one aggregate CI snapshot for head 46f98d5666b00a231ac9b999167402fe30a637f0 and repair the first actionable failure with a focused hypothesis.
```
