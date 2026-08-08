# FTAI-20260808 Portal Remediation — Issue 1089

```yaml
task_id: FTAI-20260808-portal-remediation-1089
programme_id: FTAI-20260803-portal-remediation
issue: 1089
repository: blakinio/freqtrade
lane: freqtrade-portal
task_kind: implementation
phase: implementation
status: active
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
pr: pending
owned_paths:
  - ai_platform/portal/identity/public_runtime.py
  - ai_platform/portal/web/lib/portal-api.ts
  - deploy/synology/portal/Dockerfile
  - deploy/synology/portal-oidc/Dockerfile.control-plane
  - deploy/synology/portal-oidc/control-plane-entrypoint.sh
  - deploy/synology/portal-oidc/deploy.py
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

Repair Issue #1089 without inventing a second Portal architecture. Reuse `identity/http.py::create_identity_enabled_app()` as the authenticated composition seam around the canonical control plane, keep the public API process unprivileged, run the web tier in API mode for staging/production, and make database/schema/readiness failures fail closed before traffic acceptance.

## Verified starting state

- Synology OIDC deploy sets `PORTAL_WEB_DATA_MODE=fixture` while declaring `PORTAL_ENVIRONMENT=production`.
- The control-plane image starts `ai_platform.portal.identity.public_runtime:app`, whose current app registers identity/session routes rather than the full canonical Portal router set.
- The same deploy writes a production SQLite URL even though current public production startup rejects non-PostgreSQL databases.
- `identity/http.py::create_identity_enabled_app()` already composes real identity-derived request context with `control_plane.api.create_app()` and CSRF middleware.
- The canonical control plane defaults privileged/external runtime providers to unavailable/fail-closed implementations; default bot-management composition has no Docker socket, exchange secret or direct Freqtrade mutation authority.
- Issue #1122 already delivered the versioned schema authority and migration CLI; this task must consume it rather than recreate schema ownership.
- Draft PR #1388 currently changes `control_plane/api.py` and schema/model paths. This task will avoid those paths until that PR is resolved.

## Scope

1. Full authenticated public API composition and explicit liveness/readiness semantics.
2. Web API-mode production/staging startup contract; fixture mode must fail closed there.
3. Synology deployment contract aligned to PostgreSQL plus explicit migration/readiness gate.
4. Exact-image/deployment tests proving the selected entry point, API mode, router inventory, database dialect/revision and hardening.
5. Documentation/status evidence only after implementation and tests establish the facts.

## Non-goals / safety boundary

- No protected Synology deployment from this implementation branch.
- No live trading, withdrawals or live-capital authority.
- No Docker/container-engine socket or Freqtrade/exchange/Vault execution credential in the public API process.
- No change to the private runtime-supervisor authority owned by later runtime work.
- No fixture fallback in staging/production.
- No secret values in source, logs, reports or artifacts.

## Acceptance plan

- [ ] Public runtime constructs the existing identity-enabled full canonical Portal API.
- [ ] Identity/session and representative product routes are present in one app and require identity-derived tenant context.
- [ ] `/healthz` is liveness-only and `/readyz` proves database/schema/router composition without exposing secrets.
- [ ] Production/staging web startup rejects fixture mode and requires a same-origin server-side control-plane URL.
- [ ] Synology deployment uses API mode and a supported PostgreSQL topology, applies versioned migration explicitly, and fails closed before cutover on migration/readiness failure.
- [ ] Deployment keeps public API unprivileged and private providers server-side.
- [ ] Exact deployment images boot together in API mode against PostgreSQL in non-protected CI evidence.
- [ ] Focused backend/deployment tests pass.
- [ ] Required repository workflows pass on the exact implementation head.
- [ ] Fresh independent audit reports zero material findings or all findings are repaired.
- [ ] PR review threads are resolved and no duplicate repair PR owns this Issue.
- [ ] Protected-target acceptance is reported separately and never inferred from CI.

## Context checkpoint

```yaml
checkpoint_version: 3
updated_at: 2026-08-08T19:44:00Z
status: active
branch: repair/1089-portal-api-mode-deployment
base_head: c64df386a4fa3ba739b6eaa1a223ca798a7bcae2
head: c64df386a4fa3ba739b6eaa1a223ca798a7bcae2
pr: pending
proven:
  - issue 1089 remains open and has no implementation PR or 1089-named branch
  - current deploy selects fixture web mode in production
  - current public runtime is identity-only while identity/http.py already provides the full authenticated composition seam
  - current deploy production SQLite URL conflicts with the current production PostgreSQL startup requirement
  - PR 1388 overlaps canonical control-plane API/schema paths, so this task excludes those paths
unknown:
  - final exact-image CI outcome after implementation
  - protected Synology target acceptance outcome
conflicts:
  - PR 1388 owns control-plane API/schema/model paths; avoided by path ownership
blockers: []
next_action: Implement the authenticated public composition and fail-closed API-mode startup contract on the claimed paths, then open the dedicated draft repair PR for exact-head CI.
```
