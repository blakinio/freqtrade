---
task_id: FTAI-20260801-portal-authentik-public-oidc-handover
status: waiting
branch: docs/portal-oidc-final-checkpoint-20260801
base_branch: develop
created: 2026-08-01
updated: 2026-08-01
parent_task: FTAI-20260731-portal-local-authentik-oidc-integration
related_pr: 903
supersedes_pr: 876
owned_paths:
  - .github/workflows/portal-oidc-public-deploy.yml
  - .github/workflows/portal-oidc-owner-bootstrap.yml
  - ai_platform/portal/identity/bootstrap_membership.py
  - ai_platform/portal/identity/oidc.py
  - ai_platform/portal/identity/public_runtime.py
  - ai_platform/portal/identity/runtime.py
  - deploy/synology/portal-oidc/
  - docs/agents/tasks/FTAI-20260801-portal-authentik-public-oidc-handover.md
required_reads:
  - docs/ai_platform/portal/ARCHITECTURE_DECISIONS.md
  - docs/agents/tasks/FTAI-20260731-portal-local-authentik-oidc-integration.md
---

# Portal Authentik public OIDC handover

## Frozen contract

```text
https://quant.molehill.cloud
  -> https://auth.molehill.cloud
  -> password plus Authentik TOTP/MFA
  -> https://quant.molehill.cloud/api/identity/callback
  -> Portal-owned authenticated session
```

```text
Portal origin: https://quant.molehill.cloud
Authentik origin: https://auth.molehill.cloud
Callback: https://quant.molehill.cloud/api/identity/callback
Flow: OIDC Authorization Code plus PKCE
Scopes: openid profile email
Principal identity: exact iss plus sub
Owner username: akadmin
Owner tenant: tenant-local
Owner role: admin
```

The retired `auth.quant.molehill.cloud` hostname is forbidden.

## Completed implementation

The public Authentik OIDC implementation, target deployment repairs and exact-owner bootstrap mechanism are merged on `develop`.

Key merge commits:

```text
public OIDC machine identity and deploy repairs: f4ae0eb9d7297b62fe90b2f15c1623d054b219e7
exact-owner membership bootstrap:              443da5866e9b4a9d3442f266be1fe406405ed333
```

The implementation provides:

- Authentik confidential OIDC provider and application for slug `freqtrade-portal`;
- strict public callback and exact issuer equality;
- Authorization Code plus PKCE;
- Secure `__Host-` Portal cookies;
- no automatic first membership or email/domain/group promotion;
- no client secret, OIDC subject, password or TOTP value in GitHub;
- target-side exact `akadmin` `user_uuid` lookup;
- subject transfer to the control plane over stdin;
- only the subject SHA-256 retained in the secret-free report;
- exact `tenant-local` / `admin` membership verification;
- required `identity.membership_bootstrapped` audit event;
- no Docker socket, privileged mode, host networking or control-plane host port;
- no exchange credentials, order authority, withdrawals, restore or live capital.

## Public deployment evidence

Request-only PR `#957` was consumed and closed without merge.

```text
workflow run:     30710440357
implementation:   f4ae0eb9d7297b62fe90b2f15c1623d054b219e7
artifact ID:      8821903146
artifact digest:  sha256:d60a414460fbb64f1a3604c51912f4720757f25f8e9ee017b4997a90bade6657
report SHA-256:   06814f6c2bf7a66b506527c542bb4cb6f5172953338e801609393e3d4be3449d
```

Proven by the trusted Synology runner:

- Authentik server, worker and PostgreSQL healthy;
- Portal web and control plane healthy;
- discovery HTTP 200;
- JWKS HTTP 200;
- public login endpoint HTTP 307 to the deployed Authentik application;
- identity fixture disabled;
- public ingress authorized;
- restore unauthorized;
- no secret values recorded;
- no live capital authorized.

## Exact owner membership evidence

Implementation PR `#963` passed Security, AI Platform, pre-commit/mypy, Python 3.11-3.14, distribution build and CI Gate, then merged as `443da5866e9b4a9d3442f266be1fe406405ed333`.

Request-only PR `#964` was consumed and closed without merge.

```text
workflow run:     30714870323
implementation:   443da5866e9b4a9d3442f266be1fe406405ed333
artifact ID:      8823025050
artifact digest:  sha256:6f4bc0aa1ca0be7e79d6b8c133ec03147a102f3ca5f27a7b7aea7cc63ab9f16d
report SHA-256:   c40845c48e36f8ffb6e87f555c31a6315d2d67ce69f45823043e4c798b07559c
principal ID:     dfed63e0-481a-5ad1-91ad-9a27b5eae9fb
membership ID:    6a581ce6-b710-59b8-b2bd-efefa6b78d63
```

Proven by the trusted Synology runner:

- exact active Authentik username `akadmin` resolved in `user_uuid` subject mode;
- exact OIDC subject was not written to GitHub;
- a new active membership was created for `tenant-local` with role `admin`;
- the principal and membership were re-read from the Portal database;
- `identity.membership_bootstrapped` audit evidence is present;
- secret values recorded is false;
- live capital authorized is false.

## Remaining owner acceptance

All backend, deployment and membership work is complete. The task is `waiting` only because the final acceptance requires the owner to enter private interactive credentials that are not available to automation.

The owner must perform exactly these browser actions:

1. Open `https://quant.molehill.cloud`.
2. Log in as `akadmin` using the owner password and Authentik TOTP.
3. Confirm the authenticated Portal loads for `tenant-local` with admin access.
4. Log out.
5. Confirm the previous Portal session no longer grants authenticated access.

No password, TOTP seed, TOTP code or session cookie may be posted to GitHub or chat.

## Context checkpoint

```yaml
checkpoint_version: 7
updated_at: 2026-08-01T21:32:00+02:00
develop_head: 443da5866e9b4a9d3442f266be1fe406405ed333
status: waiting
proven:
  - public Portal and Authentik deployment is healthy
  - discovery and JWKS return HTTP 200
  - public login redirects to the exact Authentik application
  - identity fixture is disabled
  - exact akadmin user_uuid was resolved target-side without GitHub disclosure
  - tenant-local admin membership is active
  - identity.membership_bootstrapped audit evidence is present
  - request PRs 957 and 964 were closed without merge
  - secret_values_recorded=false
  - live_capital_authorized=false
unknown:
  - password and TOTP browser acceptance result
  - authenticated Portal page acceptance result
  - logout session invalidation result
conflicts: []
first_failure: null
blockers:
  - explicit owner browser interaction with password and TOTP
next_action: owner logs in at https://quant.molehill.cloud, confirms admin access, logs out and confirms session invalidation
```

Terminal safety evidence:

```text
secret_values_recorded=false
live_capital_authorized=false
```
