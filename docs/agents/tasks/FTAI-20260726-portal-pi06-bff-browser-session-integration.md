---
task_id: FTAI-20260726-portal-pi06-bff-browser-session-integration
status: implementing
branch: feat/portal-pi06-bff-browser-session-integration
base_branch: develop
created: 2026-07-26
updated: 2026-07-26
related_pr: null
owned_paths:
  - ai_platform/portal/web/proxy.ts
  - ai_platform/portal/web/lib/identity.ts
  - ai_platform/portal/web/lib/client-fetch.ts
  - ai_platform/portal/web/app/api/identity/
  - ai_platform/portal/web/app/login/
  - ai_platform/portal/web/components/app-shell.tsx
  - ai_platform/portal/web/components/*form.tsx
  - ai_platform/portal/web/components/bot-lifecycle-controls.tsx
  - ai_platform/portal/web/e2e/identity-session.spec.ts
  - ai_platform/portal/web/playwright.config.ts
  - docs/ai_platform/portal/PI06_BFF_BROWSER_SESSION_INTEGRATION.md
  - docs/agents/tasks/FTAI-20260726-portal-pi06-bff-browser-session-integration.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/SECURITY_ARCHITECTURE.md
  - docs/ai_platform/portal/PI06_IDENTITY_AND_SESSION_DECISION.md
  - docs/ai_platform/portal/PI06_PRODUCT_IDENTITY_IMPLEMENTATION.md
  - docs/ai_platform/portal/NEXT_WORK_AND_REPAIR_PLAN.md
---

# PI-06 BFF Browser Session Integration

## Goal

Connect the same-origin Next.js portal boundary to the merged PI-06 identity backend without exposing IdP tokens, private control-plane addresses or credentials to browser code. Add deterministic browser acceptance for anonymous denial, authenticated session display, CSRF enforcement, MFA and step-up denial, expiry, revocation, logout-all and cross-tenant denial.

## Boundaries

- No Authentik, Synology, Cloudflare, DNS, Access, secret or user provisioning.
- No browser-readable IdP access, ID or refresh token.
- No direct browser call to the control-plane, Freqtrade, exchange or secret store.
- Proxy checks are optimistic only; authoritative session, tenant and capability enforcement remains in the identity-enabled control-plane.
- Fixture behavior is test-only, deterministic and unavailable outside fixture/test mode.
- No PI-05, PI-07, PI-08, P11 acceptance, P14 or live-capital behavior.
- Frozen thresholds, Phase 6 evidence and protected final holdout remain unchanged.

## Acceptance

1. Same-origin login and callback routes preserve redirects and forward backend session cookies without parsing or exposing IdP tokens.
2. Session, logout and logout-all routes proxy only through the server-side control-plane URL.
3. Unsafe same-origin requests require a readable CSRF cookie and matching `x-csrf-token`; the identity backend remains the authoritative verifier.
4. Anonymous protected page access redirects to login and anonymous protected API access fails with 401.
5. Fixture browser E2E deterministically covers authenticated, anonymous, CSRF-denied, MFA-denied, step-up-denied, expired, revoked, logout-all and cross-tenant-denied states.
6. Existing fixture product E2E remains green without adding public runtime or credential authority.
7. Typecheck, lint, production build, Chromium E2E, Portal Universal E2E, AI Platform CI, Freqtrade CI and security analysis pass on the exact final head.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-26T13:15:00+02:00
head: bef49bdf4d914c2aa363d99621cdb7b80fd16c9d
branch: feat/portal-pi06-bff-browser-session-integration
pr: null
status: implementing
context_routes:
  - docs/ai_platform/portal/PI06_IDENTITY_AND_SESSION_DECISION.md
  - docs/ai_platform/portal/PI06_PRODUCT_IDENTITY_IMPLEMENTATION.md
  - docs/ai_platform/portal/NEXT_WORK_AND_REPAIR_PLAN.md
owned_paths:
  - ai_platform/portal/web/proxy.ts
  - ai_platform/portal/web/lib/identity.ts
  - ai_platform/portal/web/lib/client-fetch.ts
  - ai_platform/portal/web/app/api/identity/
  - ai_platform/portal/web/app/login/
  - ai_platform/portal/web/components/app-shell.tsx
  - ai_platform/portal/web/components/*form.tsx
  - ai_platform/portal/web/components/bot-lifecycle-controls.tsx
  - ai_platform/portal/web/e2e/identity-session.spec.ts
  - ai_platform/portal/web/playwright.config.ts
  - docs/ai_platform/portal/PI06_BFF_BROWSER_SESSION_INTEGRATION.md
  - docs/agents/tasks/FTAI-20260726-portal-pi06-bff-browser-session-integration.md
proven:
  - develop head at declaration is bef49bdf4d914c2aa363d99621cdb7b80fd16c9d.
  - PR 341 merged the authoritative Python identity backend as 41834d18f3a05b0dfa44dc5af9b97942e685d2a1.
  - PR 359 merged the truthful PI-06 active-state closure as bef49bdf4d914c2aa363d99621cdb7b80fd16c9d.
  - Open PRs own RL-v2, liquidation research and inert design-reference paths; no open PR owns the declared web/BFF paths.
  - Next.js 16 uses proxy.ts for optimistic request-boundary checks; full authorization must still occur in route handlers and the backend.
derived:
  - The next reviewable package can connect the browser to the merged identity backend without provisioning a real IdP.
  - Fixture E2E can prove browser and BFF state handling while remaining explicitly non-production evidence.
unknown:
  - Exact final route and component names requiring CSRF client helper updates.
  - Exact repository CI findings after the bounded implementation is committed.
conflicts: []
first_failure: null
rejected_hypotheses:
  - Treat Cloudflare Access or page visibility as product authorization.
  - Store or expose IdP tokens in browser-readable storage.
  - Let Proxy perform authoritative database-backed authorization.
  - Provision real Authentik or Cloudflare resources in this package.
changed_paths:
  - docs/agents/tasks/FTAI-20260726-portal-pi06-bff-browser-session-integration.md
validation: []
blockers: []
next_action: Inspect current web mutation routes and client forms, implement the bounded same-origin identity boundary and deterministic fixture E2E, then run exact-head repository CI.
```
