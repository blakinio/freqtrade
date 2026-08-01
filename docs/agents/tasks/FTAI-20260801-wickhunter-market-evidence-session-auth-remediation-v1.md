---
task_id: FTAI-20260801-wickhunter-market-evidence-session-auth-remediation-v1
status: waiting
branch: fix/FTAI-20260801-wickhunter-market-evidence-session-auth-remediation-v1
base_branch: develop
base_sha: f1eb18095a728c14e1a27cd2b36352584245f917
task_kind: implementation
implementation_authorized: true
authorized_findings:
  - WH-ME-AUD-003
execution_mode: codex
related_pr: 947
---

# WickHunter Market Evidence session authorization remediation

Remediate only `WH-ME-AUD-003`: every Market Evidence API request must validate its opaque
Portal session through the authoritative identity backend and enforce the current tenant membership
and read permission. The boundary must fail closed without exposing session material.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-01T17:12:54+02:00
head: 9450a8bda4944bed2d72c5d5d2a96567eb39bafe
branch: fix/FTAI-20260801-wickhunter-market-evidence-session-auth-remediation-v1
pr: 947
status: validating
phase: complete
session_id: codex-20260801-wh-me-aud-003-1
session_role: implementer
execution_mode: codex
execution_reason: production-mode Next.js boundary reproduction and focused multi-file test/fix loop
implementation_authorized: true
base_sha: f1eb18095a728c14e1a27cd2b36352584245f917
policy_version: 2
task_kind: implementation
context_pressure: high
context_growth: stable
context_score: 11
decomposition_decision: split
decomposition_reason: audit findings have independent ownership, acceptance criteria, branches, and PRs
last_completed_step: committed and pushed coherent implementation head 9450a8bda4944bed2d72c5d5d2a96567eb39bafe and opened draft PR 947 against develop
context_routes:
  - docs/agents/tasks/FTAI-20260801-wickhunter-market-evidence-session-auth-remediation-v1.md
  - docs/agents/evidence/FTAI-20260801-wickhunter-backend-frontend-deployment-audit-v1/report.md at audit commit a9272b3e
first_failure:
  marker: WH-ME-AUD-003
  evidence: The pre-fix production-mode Next.js request returned 200 for an arbitrary opaque session cookie.
owned_paths:
  - docs/agents/tasks/FTAI-20260801-wickhunter-market-evidence-session-auth-remediation-v1.md
  - ai_platform/portal/web/lib/market-evidence/authorization.ts
  - ai_platform/portal/web/app/api/market/evidence/**
  - ai_platform/portal/web/e2e/market-evidence-production-auth.test.mjs
  - ai_platform/portal/web/package.json
  - .github/workflows/ai-platform-wickhunter-market-evidence-ci.yml
  - docs/ai_platform/portal/MARKET_EVIDENCE_READ_MODEL.md
validation_level: component
heavy_validation_runs: 1
proven:
  - Live develop is f1eb18095a728c14e1a27cd2b36352584245f917 and contains merged PR 938.
  - No local or remote remediation branch and no overlapping worktree existed before branch creation.
  - Open PR 946 changes Python OIDC and deployment diagnostics, not Task A owned web identity or Market Evidence paths.
  - The authoritative backend endpoint GET /v1/identity/session validates opaque session existence, expiry, revocation, principal status, active membership, and membership version.
  - The pre-fix real Next.js boundary returned 200 for an arbitrary production session cookie; the regression failed at forged 200 versus expected 401.
  - All four Market Evidence API route families now use one server-only guard that calls the private identity backend with a bounded timeout.
  - The guard requires the configured tenant and an analyst, model_reviewer, or admin role, matching the established audit.read mapping.
  - Production cannot activate fixture identity because fixtureIdentityMode also requires PORTAL_ENVIRONMENT=test.
derived:
  - The existing session endpoint is sufficient; no second session authority or Python identity contract change is required.
unknown: []
conflicts: []
rejected_hypotheses:
  - Cookie presence in the Next.js proxy is sufficient evidence of an authenticated session.
  - Fixture identity behavior proves production session authenticity.
changed_paths:
  - docs/agents/tasks/FTAI-20260801-wickhunter-market-evidence-session-auth-remediation-v1.md
  - ai_platform/portal/web/lib/market-evidence/authorization.ts
  - ai_platform/portal/web/app/api/market/evidence/_shared.ts
  - ai_platform/portal/web/app/api/market/evidence/summary/route.ts
  - ai_platform/portal/web/app/api/market/evidence/sources/route.ts
  - ai_platform/portal/web/app/api/market/evidence/instruments/route.ts
  - ai_platform/portal/web/app/api/market/evidence/runs/route.ts
  - ai_platform/portal/web/e2e/market-evidence-production-auth.test.mjs
  - ai_platform/portal/web/package.json
  - .github/workflows/ai-platform-wickhunter-market-evidence-ci.yml
  - docs/ai_platform/portal/MARKET_EVIDENCE_READ_MODEL.md
validation:
  - command: npm run test:market-evidence-auth before implementation
    result: FAIL
    evidence: expected pre-fix failure; real Next.js production-mode server returned 200 rather than 401 for a forged cookie
  - command: npm run test:market-evidence-auth after implementation
    result: PASS
    evidence: no-cookie, malformed, forged, expired, revoked, unknown, membership-version, tenant, permission, unavailable, timeout, malformed-response, fixture-production and all-route assertions passed
  - command: focused Playwright Market Evidence and identity-session specs
    result: PASS
    evidence: fixture identity and Market Evidence critical, security, pagination and cross-tenant browser coverage passed
  - command: npm run typecheck
    result: PASS
    evidence: TypeScript emitted no errors
  - command: npm run lint
    result: PASS
    evidence: zero errors; one pre-existing signal-wizard hook warning
  - command: npm run build
    result: PASS
    evidence: optimized Next.js production build completed and emitted all four Market Evidence routes
  - command: PR 947 exact-head required CI observation
    result: NOT_RUN
    evidence: workflow runs 30705418423, 30705418437, 30705418439, 30705418440, 30705418464, 30705418468 and 30705418481 queued for head 9450a8bda4944bed2d72c5d5d2a96567eb39bafe
blockers: []
next_action: Observe PR 947 required checks at the latest exact head and repair only a relevant failure.
```
