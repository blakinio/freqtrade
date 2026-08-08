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
pr: 1393
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
- The control-plane image starts `ai_platform.portal.identity.public_runtime:app`, whose previous app registered identity/session routes rather than the full canonical Portal router set.
- The same deploy writes a production SQLite URL even though public production startup requires PostgreSQL.
- `identity/http.py::create_identity_enabled_app()` already composes real identity-derived request context with `control_plane.api.create_app()` and CSRF middleware.
- The canonical control plane defaults privileged/external runtime providers to unavailable/fail-closed implementations; default bot-management composition has no Docker socket, exchange secret or direct Freqtrade mutation authority.
- Issue #1122 already delivered the versioned schema authority and migration CLI; this task consumes it rather than recreating schema ownership.
- Draft PR #1388 changes `control_plane/api.py` and schema/model paths. This task avoids those paths until that PR is resolved.

## Implemented slice on PR #1393

- `identity/public_runtime.py` now constructs the existing identity-enabled canonical Portal control plane rather than an identity-only app.
- Startup asserts a representative canonical product-router inventory including bots, operations, terminal, models, strategies, valuation and runtime-observability routes.
- Public API state is explicitly marked unprivileged; no live-capital authority is introduced.
- `/healthz` is a dependency-free liveness contract compatible with existing exact-image probes.
- `/readyz` verifies current schema readiness, a database transaction and the complete required router inventory; failure is a generic secret-free 503.
- The control-plane image healthcheck now targets `/readyz`.
- The web runtime defaults to `PORTAL_WEB_DATA_MODE=api` and its runtime entrypoint rejects fixture data mode, identity fixture mode or missing control-plane URL in staging/production.
- Focused source/deployment and runtime composition tests cover the new composition and fail-closed contracts.

## Scope still remaining

1. Replace the protected Synology deployer's production SQLite URL and fixture web wiring with a supported PostgreSQL + API-mode contract.
2. Run the versioned migration command explicitly before control-plane promotion and retain readiness as a startup/cutover gate.
3. Preserve existing authoritative identity/product state during the SQLite-to-PostgreSQL transition or refuse cutover until an explicit migration/restore path is completed; never silently reset state.
4. Prove exact deployment images together in API mode against the supported PostgreSQL topology.
5. Complete API-mode critical browser evidence, fresh independent audit, exact-head required CI, documentation/status reconciliation and protected-target acceptance separation.

## Non-goals / safety boundary

- No protected Synology deployment from this implementation branch.
- No live trading, withdrawals or live-capital authority.
- No Docker/container-engine socket or Freqtrade/exchange/Vault execution credential in the public API process.
- No change to the private runtime-supervisor authority owned by later runtime work.
- No fixture fallback in staging/production.
- No secret values in source, logs, reports or artifacts.

## Acceptance plan

- [x] Public runtime constructs the existing identity-enabled full canonical Portal API.
- [x] Identity/session and representative product routes are present in one app and require identity-derived tenant context.
- [x] `/healthz` is liveness-only and `/readyz` proves database/schema/router composition without exposing secrets.
- [x] Production/staging web startup rejects fixture mode and requires a server-side control-plane URL.
- [ ] Synology deployment uses API mode and a supported PostgreSQL topology, applies versioned migration explicitly, and fails closed before cutover on migration/readiness failure.
- [x] Deployment image/process contract keeps public API unprivileged and private providers server-side.
- [ ] Exact deployment images boot together in API mode against PostgreSQL in non-protected CI evidence.
- [ ] Focused backend/deployment tests pass on the final implementation head.
- [ ] Required repository workflows pass on the exact final implementation head.
- [ ] Fresh independent audit reports zero material findings or all findings are repaired.
- [ ] PR review threads are resolved and no duplicate repair PR owns this Issue.
- [ ] Protected-target acceptance is reported separately and never inferred from CI.

## Context checkpoint

```yaml
checkpoint_version: 3
updated_at: 2026-08-08T20:02:00Z
status: active
branch: repair/1089-portal-api-mode-deployment
base_head: c64df386a4fa3ba739b6eaa1a223ca798a7bcae2
source_head_before_checkpoint: 0a0ef4eb03138ff72122e7402a366808a850fd71
pr: 1393
proven:
  - issue 1089 is claimed by ftai-1089-20260808T194400Z-gpt56sol
  - draft implementation PR 1393 exists and is linked to issue 1089
  - public runtime now composes identity with the canonical product control plane
  - staging/production web runtime now fails closed unless API mode and a control-plane URL are selected
  - control-plane container readiness is distinct from liveness and verifies schema/database/router composition
  - current exact-image workflow already launches the two images together in API mode for staging evidence
unknown:
  - final CI outcome after the current source changes
  - protected Synology target acceptance outcome
conflicts:
  - PR 1388 owns control-plane API/schema/model paths; those paths remain untouched by this repair
blockers:
  - canonical Synology deploy.py still selects production SQLite and fixture web mode, so PR 1393 must remain draft until that wiring and state-transition contract are repaired
next_action: Repair the canonical Synology deployer to require/preserve supported PostgreSQL state, run versioned migration before promotion, select API web mode and reject any unsafe legacy-state cutover; then run exact-head CI and independent audit.
```
