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
  - .github/workflows/portal-api-mode-browser.yml
  - .github/workflows/portal-schema-exact-image.yml
  - ai_platform/portal/database/transfer.py
  - ai_platform/portal/identity/public_runtime.py
  - ai_platform/portal/web/lib/portal-api.ts
  - deploy/synology/portal/Dockerfile
  - deploy/synology/portal-oidc/Dockerfile.control-plane
  - deploy/synology/portal-oidc/control-plane-entrypoint.sh
  - deploy/synology/portal-oidc/deploy.py
  - deploy/synology/portal-oidc/postgresql_copy_on_write.py
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

Repair Issue #1089 without inventing a second Portal architecture. Reuse the existing identity-enabled canonical control-plane composition, make staging/production web strictly API-backed, move the public Portal deployment to a private PostgreSQL topology with explicit schema authority, preserve durable state during cutover, and fail closed before traffic acceptance.

## Implemented repair candidate

- Public runtime composes identity with the canonical Portal control plane and rejects production SQLite.
- `/healthz` is liveness-only; `/readyz` verifies database connectivity, schema revision and required product-router composition.
- Web defaults to API mode and refuses fixture data, identity fixture mode or a missing control-plane URL in staging/production.
- The exact control-plane image contains the runtime dependency/resource set required by the full control plane, including `jsonschema`, Feature Registry and Strategy Lab assets discovered by exact-image validation.
- `ai_platform.portal.database.transfer` provides bounded offline SQLite-to-PostgreSQL transfer with source integrity validation, fresh-target enforcement, dependency-ordered copy and post-copy row/integrity verification.
- Synology deployment provisions a private digest-pinned PostgreSQL service with no published database port, writes candidate runtime state separately, snapshots/quiesces legacy state, runs authoritative migration/readiness before candidate promotion, selects web API mode and activates the candidate only after control/web/public probes succeed.
- Existing PostgreSQL revisions use copy-on-write cutover: backup, quiesce, clone to a candidate database, migration/readiness on the candidate and retention of the old database for rollback.
- Non-protected exact-image PostgreSQL evidence covers migration, SQLite state transfer, canonical authenticated backend read + dry-run mutation, unauthenticated fail-closed behavior, web API mode, restart persistence and fixture rejection.
- A dedicated Chromium workflow now exercises a real production API-mode web image through HTTPS, a real persisted identity session and CSRF token, a backend-derived `/bots` read, a browser-originated dry-run bot mutation through the Next BFF, refresh persistence, and explicit zero request interception/fixture identity evidence.
- The deployment test that previously depended on the Synology-only Liquid20 host path now isolates that host dependency with a deterministic group-id stub; host-mount behavior remains covered by dedicated deployment tests.
- No protected Synology deployment, production secret, live trading, withdrawal, model promotion or live-capital mutation is authorized or performed by this task.

## Acceptance plan

- [x] Public runtime constructs the existing identity-enabled full canonical Portal API.
- [x] Identity/session and representative product routes are present in one app and require identity-derived tenant context.
- [x] `/healthz` is liveness-only and `/readyz` proves database/schema/router composition without exposing secrets.
- [x] Production/staging web startup rejects fixture mode and requires a server-side control-plane URL.
- [x] Synology deployment selects API mode and a private PostgreSQL topology, applies versioned migration explicitly, preserves previous state and gates promotion on readiness.
- [x] Deployment image/process contract keeps public API unprivileged and private providers server-side.
- [x] Real API-mode Chromium acceptance workflow exists with no request interception or fixture identity/data path.
- [ ] Exact-image PostgreSQL workflow passes on the final implementation head.
- [ ] Real authenticated Chromium API-mode journey passes on the final implementation head.
- [ ] Focused backend/deployment tests pass on the final implementation head.
- [ ] Required repository workflows pass on the exact final implementation head.
- [ ] Fresh independent audit reports zero material findings or all findings are repaired.
- [ ] PR review threads are resolved and no duplicate repair PR owns this Issue.
- [ ] Protected-target acceptance is reported separately and never inferred from CI.

## Validation evidence and repaired failures

Stale failures were used only as diagnostic evidence and were repaired rather than counted as acceptance:

- exact image missing `jsonschema`;
- exact image missing Feature Registry assets;
- exact image missing Strategy Lab assets;
- private-route introspection incompatibility;
- FastAPI readiness response-model inference;
- deployment test accidentally requiring the Synology Liquid20 host mount on GitHub-hosted CI;
- initial Chromium script location would not resolve workspace `@playwright/test`; the script now executes from the web workspace.

Final acceptance requires fresh exact-head results after these repairs.

## Recovery checkpoint

```yaml
policy_version: 1
generation: 2
session_id: 20260808T210000Z-owner-continuation
session_started_at: 2026-08-08T21:00:00Z
checkpointed_at: 2026-08-08T21:20:00Z
last_progress_at: 2026-08-08T21:20:00Z
phase: validation
exact_head_before_checkpoint_commit: 1ede0194fb102ebd384a28d0e61786c475739b35
pull_request: 1393
active_operation: GitHub Actions exact-head validation including real Chromium API-mode journey
external_run_ids: []
operation_started_at: null
wait_deadline_at: null
check_generation: implementation-browser-e2e-v1
checks_used: 0
status: active
safe_to_resume: true
resume_condition: current-head GitHub Actions exist or an actionable validation failure is available
next_action: Observe one aggregate current-head CI snapshot, repair the first actionable failure if any, then perform fresh independent audit when exact-head implementation and E2E gates are green.
```

## Context checkpoint

```yaml
checkpoint_version: 5
updated_at: 2026-08-08T21:20:00Z
status: validating
branch: repair/1089-portal-api-mode-deployment
base_head: c64df386a4fa3ba739b6eaa1a223ca798a7bcae2
head_before_checkpoint_commit: 1ede0194fb102ebd384a28d0e61786c475739b35
pr: 1393
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
  - Synology candidate uses private digest-pinned PostgreSQL plus authoritative migration/readiness
  - legacy SQLite and existing PostgreSQL state have explicit preservation/rollback contracts
  - non-protected exact-image PostgreSQL validation exists
  - real Chromium API-mode E2E workflow now exists with persisted identity, CSRF, backend read, dry-run mutation, refresh persistence and no request interception
unknown:
  - final exact-head CI outcome
  - final Chromium E2E outcome
  - independent audit result
  - protected Synology target acceptance outcome
conflicts:
  - PR 1388 owns control-plane API/schema/model paths; those paths remain untouched
blockers: []
next_action: Inspect one aggregate CI snapshot for the post-checkpoint head and repair the first actionable failure; if green, proceed to fresh independent audit and closeout evidence.
```
