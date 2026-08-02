---
task_id: FTAI-20260802-portal-sqlite-login-lock-repair
status: completed
branch: fix/portal-sqlite-login-lock-20260802
base_branch: develop
created: 2026-08-02
updated: 2026-08-02
parent_task: FTAI-20260802-portal-login-500-diagnostic
owned_paths:
  - ai_platform/portal/identity/service.py
  - ai_platform/portal/control_plane/database.py
  - tests/ai_platform/portal/identity/test_identity_lifecycle.py
  - docs/agents/tasks/FTAI-20260802-portal-sqlite-login-lock-repair.md
---

# Portal SQLite login lock repair

## Proven incident

Trusted Synology diagnostic run `30757559104` captured the public login failure as:

```text
sqlite3.OperationalError: database is locked
public_runtime.login
  -> IdentityService.begin_login
  -> IdentityRepository.store_login_flow
```

Diagnostic artifact ID `8836409790`, artifact digest
`sha256:6ef6d3e0a20396432b9d5c2b4c9314854b6f3e75bddf16b5f0038a7dd1c0f2ac`,
report SHA-256
`1fc83ea8676dc18c0e0b5d9955b55b6e1287c59b3554adcd09c6f720d86f29df`.

## Root cause

`complete_login()` marked the one-time OIDC flow consumed and flushed that write, then retained the same SQLite write transaction while performing external OIDC token exchange. A concurrent `begin_login()` could exhaust SQLite's default busy wait while trying to store a new flow.

## Repair

- commit one-time flow consumption before external OIDC network I/O;
- copy only the bounded flow values needed after the transaction closes;
- perform principal, membership, session and audit writes in a fresh transaction after successful OIDC exchange;
- configure a 30-second SQLite DB-API busy timeout for brief residual write collisions;
- prove a concurrent login can persist while callback exchange is deliberately blocked;
- preserve one-time state consumption, issuer validation, MFA enforcement and session behavior.

## Delivery evidence

Implementation PR `#1072` merged as commit
`0e7825bf860cd8011e1bd9207fcb0765baf8d52a` after successful exact-head validation:

- Freqtrade CI run `30758092154`;
- AI Platform CI run `30758092163`;
- AI Program Closure E2E run `30758092150`;
- AI Strategy Engine run `30758092151`;
- zizmor security analysis run `30758092153`;
- full AI suite: `1080 passed`, `71 skipped` before final exact-head rerun;
- Python 3.11, 3.12, 3.13 and 3.14 matrix and CI Gate passed.

Request-only deployment PR `#1073` executed on the trusted Synology runner and closed without merge. Deployment run `30758715633` produced artifact `8837000925` with digest
`sha256:c678adf8766dbdac633ea9f6e6385e45c4c64662be3afb618a952672cb5ca411`.

The secret-free deployment report proves:

- status `success`;
- public login status `307` and redirect to the Authentik authorization endpoint;
- public callback redirect verified as `https://quant.molehill.cloud/portal`;
- Portal web and control-plane containers running and healthy on implementation `0e7825bf860c`;
- Authentik PostgreSQL, server and worker running and healthy;
- discovery and JWKS returned `200`;
- provider grant types exactly `["authorization_code"]`;
- legacy grants disabled;
- identity fixture disabled;
- no membership bootstrap, restore, trading, withdrawal or live-capital action;
- no secret values recorded.

At 2026-08-02 22:49 CEST the owner confirmed that the deployed Portal login works. This completes the remaining owner-only interactive acceptance without recording credentials, TOTP values or other secrets.

## Safety

No credentials, membership or production data were changed outside the existing bounded deployment contract. Failed OIDC exchange still leaves the state consumed and requires a fresh login, preserving fail-closed replay protection.

## Terminal checkpoint

```yaml
checkpoint_version: 5
updated_at: 2026-08-02T22:49:00+02:00
status: completed
proven:
  - public login HTTP 500 was caused by sqlite database locking
  - the transaction holding the writer lock across OIDC network I/O was removed
  - a bounded 30-second SQLite busy timeout is configured
  - concurrency regression proves a second login persists during a blocked callback exchange
  - all implementation, security, repository and E2E gates passed
  - implementation PR 1072 merged as 0e7825bf860cd8011e1bd9207fcb0765baf8d52a
  - trusted Synology deployment run 30758715633 succeeded
  - public login now returns HTTP 307 to Authentik instead of HTTP 500
  - public callback redirect to https://quant.molehill.cloud/portal is verified
  - request-only PR 1073 closed without merge
  - owner confirmed successful interactive Portal login at 2026-08-02T22:49:00+02:00
remaining_owner_acceptance: []
next_action: none; repair, deployment and owner acceptance are terminally complete
blockers: []
```

```text
secret_values_recorded=false
live_capital_authorized=false
```
