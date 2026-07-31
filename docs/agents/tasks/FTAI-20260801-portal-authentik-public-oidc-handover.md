---
task_id: FTAI-20260801-portal-authentik-public-oidc-handover
status: ready
branch: feat/portal-authentik-public-oidc-20260801
base_branch: develop
created: 2026-08-01
updated: 2026-08-01
parent_task: FTAI-20260731-portal-local-authentik-oidc-integration
related_pr: 876
owned_paths:
  - .github/workflows/portal-oidc-local-test-deploy.yml
  - .github/workflows/portal-synology-lan-preview.yml
  - ai_platform/portal/identity/local_test_runtime.py
  - ai_platform/portal/identity/oidc.py
  - ai_platform/portal/identity/runtime.py
  - ai_platform/portal/web/lib/identity.ts
  - deploy/synology/portal/Dockerfile
  - deploy/synology/portal/deploy-preview.sh
  - deploy/synology/portal-oidc/
  - tests/ai_platform/portal/identity/test_oidc.py
  - tests/ai_platform/portal/deployment/test_portal_oidc_local_deploy.py
  - docs/agents/tasks/FTAI-20260801-portal-authentik-public-oidc-handover.md
required_reads:
  - docs/ai_platform/portal/ARCHITECTURE_DECISIONS.md
  - docs/agents/tasks/FTAI-20260731-portal-local-authentik-oidc-integration.md from PR 876
search_first:
  - current develop head
  - PR 876 exact head, diff, review state and failed workflow logs
  - Authentik public OIDC discovery for the actual provider slug
---

# Portal Authentik public OIDC handover

## Goal

Complete real Portal authentication through the existing Synology Authentik deployment using public Cloudflare Tunnel HTTPS origins, portal-owned sessions and OIDC Authorization Code plus PKCE.

Required terminal browser flow:

```text
https://quant.molehill.cloud
  -> https://auth.molehill.cloud
  -> password plus Authentik TOTP/MFA
  -> https://quant.molehill.cloud/api/identity/callback
  -> authenticated Portal session
```

## Frozen public contract

```text
Portal origin: https://quant.molehill.cloud
Authentik origin: https://auth.molehill.cloud
Portal callback: https://quant.molehill.cloud/api/identity/callback
Scopes: openid profile email
External principal identity: exact OIDC iss + sub
```

Do not use the retired `auth.quant.molehill.cloud` hostname. Resolve the provider slug from the deployed provider and its discovery document; do not infer it from a repository filename.

## Verified infrastructure state

- Authentik 2026.5.5 server, worker and PostgreSQL are deployed on Synology.
- Runtime secrets are target-generated and stored only on Synology in a persistent `runtime.env` with mode `0600`.
- PostgreSQL has no host-published port.
- Authentik readiness repair PR 862 merged as `6ac747a069455ddfbfa00d861008dd81fbf509cf`.
- Request-only rerun PR 865 was consumed and closed without merge.
- Previously recorded deployment run: `30625762233`.
- Previously recorded artifact: `portal-authentik-local-test-deploy-865`.
- The owner completed `akadmin` setup and TOTP/MFA enrollment.
- The owner verified that the Authentik authentication flow renders over valid HTTPS at `auth.molehill.cloud`.
- Cloudflare Tunnel routes:

```text
https://quant.molehill.cloud -> http://192.168.1.2:3031
https://auth.molehill.cloud  -> http://192.168.1.2:9000
```

Browser reachability does not prove that the Synology identity container can complete public discovery, JWKS and token exchange. Verify container egress and Cloudflare hairpin behavior.

## Repository checkpoint

At handover creation:

```text
develop: 04404b14c05586e6452ab5d9ce26920822412ed9
PR 876 branch: feat/portal-local-authentik-oidc-20260731
PR 876 head: 23bf942330af0f6ce3c09c4526905058a8161449
PR 876 state: open, not mergeable
PR 876 divergence before this handover: 18 ahead, 26 behind develop
merge base: 1060dec433a7e9d72e53ccddb6d76fe93842b187
```

Freeze both heads again before mutation because these values are checkpoint evidence only.

PR 876 already contains most required implementation:

- idempotent Authentik OIDC blueprint;
- confidential client and target-owned secret preservation;
- discovery, JWKS and claims validation;
- Authorization Code plus PKCE, state and nonce;
- Next.js BFF callback;
- internal Python identity/session service;
- Portal-owned sessions;
- fixture identity disablement;
- Synology deployment workflow and focused tests.

Its contract is obsolete because it targets LAN HTTP:

```text
Portal: http://192.168.1.2:3031
Authentik: http://192.168.1.2:9000
Issuer: http://192.168.1.2:9000/application/o/freqtrade-portal-local/
```

Adapt it to public HTTPS; do not deploy it unchanged.

## Last known PR 876 CI

```text
Security Analysis: success, run 30648432363
Portal Web CI: success, run 30648432355
Portal Universal E2E: success, run 30648432447
AI Platform CI: failure, run 30648432349
Freqtrade CI: failure, run 30648432361
```

Fetch current exact-head logs and repair the first real failures. Do not assume their cause from this checkpoint.

## Architecture and security invariants

- Authentik remains the identity provider and owns password, recovery and TOTP/MFA.
- Portal must not implement or store a separate TOTP secret.
- Use OIDC Authorization Code plus PKCE with a confidential server-side client.
- Next.js remains the browser BFF.
- The internal Python service terminates OIDC, validates claims and owns Portal sessions.
- OAuth access, refresh and ID tokens must not be exposed to browser JavaScript.
- Portal persistence remains authoritative for principals, memberships, roles and sessions.
- External identity is keyed only by exact `iss + sub`.
- Email, domain and group claims must not silently grant the first membership or admin role.
- The first membership requires an explicit, bounded and audited target-side bootstrap.
- Public runtime transport is HTTPS only.
- Portal session cookie remains Secure, HttpOnly, SameSite=Lax, Path=/, without Domain, and uses the `__Host-portal_session` name.
- Apply equivalent secure treatment to the CSRF cookie.
- `local_http_test` may remain only as a fail-closed test-only capability; it must not be the public deployment mode.
- Do not put Cloudflare Access in front of the whole Authentik hostname before OIDC acceptance.
- Do not create router port forwarding.

## Execution plan

1. Freeze current `develop`, PR 876 head, full diff, workflow results and review threads.
2. Choose between safely refreshing PR 876 and creating a clean replacement branch from current `develop`.
3. Prefer a clean replacement when conflict resolution could obscure or revert newer Portal work.
4. If replaced, declare that it supersedes PR 876 and close PR 876 without merge only after equivalent functionality and tests exist.
5. Configure:

```text
PORTAL_EXTERNAL_URL=https://quant.molehill.cloud
PORTAL_IDENTITY_REDIRECT_URI=https://quant.molehill.cloud/api/identity/callback
PORTAL_IDENTITY_ISSUER=https://auth.molehill.cloud/application/o/<actual-provider-slug>/
```

6. Verify discovery returns the same exact HTTPS issuer and public authorization, token and JWKS endpoints.
7. Keep the Authentik blueprint idempotent and preserve the target-generated client secret without printing or rotating it unnecessarily.
8. Verify browser-to-Portal, BFF-to-identity-service and identity-service-to-public-Authentik paths.
9. Keep the control-plane port internal and prohibit Docker socket, privileged mode and host networking.
10. Inspect `.github/workflows/portal-synology-lan-preview.yml` and `deploy/synology/portal/deploy-preview.sh` so no later workflow overwrites TCP 3031 or re-enables fixture identity.
11. Add or retain tests for issuer, discovery, JWKS, PKCE, state, nonce, redirect rejection, Secure cookies, CSRF, logout, no browser tokens, blueprint idempotency, secret preservation and fixture disablement.
12. Require all applicable exact-head checks to pass and merge with `expected_head_sha`.
13. After merge, create one separate request-only PR containing exactly one frozen deployment request file.
14. Deploy only through GitHub Environment `synology-staging` and trusted runner `freqtrade-staging`.
15. Preserve protected runtime env, secrets and persistent Authentik/PostgreSQL volumes.
16. Produce a secret-free always-uploaded report and close the request PR without merge.
17. Complete browser login, exact-principal membership bootstrap, authenticated Portal access and logout acceptance.

## Safety boundary

This task does not authorize live capital, production trading, real exchange orders, withdrawals, exchange credentials in GitHub, destructive restore, database host publication, Docker socket access, privileged containers, host networking or an unauthenticated public Portal terminal state.

Any Freqtrade runtime touched by this work must remain `dry_run` and receive no order authority.

## Terminal acceptance

Completion requires proof that:

1. `auth.molehill.cloud` remains healthy.
2. `quant.molehill.cloud` redirects an unauthenticated browser to Authentik.
3. Password plus Authentik TOTP/MFA succeeds.
4. The callback returns to the exact public Portal callback.
5. Portal creates its own secure session.
6. Fixture identity is disabled.
7. Missing membership fails closed.
8. A one-time audited exact-principal bootstrap grants the intended membership.
9. The authenticated user can open the Portal.
10. Logout invalidates the Portal session.
11. Required exact-head CI is green.
12. Trusted-runner deployment evidence is captured.
13. No workflow later restores fixture mode.
14. No secret value is recorded.
15. No live-capital authority is granted.

The terminal report must record implementation and request PRs, exact head and merge SHAs, workflow and deployment run IDs, artifact identity and digest, container health, public endpoint results, fixture disablement, browser acceptance and membership bootstrap evidence, plus these exact lines:

```text
secret_values_recorded=false
live_capital_authorized=false
```

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-01T00:28:00+02:00
head: 04404b14c05586e6452ab5d9ce26920822412ed9
branch: docs/portal-authentik-public-oidc-handover-20260801
pr: "#895"
status: ready
proven:
  - Authentik server, worker and PostgreSQL are deployed with persistent target-owned secrets.
  - Authentik login renders over valid HTTPS at auth.molehill.cloud through Cloudflare Tunnel.
  - Portal public hostname is quant.molehill.cloud and its BFF callback is /api/identity/callback.
  - PR 876 contains most OIDC and Portal session implementation but uses obsolete LAN HTTP origins.
derived:
  - Reusing the nearly complete Authentik integration is safer than replacing it with new Portal-local password and TOTP code.
  - Public HTTPS removes the need to deploy local_http_test mode.
  - A clean replacement branch may be safer than merging a heavily diverged PR 876 branch.
unknown:
  - Current provider slug and public discovery output.
  - Current causes of PR 876 CI failures.
  - Synology container public-issuer hairpin behavior.
  - Exact first principal iss and sub for membership bootstrap.
conflicts: []
first_failure:
  marker: PORTAL_OIDC_PUBLIC_HTTPS_NOT_DEPLOYED
  evidence: Authentik public ingress works, but Portal lacks a merged and deployed public-HTTPS OIDC integration.
rejected_hypotheses:
  - Replace Authentik with new Portal-local authentication.
  - Deploy PR 876 unchanged.
  - Use auth.quant.molehill.cloud.
  - Auto-promote the first matching email to administrator.
validation: []
blockers:
  - Reconcile PR 876 with current develop and public HTTPS.
  - Diagnose and repair exact-head CI failures.
  - Complete trusted-runner deployment and browser acceptance.
next_action: Freeze current develop and PR 876, implement or replace PR 876 for quant.molehill.cloud plus auth.molehill.cloud, obtain exact-head green CI, merge with expected_head_sha, execute one request-only Synology deployment and complete browser acceptance without recording secrets or authorizing live capital.
```
