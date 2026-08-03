# FTAI-20260803 Portal Remediation — Issue 1124 (Archived)

```yaml
task_id: FTAI-20260803-portal-remediation-1124
programme_id: FTAI-20260803-portal-remediation
issue: 1124
repository: blakinio/freqtrade
lane: freqtrade-portal
task_kind: implementation
phase: closeout
status: completed
priority: high
prompting_standard_version: 2.1
execution_policy_version: 2
branch: fix/portal-1124-liquid20-session-authorization
base_branch: develop
base_head: 0a82a5c93613a213989865bd9128ac7263227148
validated_product_head: b5413489daa04b55b7167e3f291f2f919b195014
pr: 1146
ownership_released_on_merge: true
shared_path_leases: []
live_capital_authorized: false
withdrawals_enabled: false
protected_production_deployment_authorized: false
```

## Result

Liquid20 list, summary and health local-read endpoints now validate the allowlisted Portal session cookie through the authoritative PI-06 current-session endpoint before touching the mounted read model. The centralized server-only local-read authorization engine enforces current expiry, configured tenant and explicit human Portal roles, and fails closed for identity denial, timeout, malformed response and upstream failure. Market Evidence consumes the same engine with its existing stricter role policy.

## Changed paths

- `.github/workflows/portal-web.yml`
- `ai_platform/portal/web/lib/local-read-authorization.ts`
- `ai_platform/portal/web/lib/market-evidence/authorization.ts`
- `ai_platform/portal/web/app/api/market/liquidations/_shared.ts`
- `ai_platform/portal/web/app/api/market/liquidations/route.ts`
- `ai_platform/portal/web/app/api/market/liquidations/summary/route.ts`
- `ai_platform/portal/web/app/api/market/liquidations/health/route.ts`
- `ai_platform/portal/web/e2e/liquid20-production-auth.test.mjs`
- `ai_platform/portal/web/package.json`

## Acceptance evidence

- Missing and malformed cookies: safe `401` on every Liquid20 route.
- Forged, unknown, revoked, expired and membership-mismatch sessions: safe `401` on every route.
- Cross-tenant and unauthorized-service-role sessions: safe `403` on every route.
- Identity timeout, connection failure, malformed JSON and invalid session contract: fail-closed `503` on every route.
- Valid current human membership: list, summary and health return `200` with `no-store`.
- Only `__Host-portal_session` is forwarded; unrelated browser cookies are not forwarded.
- Fixture identity cookie cannot bypass the production-mode path.
- Static route inventory requires the authorization call in all three local-reader handlers.
- Market Evidence production session regression remains green after centralization.

## Exact-head validation

Validated product head: `b5413489daa04b55b7167e3f291f2f919b195014`.

- Portal Web CI `30806053844`: PASS, including typecheck, lint, production build, Market Evidence production auth, Liquid20 production auth and Chromium regression.
- Portal Universal E2E `30806053841`: PASS.
- AI Platform CI `30806053529`: PASS.
- AI Platform WickHunter Market Evidence CI `30806053638`: PASS, including production-mode session tests.
- Freqtrade CI `30806053451`: PASS.
- Portal Completeness Audit `30806053576`: PASS.
- AI Program Closure E2E `30806053447`: PASS.
- GitHub Actions Security Analysis `30806053473`: PASS.

The remaining closeout-only commits archive this task and update durable programme state. Required checks must pass again on the exact final PR head before merge.

## Fresh audit

Changed-path review found no material unresolved issue: authorization precedes every data read; identity failures are mapped before dataset failures; the helper forwards only the session allowlist, uses the existing bounded identity backend fetch with manual redirects and `no-store`, retains test-only fixture gating, and does not create the future shared BFF transport or canonical error-envelope authorities.

## Terminal checkpoint

```yaml
checkpoint_version: 2
updated_at: 2026-08-03T10:39:00Z
head: b5413489daa04b55b7167e3f291f2f919b195014
branch: fix/portal-1124-liquid20-session-authorization
pr: 1146
status: completed
proven:
  - the arbitrary-cookie Liquid20 bypass is removed from all three route handlers
  - authoritative current-session, expiry, tenant and role checks execute before local read-model access
  - production-mode security integration passes for all required positive and negative outcomes
  - exact-head repository, Portal, E2E, audit and security workflows pass
  - no secret/token value was logged or persisted
derived:
  - the task becomes visible as archived on develop only through merge of PR 1146
unknown: []
conflicts: []
blockers: []
next_action: Merge PR #1146 after exact-final-head checks remain green, verify Issue #1124 closes, then select Issue #1126.
```
