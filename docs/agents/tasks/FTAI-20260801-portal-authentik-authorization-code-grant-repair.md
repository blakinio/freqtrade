---
task_id: FTAI-20260801-portal-authentik-authorization-code-grant-repair
status: done
branch: docs/portal-authentik-grant-repair-checkpoint-20260801
base_branch: develop
created: 2026-08-01
updated: 2026-08-01
parent_task: FTAI-20260801-portal-authentik-public-oidc-handover
implementation_pr: 969
deployment_pr: 970
---

# Portal Authentik authorization-code grant repair

## Observed failure

The owner initiated public Portal login and Authentik redirected back to the Portal callback with:

```text
error=invalid_request
error_description=The request is otherwise malformed
```

The callback correctly rejected the error response because it contained no authorization `code`.

## Root cause

Authentik `2026.5` exposes provider `grant_types` as an explicit configuration field. The existing public Portal blueprint did not set that field, so the deployed provider had no enabled authorization-code grant and rejected the otherwise valid Authorization Code plus PKCE request.

## Repair

Implementation PR `#969` configured the provider with exactly:

```yaml
grant_types:
  - authorization_code
```

It also added trusted-runner verification that reads the deployed provider from the Authentik container and fails closed unless the resulting list is exactly:

```json
["authorization_code"]
```

Legacy and unrelated grants remain disabled, including implicit, hybrid, password, client credentials, refresh token and device-code flows.

Implementation merge commit:

```text
0fb4a30ac739ca1396c1477b08a812158ab568cd
```

## Validation

PR `#969` passed:

- AI Platform tests and lint;
- GitHub Actions security analysis;
- pre-commit and mypy;
- Python 3.11, 3.12, 3.13 and 3.14 tests;
- distribution build;
- CI Gate.

## Trusted Synology deployment evidence

Request-only PR `#970` was consumed and closed without merge.

```text
workflow run:     30717518354
implementation:   0fb4a30ac739ca1396c1477b08a812158ab568cd
artifact ID:      8824028586
artifact digest:  sha256:581961c62dcc85e3303530ba75a2cd8db9734a3758e8c32052a91694604c259c
report SHA-256:   dfaab11fca5f275eb558922511806162fc17fc62593d9bfe916cf3f007a96bf2
```

The trusted-runner report proves:

- deployment status is success;
- deployed grant types are exactly `["authorization_code"]`;
- authorization-code grant is enabled;
- legacy grants are disabled;
- provider and application exist;
- callback is `https://quant.molehill.cloud/api/identity/callback`;
- scopes are `openid profile email`;
- discovery returns HTTP 200;
- JWKS returns HTTP 200;
- the Portal login endpoint returns HTTP 307;
- Authentik PostgreSQL, server and worker are running and healthy;
- Portal web and control plane are running and healthy;
- identity fixture is disabled;
- public ingress is authorized;
- restore is unauthorized;
- no secret values were recorded;
- live capital is unauthorized.

## Remaining interactive acceptance

The malformed authorization request is repaired. Final browser acceptance still requires the owner to enter private credentials that are not available to automation:

1. Open a fresh browser session at `https://quant.molehill.cloud`.
2. Do not reuse the earlier callback URL or its old `state` value.
3. Log in as `akadmin` with the owner password and current TOTP.
4. Confirm the Portal opens with `tenant-local` admin access.
5. Log out and confirm the previous session no longer grants access.

No password, TOTP seed, TOTP code or session cookie may be posted to GitHub or chat.

## Terminal state

```yaml
status: done
root_cause: missing Authentik provider grant_types on version 2026.5
repair: authorization_code-only provider configuration
implementation_sha: 0fb4a30ac739ca1396c1477b08a812158ab568cd
deployment_run: 30717518354
deployed_grant_types:
  - authorization_code
legacy_grants_disabled: true
secret_values_recorded: false
live_capital_authorized: false
```
