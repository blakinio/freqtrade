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
  - Authentik public OIDC discovery document for the actual provider slug
---

# Portal Authentik public OIDC handover

## Goal

Complete real Portal authentication through the existing Synology Authentik deployment using public Cloudflare Tunnel HTTPS origins, portal-owned sessions and the existing OIDC Authorization Code plus PKCE architecture.

The terminal browser flow must be:

```text
https://quant.molehill.cloud
  -> https://auth.molehill.cloud
  -> password and Authentik TOTP/MFA
  -> https://quant.molehill.cloud/api/identity/callback
  -> authenticated Portal session
```

## Current external contract

```text
Portal public origin: https://quant.molehill.cloud
Authentik public origin: https://auth.molehill.cloud
Portal callback: https://quant.molehill.cloud/api/identity/callback
Scopes: openid profile email
External principal key: exact OIDC iss + sub
```

The retired hostname `auth.quant.molehill.cloud` must not be used. The owner moved Authentik to `auth.molehill.cloud` because Cloudflare Universal SSL did not cover the deeper hostname.

The actual provider slug is not frozen by this handover. Resolve it from the deployed Authentik provider and its discovery document. Never guess it from a filename.

## Verified infrastructure state

- Authentik 2026.5.5 server, worker and PostgreSQL are already deployed on Synology.
- Runtime secrets are target-generated and stored only on Synology in the protected persistent `runtime.env` with mode `0600`.
- PostgreSQL has no host-published port.
- The Authentik readiness repair merged in PR 862 as `6ac747a069455ddfbfa00d861008dd81fbf509cf`.
- Exact-one-file rerun request PR 865 was consumed and closed without merge.
- Previously recorded successful deployment run: `30625762233`.
- Previously recorded artifact name: `portal-authentik-local-test-deploy-865`.
- The owner completed `akadmin` setup and TOTP/MFA enrollment.
- The owner verified that `https://auth.molehill.cloud/if/flow/default-authentication-flow/` renders the Authentik login page over valid HTTPS.
- Cloudflare Tunnel currently routes:

```text
https://quant.molehill.cloud -> http://192.168.1.2:3031
https://auth.molehill.cloud  -> http://192.168.1.2:9000
```

Browser reachability is not proof that a Synology container can complete public discovery, JWKS and token exchange. Verify container egress and hairpin routing explicitly.

## Repository checkpoint

At creation of this handover:

```text
develop: 4660b1eb19b2c09af21f46cab2916b64dec7bfaf
PR 876 branch: feat/portal-local-authentik-oidc-20260731
PR 876 head: 23bf942330af0f6ce3c09c4526905058a8161449
PR 876 state: open, not mergeable
PR 876 divergence: 18 commits ahead and 26 commits behind develop
merge base: 1060dec433a7e9d72e53ccddb6d76fe93842b187
```

These values are evidence of the handover point only. Freeze the current `develop` and PR head again before any mutation.

PR 876 currently changes 13 paths and implements:

- an idempotent Authentik OIDC blueprint;
- confidential client handling with target-owned secret preservation;
- OIDC discovery, JWKS and claim validation;
- Authorization Code plus PKCE, state and nonce;
- a Next.js BFF callback;
- an internal Python identity/session service;
- portal-owned sessions;
- fixture identity disablement;
- a Synology deployment workflow and focused tests.

Its frozen product contract is obsolete because it targets LAN HTTP:

```text
Portal: http://192.168.1.2:3031
Authentik: http://192.168.1.2:9000
Issuer: http://192.168.1.2:9000/application/o/freqtrade-portal-local/
```

The implementation must be adapted to public HTTPS rather than deployed unchanged.

## Last known exact-head CI for PR 876

```text
GitHub Actions Security Analysis: success, run 30648432363
Portal Web CI: success, run 30648432355
Portal Universal E2E: success, run 30648432447
AI Platform CI: failure, run 30648432349
Freqtrade CI: failure, run 30648432361
```

Do not infer the current failure cause from this checkpoint. Fetch exact-head logs and repair the first real failures.

## Frozen architecture and security decisions

- Authentik remains the external identity provider.
- Portal must not implement or store its own TOTP secret.
- Flow is OIDC Authorization Code plus PKCE with a confidential server-side client.
- Next.js remains the browser BFF.
- The internal Python identity service terminates OIDC, validates claims and owns Portal sessions.
- OAuth access, refresh and ID tokens must not be exposed to browser JavaScript.
- Portal persistence remains authoritative for principals, memberships, roles and sessions.
- External identity is keyed only by exact `iss + sub`.
- Email, domain and Authentik group claims must not silently grant the first Portal membership or admin role.
- The first membership requires an explicit, bounded and audited bootstrap.
- Normal public transport is HTTPS only.
- Standard session cookie remains:

```text
__Host-portal_session
Secure
HttpOnly
SameSite=Lax
Path=/
no Domain attribute
```

- Apply equivalent secure handling to the CSRF cookie according to the existing identity design.
- The narrow `local_http_test` mode may remain only as a fail-closed test-only capability if still useful. It must not be the mode deployed at the public origins.
- Do not add Cloudflare Access in front of the whole Authentik hostname during initial OIDC acceptance; it can block discovery, callback or token exchange.
- Do not create router port forwarding.

## Implementation plan

### 1. Freeze and reconcile

1. Fetch the current `develop` SHA.
2. Fetch PR 876 metadata, full diff, current workflow results and review threads.
3. Decide between safely refreshing PR 876 or replacing it with a clean branch from current `develop`.
4. Prefer a clean replacement PR when conflict resolution would obscure or accidentally revert newer Portal work.
5. If replaced, state that the new PR supersedes 876 and close 876 without merge only after equivalent functionality and tests are present.

### 2. Replace the LAN runtime contract

Configure the deployed runtime for:

```text
PORTAL_EXTERNAL_URL=https://quant.molehill.cloud
PORTAL_IDENTITY_REDIRECT_URI=https://quant.molehill.cloud/api/identity/callback
PORTAL_IDENTITY_ISSUER=https://auth.molehill.cloud/application/o/<actual-provider-slug>/
```

The discovery document must report the same exact HTTPS issuer. Validate that authorization, token and JWKS endpoints also use `auth.molehill.cloud`.

### 3. Authentik blueprint

Keep the blueprint idempotent. It must create or update:

- one Portal Application;
- one OAuth2/OIDC Provider;
- a confidential client;
- preserved target-generated client credentials;
- the exact public callback;
- `openid profile email` scopes;
- active-user access policy;
- the existing Authentik authentication flow with enrolled TOTP/MFA.

Do not rotate or print the existing client secret unless rotation is strictly required and explicitly evidenced. No secret value may enter GitHub, Actions logs, PR text or artifacts.

### 4. Runtime topology

Verify:

- browser to public Portal HTTPS;
- Portal BFF to the internal identity service;
- identity service to public Authentik discovery, token and JWKS endpoints;
- forwarded host and scheme behavior through Cloudflare Tunnel;
- no host-published control-plane port;
- no Docker socket, privileged mode or host networking;
- fixture identity disabled in the deployed Portal.

### 5. Prevent fixture redeployment

Inspect `.github/workflows/portal-synology-lan-preview.yml` and `deploy/synology/portal/deploy-preview.sh` before merge.

A normal develop-triggered preview deployment must not later overwrite the OIDC deployment on TCP 3031 or re-enable fixture identity. Establish one canonical deployment contract or make the modes and triggers mutually exclusive.

### 6. Test and merge gates

Required coverage includes:

- exact issuer validation;
- HTTPS discovery and JWKS;
- Authorization Code plus PKCE;
- state and nonce validation;
- bad issuer and bad redirect rejection;
- Secure `__Host-*` cookie invariants;
- CSRF enforcement;
- logout and logout-all;
- no browser-visible OAuth tokens;
- fixture identity disabled;
- blueprint idempotency;
- client secret preservation;
- secret-free reports;
- Compose/render checks;
- no competing fixture deployment.

All required checks must be green at the exact implementation head before merge. Merge with `expected_head_sha`.

### 7. Trusted Synology deployment

After implementation merge:

1. Create a separate request-only PR containing exactly one frozen request file.
2. Run it only through GitHub Environment `synology-staging` and trusted runner `freqtrade-staging`.
3. Preserve the existing protected env file, secrets and Authentik/PostgreSQL volumes.
4. Produce an always-uploaded, secret-free report.
5. Close the request PR without merge after its one authorized operation and evidence capture.

### 8. First membership bootstrap

The accepted sequence is:

1. Authentik login succeeds and returns exact `iss + sub`.
2. Portal creates or recognizes the principal but denies product access without membership.
3. A target-side, one-time and audited bootstrap grants the exact principal the required initial membership and role.
4. No email-based, domain-based or first-login-is-admin shortcut is allowed.

If final browser acceptance stops only at the owner's interactive MFA challenge, leave exactly one owner next action describing that interaction.

## Safety boundary

This task does not authorize:

- live capital;
- production trading;
- real exchange orders;
- withdrawals;
- exchange credentials in GitHub or Portal configuration;
- destructive restore or migration;
- a database host port;
- Docker socket access by application containers;
- privileged containers;
- host networking;
- unauthenticated public Portal access as a terminal state.

Any Freqtrade runtime touched by this task must remain `dry_run` and must not receive order authority.

## Terminal acceptance

The task is complete only when all are proven:

1. `https://auth.molehill.cloud` remains healthy.
2. `https://quant.molehill.cloud` redirects an unauthenticated browser to Authentik.
3. Password plus Authentik TOTP/MFA completes successfully.
4. Callback returns to `https://quant.molehill.cloud/api/identity/callback`.
5. Portal creates its own secure session.
6. Fixture identity is disabled.
7. Missing membership fails closed.
8. Explicit exact-principal bootstrap grants the intended membership.
9. The authenticated user can open the Portal.
10. Logout invalidates the Portal session.
11. Required CI is green on the exact implementation head.
12. Trusted-runner deployment evidence is captured.
13. No later workflow restores fixture mode.
14. No secret value is recorded.
15. No live-capital authority is granted.

## Required terminal report

Record:

- implementation PR and exact head SHA;
- merge SHA;
- required workflow run IDs;
- request-only PR and its terminal closed-without-merge state;
- deployment run and job IDs;
- artifact ID, name and digest;
- container names and health states;
- public endpoint checks;
- fixture identity disabled evidence;
- login, callback, session and logout acceptance;
- membership bootstrap evidence;
- exact lines:

```text
secret_values_recorded=false
live_capital_authorized=false
```

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-01T00:21:00+02:00
head: 4660b1eb19b2c09af21f46cab2916b64dec7bfaf
branch: docs/portal-authentik-public-oidc-handover-20260801
pr: null
status: ready
proven:
  - Authentik server, worker and PostgreSQL are deployed on Synology with persistent target-owned secrets.
  - Authentik readiness repair PR 862 merged as 6ac747a069455ddfbfa00d861008dd81fbf509cf.
  - Authentik login renders over valid HTTPS at auth.molehill.cloud through Cloudflare Tunnel.
  - Portal public hostname is quant.molehill.cloud and callback is /api/identity/callback.
  - PR 876 contains the majority of the real OIDC and Portal session implementation but is based on obsolete LAN HTTP origins.
  - PR 876 is 18 commits ahead and 26 commits behind develop at this checkpoint.
derived:
  - Reusing Authentik is now justified as shared identity infrastructure and is less risky than replacing the nearly completed integration with a new local authentication system.
  - Public HTTPS removes the need to deploy the special local_http_test transport mode.
  - A clean replacement branch may be safer than merging the heavily diverged PR 876 branch.
unknown:
  - Current provider slug and public discovery output.
  - Current exact causes of the AI Platform and Freqtrade CI failures.
  - Whether the Synology identity container can reach the public Authentik issuer through Cloudflare hairpin egress.
  - Exact first principal iss and sub required for membership bootstrap.
conflicts: []
first_failure:
  marker: PORTAL_OIDC_PUBLIC_HTTPS_NOT_DEPLOYED
  evidence: Authentik public ingress works, but Portal still lacks a merged and deployed public-HTTPS OIDC integration.
rejected_hypotheses:
  - Replace Authentik with a new Portal-local password and TOTP implementation.
  - Deploy PR 876 unchanged with LAN HTTP issuer and callback.
  - Use auth.quant.molehill.cloud.
  - Put Cloudflare Access in front of all Authentik endpoints before OIDC acceptance.
  - Auto-promote the first matching email address to Portal administrator.
validation: []
blockers:
  - PR 876 must be reconciled with current develop and the public HTTPS contract.
  - Exact-head CI failures must be diagnosed and repaired.
  - Trusted-runner deployment and interactive browser acceptance remain pending.
next_action: Freeze current develop and PR 876, then implement or replace PR 876 for quant.molehill.cloud plus auth.molehill.cloud, obtain exact-head green CI, merge with expected_head_sha, execute one request-only Synology deployment and complete browser acceptance without recording secrets or authorizing live capital.
```