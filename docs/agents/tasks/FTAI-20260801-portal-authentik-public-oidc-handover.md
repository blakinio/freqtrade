---
task_id: FTAI-20260801-portal-authentik-public-oidc-handover
status: waiting
branch: docs/portal-oidc-exact-issuer-checkpoint-20260802
base_branch: develop
created: 2026-08-01
updated: 2026-08-02
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
Issuer: https://auth.molehill.cloud/application/o/freqtrade-portal/
Callback: https://quant.molehill.cloud/api/identity/callback
Flow: OIDC Authorization Code plus PKCE
Scopes: openid profile email
Principal identity: exact iss plus sub
Owner username: akadmin
Owner tenant: tenant-local
Owner role: admin
```

The retired `auth.quant.molehill.cloud` hostname is forbidden. The issuer is an exact OIDC identifier; its final `/` is significant and must not be normalized away.

## Completed implementation

The public Authentik OIDC implementation, exact-owner bootstrap, Authentik 2026.5 grant repair and exact issuer repair are merged on `develop`.

Key merge commits:

```text
public OIDC machine identity and deploy repairs: f4ae0eb9d7297b62fe90b2f15c1623d054b219e7
exact-owner membership bootstrap:              443da5866e9b4a9d3442f266be1fe406405ed333
authorization-code grant repair:               0fb4a30ac739ca1396c1477b08a812158ab568cd
exact trailing-slash issuer repair:             8f23bbc7e09c1c1c0906e32adc2b5af137ec07d7
```

The implementation provides:

- Authentik confidential OIDC provider and application for slug `freqtrade-portal`;
- exact discovery issuer equality and exact JWT issuer validation;
- Authorization Code plus PKCE;
- provider grant types restricted to exactly `authorization_code`;
- Secure `__Host-` Portal cookies;
- no automatic first membership or email/domain/group promotion;
- no client secret, OIDC subject, password or TOTP value in GitHub;
- target-side exact `akadmin` `user_uuid` lookup;
- subject transfer to the control plane over stdin;
- only the subject SHA-256 retained in the owner-bootstrap report;
- exact `tenant-local` / `admin` membership verification;
- required `identity.membership_bootstrapped` audit event;
- no Docker socket, privileged mode, host networking or control-plane host port;
- no exchange credentials, order authority, withdrawals, restore or live capital.

## Initial public deployment evidence

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
- an active membership exists for `tenant-local` with role `admin`;
- the principal and membership were re-read from the Portal database;
- `identity.membership_bootstrapped` audit evidence is present;
- secret values recorded is false;
- live capital authorized is false.

## Authentik 2026.5 grant repair

The first owner browser attempt reached Authentik but `/authorize` returned `invalid_request`. Authentik 2026.5 required an explicit provider grant configuration, while the existing provider had an empty `grant_types` set.

Implementation PR `#969` merged as `0fb4a30ac739ca1396c1477b08a812158ab568cd`. Request-only PR `#970` was consumed and closed without merge.

```text
workflow run:     30717518354
implementation:   0fb4a30ac739ca1396c1477b08a812158ab568cd
artifact ID:      8824028586
artifact digest:  sha256:581961c62dcc85e3303530ba75a2cd8db9734a3758e8c32052a91694604c259c
report SHA-256:   dfaab11fca5f275eb558922511806162fc17fc62593d9bfe916cf3f007a96bf2
```

Proven on target:

- provider grant types equal exactly `authorization_code`;
- legacy and unrelated grants are disabled;
- discovery and JWKS return HTTP 200;
- public login returns an Authentik redirect;
- existing owner membership remains unchanged.

## Callback HTTP 500 diagnosis and exact issuer repair

After the grant repair, the owner completed password and TOTP and Authentik issued a valid authorization code. The Portal callback returned an HTML-backed HTTP 500. A one-time sanitized diagnostic was implemented and merged, then request-only PR `#984` was consumed and closed without merge.

```text
diagnostic workflow run:     30720540543
diagnostic artifact ID:      8824712608
diagnostic artifact digest:  sha256:de6786e44b8f966320ddb08187adebe6a243531025ae4f2430310c363ed85374
confirmed exception:         jwt.exceptions.InvalidIssuerError
Portal boundary:             OidcProtocolError: OIDC JWT validation failed
session count after failure: 0
```

The root cause was exact OIDC issuer handling. Authentik published and signed the ID token with issuer:

```text
https://auth.molehill.cloud/application/o/freqtrade-portal/
```

The Portal client removed the final `/` before PyJWT validation. Because OIDC issuer comparison is exact, PyJWT rejected the otherwise valid ID token.

Implementation PR `#986` preserved the configured issuer byte-for-byte for discovery comparison, JWT validation and principal identity, while trimming only when joining the discovery URL. It added regression coverage for an Authentik-style trailing-slash issuer and merged as `8f23bbc7e09c1c1c0906e32adc2b5af137ec07d7` after all required checks passed.

Request-only rollout PR `#991` was consumed and closed without merge.

```text
workflow run:     30721323788
implementation:   8f23bbc7e09c1c1c0906e32adc2b5af137ec07d7
artifact ID:      8825156338
artifact digest:  sha256:529a3f3b1e29dd3fe2e00a1a83ab63c13a7d8c0a3f021eb2638e801444ae91ff
report SHA-256:   6099c1541c7376a0b6342ffe4ace22f0588ff69d7f2eab1dac94c61e637ff6ec
```

Proven by the trusted Synology runner after the repair:

- control-plane image `local/freqtrade-portal-control-plane:8f23bbc7e09c` is running and healthy;
- web image `local/freqtrade-portal-web:8f23bbc7e09c` is running and healthy;
- Authentik PostgreSQL, server and worker are running and healthy;
- issuer equals the exact trailing-slash contract;
- discovery HTTP 200;
- JWKS HTTP 200;
- public login HTTP 307;
- provider grant types equal exactly `authorization_code`;
- legacy grants remain disabled;
- identity fixture remains disabled;
- no membership bootstrap or mutation was authorized;
- secret values recorded is false;
- live capital authorized is false.

## Remaining owner acceptance

All code, provider configuration, deployment and owner membership work is complete. The task remains `waiting` only because final acceptance requires private browser interaction unavailable to automation.

The previous callback URL, authorization code and state are consumed and must not be reused. The owner must perform a completely fresh flow:

1. Close all previous callback and Authentik tabs.
2. Open a new private/incognito browser window.
3. Open `https://quant.molehill.cloud` from the root URL.
4. Log in as `akadmin` using the owner password and a current Authentik TOTP.
5. Confirm the authenticated Portal loads for `tenant-local` with admin access.
6. Log out.
7. Confirm the previous Portal session no longer grants authenticated access.

No password, TOTP seed, TOTP code, authorization code, state value, JWT or session cookie may be posted to GitHub or chat.

## Context checkpoint

```yaml
checkpoint_version: 9
updated_at: 2026-08-02T00:49:00+02:00
implementation_head: 8f23bbc7e09c1c1c0906e32adc2b5af137ec07d7
status: waiting
proven:
  - public Portal and Authentik deployment is healthy
  - Authentik provider grants equal exactly authorization_code
  - discovery and JWKS return HTTP 200
  - public login redirects to the exact Authentik application
  - exact trailing-slash issuer is preserved for JWT validation
  - callback InvalidIssuerError root cause is fixed and deployed
  - Portal web and control-plane images run implementation 8f23bbc7e09c
  - identity fixture is disabled
  - exact akadmin user_uuid was resolved target-side without GitHub disclosure
  - tenant-local admin membership is active
  - identity.membership_bootstrapped audit evidence is present
  - request PRs 957, 964, 970, 984 and 991 were closed without merge
  - secret_values_recorded=false
  - live_capital_authorized=false
unknown:
  - fresh password and TOTP browser acceptance result after exact issuer rollout
  - authenticated Portal page acceptance result
  - logout session invalidation result
conflicts: []
first_failure: null
blockers:
  - explicit owner browser interaction with password and TOTP
next_action: owner starts a fresh incognito flow at https://quant.molehill.cloud, confirms tenant-local admin access, logs out and confirms session invalidation
```

Terminal safety evidence:

```text
secret_values_recorded=false
live_capital_authorized=false
```
