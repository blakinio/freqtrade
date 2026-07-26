---
task_id: FTAI-20260726-portal-pi06-bff-browser-session-integration
status: reviewing
branch: feat/portal-pi06-bff-browser-session-integration
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
updated_at: 2026-07-26T13:55:00+02:00
head: 16ee08b3f58a35a78bd5e64ad3e56470e6d48e4b
branch: feat/portal-pi06-bff-browser-session-integration
pr: 361
status: reviewing
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
  - Open PRs at declaration owned RL-v2, liquidation research and inert design-reference paths; none owned the declared web/BFF paths.
  - Next.js Proxy performs only bounded cookie and CSRF checks; changed Route Handlers repeat the browser boundary and the identity-enabled control-plane remains authoritative.
  - Same-origin login and callback accept only safe relative application returns, and login accepts only an HTTPS authorization redirect produced by the private backend.
  - Browser code receives only opaque portal session and CSRF cookies; no IdP access, ID or refresh token is stored in browser-readable storage.
  - Fixture identity is available only when fixture data mode, test environment and explicit fixture identity mode are all enabled.
  - Candidate head 898e13b0fbc8c754e7028abf5ad1ff442563de40 passed Portal Web CI 285: typecheck, lint, production build and all 37 Chromium tests.
  - Earlier candidate head ba6b693502b36db7e153637642b58becdae4be39 passed AI Platform CI 1507 and GitHub Actions Security Analysis 1686.
derived:
  - The repository BFF and browser-session boundary is independently reviewable without provisioning a real IdP or external ingress.
  - Deterministic fixture E2E proves browser and BFF state handling but is not Authentik, recovery or P11 evidence.
unknown:
  - Exact final CI outcome after removing temporary Playwright diagnostics and writing this checkpoint.
  - Real Authentik, MFA enrollment, recovery, browser cookie and Cloudflare ingress behavior in the target Synology environment.
conflicts: []
first_failure:
  marker: LEGACY_DIRECT_API_TESTS_WITHOUT_SESSION
  evidence: The first Chromium run passed 34 of 37 tests. Two bot-operation contract tests and one liquidation read-only contract test called protected BFF routes through a fresh APIRequestContext without establishing a fixture session; they correctly received 401 instead of their intended domain responses. The tests were updated to establish the explicit fixture session, and unsafe bot requests now include the matching CSRF header. Portal Web CI 285 then passed all 37 tests.
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
  - command: Portal Web CI 285 on candidate head 898e13b0fbc8c754e7028abf5ad1ff442563de40
    result: PASS
    evidence: Typecheck, lint, production build and 37 Chromium tests passed; the temporary failure-evidence step was skipped.
  - command: AI Platform CI 1507 on initial implementation head ba6b693502b36db7e153637642b58becdae4be39
    result: PASS
    evidence: Full AI platform validation passed before test-only repair.
  - command: GitHub Actions Security Analysis 1686 on initial implementation head ba6b693502b36db7e153637642b58becdae4be39
    result: PASS
    evidence: Zizmor completed successfully.
blockers: []
next_action: Require Portal Web, Portal Universal E2E, AI Platform, Freqtrade and security CI to pass on the exact final head without temporary diagnostics, then mark PR 361 ready and squash-merge. Keep real Authentik/Synology and Cloudflare evidence in separate packages.
```
