---
task_id: FTAI-20260802-portal-login-500-diagnostic
status: completed
branch: fix/portal-login-500-diagnostic-20260802
base_branch: develop
created: 2026-08-02
updated: 2026-08-02
parent_task: FTAI-20260801-portal-authentik-public-oidc-handover
owned_paths:
  - deploy/synology/portal-oidc/diagnose_login_failure.py
  - .github/workflows/portal-oidc-login-diagnostic.yml
  - tests/ai_platform/portal/deployment/test_portal_oidc_login_diagnostic.py
  - docs/agents/tasks/FTAI-20260802-portal-login-500-diagnostic.md
---

# Portal login HTTP 500 diagnostic

## Incident

At 2026-08-02 18:24 CEST the owner opened:

```text
https://quant.molehill.cloud/api/identity/login?return_to=%2F
```

The public Portal returned HTTP 500 JSON:

```json
{"detail":"Portal identity backend returned non-JSON status 500"}
```

The Next.js BFF message proved only that the internal identity backend returned a non-JSON HTTP 500. It did not identify the underlying exception.

## Diagnostic result

Trusted Synology diagnostic run `30757559104` captured the sanitized exception:

```text
sqlite3.OperationalError: database is locked
public_runtime.login
  -> IdentityService.begin_login
  -> IdentityRepository.store_login_flow
```

Artifact ID `8836409790`, artifact digest
`sha256:6ef6d3e0a20396432b9d5c2b4c9314854b6f3e75bddf16b5f0038a7dd1c0f2ac`,
report SHA-256
`1fc83ea8676dc18c0e0b5d9955b55b6e1287c59b3554adcd09c6f720d86f29df`.

The diagnostic also proved that the deployed Portal and Authentik containers were healthy and that Authentik/MFA was not the immediate source of the HTTP 500.

## Repair and target proof

Repair task `FTAI-20260802-portal-sqlite-login-lock-repair` split the callback transaction before external OIDC network I/O, added a bounded SQLite busy timeout and introduced a concurrency regression.

Implementation PR `#1072` merged as
`0e7825bf860cd8011e1bd9207fcb0765baf8d52a` after all required repository, security and E2E gates passed.

Request-only deployment PR `#1073` executed trusted Synology run `30758715633`, uploaded artifact `8837000925` with digest
`sha256:c678adf8766dbdac633ea9f6e6385e45c4c64662be3afb618a952672cb5ca411`, and closed without merge.

The deployment report proves:

- deployment status `success`;
- public login status `307` to Authentik instead of HTTP 500;
- public callback redirect verified as `https://quant.molehill.cloud/portal`;
- Portal web and control-plane containers running and healthy;
- Authentik PostgreSQL, server and worker running and healthy;
- discovery and JWKS status `200`;
- exactly `authorization_code` grant type with legacy grants disabled;
- identity fixture disabled;
- no secret values recorded and no live-capital action authorized.

At 2026-08-02 22:49 CEST the owner confirmed that the deployed Portal login works. This completes the owner-only interactive acceptance without recording credentials, TOTP values or other secrets.

## Acceptance inventory result

- diagnostic implementation was limited to the four owned paths;
- focused tests and exact-one-file request enforcement passed;
- required repository CI was green;
- trusted runner uploaded a secret-free report with the login HTTP 500 and sanitized exception;
- diagnostic request-only PR closed without merge;
- exact root cause and bounded repair were recorded;
- repair was merged, deployed and target-proven;
- owner confirmed successful interactive Portal login after deployment.

## Terminal checkpoint

```yaml
checkpoint_version: 3
updated_at: 2026-08-02T22:49:00+02:00
status: completed
proven:
  - public Next.js login route reached the identity backend
  - identity backend HTTP 500 was caused by sqlite3.OperationalError database is locked
  - the lock occurred while storing a new login flow
  - Authentik and MFA were not the immediate failure source
  - repair PR 1072 merged as 0e7825bf860cd8011e1bd9207fcb0765baf8d52a
  - trusted Synology deployment run 30758715633 succeeded
  - public login now returns HTTP 307 to Authentik
  - callback redirect to https://quant.molehill.cloud/portal is verified
  - request-only deployment PR 1073 closed without merge
  - owner confirmed successful interactive Portal login at 2026-08-02T22:49:00+02:00
remaining_owner_acceptance: []
next_action: none; incident diagnostic, repair, deployment and owner acceptance are terminally complete
blockers: []
```

```text
secret_values_recorded=false
live_capital_authorized=false
```
