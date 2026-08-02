---
task_id: FTAI-20260802-portal-public-origin-redirect-repair
status: waiting
branch: docs/portal-public-origin-proof-checkpoint-20260802
base_branch: develop
created: 2026-08-02
updated: 2026-08-02
parent_task: FTAI-20260801-portal-authentik-public-oidc-handover
owned_paths: []
---

# Portal public-origin redirect repair

## Incident

After successful Authentik password and TOTP authentication, the public callback created the Portal session but returned a browser redirect to `https://0.0.0.0:3000/`. Chrome rejected the non-routable container address with `ERR_ADDRESS_INVALID`.

## Confirmed cause

The Next.js callback route built the final redirect from `request.nextUrl.origin`. Behind Cloudflare Tunnel and the container listener, that origin can be the internal listener address rather than the public Portal origin.

## Completed implementation

Implementation PR `#1004` introduced a trusted public-origin resolver for callback and fixture-login redirects. Production no longer derives the final browser origin from the container request. The exact-head implementation passed AI Platform tests, Portal typecheck/lint/build and Chromium regression, Universal E2E, Security, Python 3.11-3.14, pre-commit/mypy, distribution build and CI Gate, then merged as:

```text
c9570c6bf86f1285491ae9e537b6796ae9dc564f
```

The first request-only rollout `#1010` deployed that application revision successfully but exposed a syntax error in the new target verifier before the HTTP assertion could run. No callback-proof claim was made from that failed verifier run. Request `#1010` was closed without merge.

Verifier repair PR `#1012` rewrote the generated Node probe and added `node --check` regression coverage. It passed exact-head AI Platform, Security, pre-commit/mypy, Python 3.11-3.14, distribution build and CI Gate, then merged as:

```text
6c0f3370428044584efb73352d47218661b531cb
```

## Trusted target evidence

Request-only PR `#1014` was consumed and closed without merge.

```text
workflow run:     30743112661
job:              91483929864
implementation:   6c0f3370428044584efb73352d47218661b531cb
artifact ID:      8832123343
artifact digest:  sha256:144d201c13fcf074518b2aba6145d152d091d3a2b1874cba73ef8dfc40eda56b
report SHA-256:   9ee3e4ec61663fbb398a38971ca324cbe3b621a92b6b568d4846d6a5192fe84b
```

Proven by the trusted Synology runner:

- Portal web and control plane are running and healthy on the exact implementation revision;
- Authentik PostgreSQL, server and worker are running and healthy;
- discovery and JWKS return HTTP 200;
- public login returns HTTP 307 to Authentik;
- the provider grant list is exactly `authorization_code`;
- the isolated built-image callback probe returns HTTP 303;
- the callback `Location` is exactly `https://quant.molehill.cloud/portal`;
- `public_callback_redirect_verified=true`;
- identity fixture is disabled in the deployed public runtime;
- no Authentik client-secret rotation or owner membership mutation occurred;
- restore remains unauthorized;
- no secret values were recorded;
- no live capital was authorized.

Superseded PR `#982` was explicitly closed without merge. Request-only PRs `#1010` and `#1014` are terminal and closed without merge.

## Remaining owner acceptance

The code, deployment and target-side callback proof are complete. This task is `waiting` only for a fresh private browser journey:

1. Close the old `0.0.0.0:3000` tab and all stale callback tabs.
2. Open a new incognito window at `https://quant.molehill.cloud`.
3. Log in as `akadmin` using the private password and current Authentik TOTP.
4. Confirm the browser remains on `https://quant.molehill.cloud` and the Portal loads for `tenant-local` with admin access.
5. Log out.
6. Confirm the previous Portal session no longer grants authenticated access.

No password, TOTP seed, TOTP code, authorization code, state value or session cookie may be posted to GitHub or chat.

## Context checkpoint

```yaml
checkpoint_version: 2
updated_at: 2026-08-02T12:25:00+02:00
status: waiting
proven:
  - public callback no longer derives its final browser origin from request.nextUrl.origin
  - implementation PR 1004 merged as c9570c6bf86f1285491ae9e537b6796ae9dc564f
  - verifier repair PR 1012 merged as 6c0f3370428044584efb73352d47218661b531cb
  - exact built-image callback probe returned HTTP 303
  - callback Location is exactly https://quant.molehill.cloud/portal
  - public Portal, control plane and Authentik services are healthy
  - discovery and JWKS return HTTP 200
  - provider uses exactly authorization_code
  - request PRs 1010 and 1014 are closed without merge
  - superseded PR 982 is closed without merge
  - secret_values_recorded=false
  - live_capital_authorized=false
unknown:
  - fresh owner browser authenticated Portal acceptance result
  - logout session invalidation result
conflicts: []
first_failure: null
blockers:
  - explicit owner browser interaction with private password and TOTP
next_action: owner performs a fresh incognito login from https://quant.molehill.cloud, confirms tenant-local admin access, logs out and confirms session invalidation
```

```text
secret_values_recorded=false
live_capital_authorized=false
```
