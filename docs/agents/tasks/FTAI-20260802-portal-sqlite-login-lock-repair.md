---
task_id: FTAI-20260802-portal-sqlite-login-lock-repair
status: active
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

Trusted Synology diagnostic run `30757559104` captured the current public login failure as:

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

## Root cause

`complete_login()` marked the one-time OIDC flow consumed and flushed that write, then retained the same SQLite write transaction while performing external OIDC token exchange. A concurrent `begin_login()` could exhaust SQLite's default busy wait while trying to store a new flow.

## Repair

- commit one-time flow consumption before external OIDC network I/O;
- copy only the bounded flow values needed after the transaction closes;
- perform principal, membership, session and audit writes in a fresh transaction after successful OIDC exchange;
- configure a 30-second SQLite DB-API busy timeout for brief residual write collisions;
- prove a concurrent login can persist while callback exchange is deliberately blocked;
- preserve one-time state consumption, issuer validation, MFA enforcement and session behavior.

## Safety

No Authentik configuration, credentials, membership, production data, restore, trading, withdrawal or live-capital authority. Failed OIDC exchange leaves the state consumed and requires a fresh login, preserving fail-closed replay protection.

## Checkpoint

```yaml
checkpoint_version: 2
updated_at: 2026-08-02T19:04:00+02:00
status: active
proven:
  - public login HTTP 500 is caused by sqlite database locking
  - the lock occurs while storing a new login flow
  - deployed containers are healthy and Authentik is not the immediate failure source
  - bounded transaction split and concurrency regression are implemented
  - all temporary implementation workflows and scripts are removed from the final diff
validation:
  exact_head: pending
next_action: complete exact-head CI, merge, deploy and repeat public login acceptance
blockers: []
```

```text
secret_values_recorded=false
live_capital_authorized=false
```
