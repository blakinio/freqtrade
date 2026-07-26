---
task_id: FTAI-20260726-portal-pi06-bff-browser-session-integration
status: done
branch: develop
base_branch: develop
created: 2026-07-26
updated: 2026-07-26
related_pr: 361
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
updated_at: 2026-07-26T14:02:00+02:00
head: 4f76eecadcb8dda964a8d247327db9dc6ef1c931
branch: develop
pr: 361
status: done
context_routes:
  - docs/ai_platform/portal/PI06_IDENTITY_AND_SESSION_DECISION.md
  - docs/ai_platform/portal/PI06_PRODUCT_IDENTITY_IMPLEMENTATION.md
  - docs/ai_platform/portal/PI06_BFF_BROWSER_SESSION_INTEGRATION.md
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
  - develop head at declaration was bef49bdf4d914c2aa363d99621cdb7b80fd16c9d.
  - PR 341 merged the authoritative Python identity backend as 41834d18f3a05b0dfa44dc5af9b97942e685d2a1.
  - PR 359 merged the truthful PI-06 active-state closure as bef49bdf4d914c2aa363d99621cdb7b80fd16c9d.
  - PR 361 squash-merged the bounded same-origin BFF/browser-session package as 4f76eecadcb8dda964a8d247327db9dc6ef1c931.
  - Next.js Proxy performs only bounded cookie and CSRF checks; changed Route Handlers repeat the browser boundary and the identity-enabled control-plane remains authoritative.
  - Same-origin login and callback accept only safe relative application returns, and login accepts only an HTTPS authorization redirect produced by the private backend.
  - Browser code receives only opaque portal session and CSRF cookies; no IdP access, ID or refresh token is stored in browser-readable storage.
  - Fixture identity is available only when fixture data mode, test environment and explicit fixture identity mode are all enabled.
  - Exact final implementation head ec1970a9272bec241a1bab3c447ebd36f53afa58 passed Portal Web CI 287, Portal Universal E2E 292, AI Platform CI 1521, Freqtrade CI 1837 and GitHub Actions Security Analysis 1702.
  - Portal Web CI 287 passed typecheck, lint, production build and all 37 Chromium tests without a diagnostic workflow in the final diff.
derived:
  - The repository backend and same-origin browser boundary are complete bounded PI-06 subpackages.
  - PI-06 remains active because real Authentik/Synology deployment, MFA enrollment, recovery, backup/restore and target-environment acceptance are not repository browser evidence.
unknown:
  - Real Authentik, MFA enrollment, recovery, browser cookie and Cloudflare ingress behavior in the target Synology environment.
conflicts: []
first_failure:
  marker: LEGACY_DIRECT_API_TESTS_WITHOUT_SESSION
  evidence: The first Chromium run passed 34 of 37 tests. Two bot-operation contract tests and one liquidation read-only contract test called protected BFF routes through a fresh APIRequestContext without establishing a fixture session; they correctly received 401 instead of their intended domain responses. The tests were updated to establish the explicit fixture session, and unsafe bot requests now include the matching CSRF header. Portal Web CI 285 then passed all 37 tests, and the exact final head passed Portal Web CI 287.
rejected_hypotheses:
  - Treat Cloudflare Access or page visibility as product authorization.
  - Store or expose IdP tokens in browser-readable storage.
  - Let Proxy perform authoritative database-backed authorization.
  - Provision real Authentik or Cloudflare resources in this package.
  - Keep the temporary Playwright output/artifact workflow in the final diff.
changed_paths:
  - ai_platform/portal/web/app/api/bots/[botId]/desired-state/route.ts
  - ai_platform/portal/web/app/api/bots/[botId]/revisions/route.ts
  - ai_platform/portal/web/app/api/bots/route.ts
  - ai_platform/portal/web/app/api/grid-bots/route.ts
  - ai_platform/portal/web/app/api/identity/callback/route.ts
  - ai_platform/portal/web/app/api/identity/fixture-state/route.ts
  - ai_platform/portal/web/app/api/identity/login/route.ts
  - ai_platform/portal/web/app/api/identity/logout-all/route.ts
  - ai_platform/portal/web/app/api/identity/logout/route.ts
  - ai_platform/portal/web/app/api/identity/session/route.ts
  - ai_platform/portal/web/app/api/notifications/preferences/route.ts
  - ai_platform/portal/web/app/api/signals/route.ts
  - ai_platform/portal/web/app/api/terminal/route.ts
  - ai_platform/portal/web/app/login/page.tsx
  - ai_platform/portal/web/components/app-shell.tsx
  - ai_platform/portal/web/components/bot-lifecycle-controls.tsx
  - ai_platform/portal/web/components/bot-revision-form.tsx
  - ai_platform/portal/web/components/create-bot-form.tsx
  - ai_platform/portal/web/components/grid-bot-form.tsx
  - ai_platform/portal/web/components/notification-preferences-form.tsx
  - ai_platform/portal/web/components/session-controls.tsx
  - ai_platform/portal/web/components/signal-wizard-form.tsx
  - ai_platform/portal/web/components/terminal-form.tsx
  - ai_platform/portal/web/e2e/bot-operations.spec.ts
  - ai_platform/portal/web/e2e/identity-session.spec.ts
  - ai_platform/portal/web/e2e/liquidations.spec.ts
  - ai_platform/portal/web/e2e/shell.spec.ts
  - ai_platform/portal/web/lib/client-fetch.ts
  - ai_platform/portal/web/lib/identity.ts
  - ai_platform/portal/web/playwright.config.ts
  - ai_platform/portal/web/proxy.ts
  - docs/agents/tasks/FTAI-20260726-portal-pi06-bff-browser-session-integration.md
  - docs/ai_platform/portal/PI06_BFF_BROWSER_SESSION_INTEGRATION.md
validation:
  - command: Portal Web CI 287 on exact final head ec1970a9272bec241a1bab3c447ebd36f53afa58
    result: PASS
    evidence: Typecheck, lint, production build and all 37 Chromium tests passed.
  - command: Portal Universal E2E 292 on exact final head ec1970a9272bec241a1bab3c447ebd36f53afa58
    result: PASS
    evidence: Universal fixture browser workflow completed successfully.
  - command: AI Platform CI 1521 on exact final head ec1970a9272bec241a1bab3c447ebd36f53afa58
    result: PASS
    evidence: Full AI tests, Ruff, Ruff format, codespell and JSON validation passed.
  - command: Freqtrade CI 1837 on exact final head ec1970a9272bec241a1bab3c447ebd36f53afa58
    result: PASS
    evidence: Required repository CI gate completed successfully.
  - command: GitHub Actions Security Analysis 1702 on exact final head ec1970a9272bec241a1bab3c447ebd36f53afa58
    result: PASS
    evidence: Zizmor completed successfully.
blockers: []
next_action: Declare a separate Authentik/Synology deployment package after a fresh develop and path-ownership preflight. Pin container images, use runtime-injected secret placeholders, restrict bootstrap, add backup/restore and recovery runbooks, and prove real login, MFA, logout, revocation and recovery only against owner-managed target resources. Keep Cloudflare P11 acceptance, PI-07, PI-08 and live capital separate.
```
