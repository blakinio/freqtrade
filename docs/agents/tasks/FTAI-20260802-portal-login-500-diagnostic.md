---
task_id: FTAI-20260802-portal-login-500-diagnostic
status: active
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

The Next.js BFF message proves only that the internal identity backend returned a non-JSON HTTP 500. It does not identify the underlying exception.

## Objective

Capture a secret-free, read-only trusted-runner diagnostic that identifies the sanitized control-plane exception and application frames for the observed `/v1/identity/login` HTTP 500.

## Authorization and boundaries

- diagnostic only;
- read recent Portal web and control-plane container logs;
- read container state/revision and aggregate identity database state;
- redact OIDC code, state, tokens, cookies, authorization headers, client secrets and long token-like values;
- do not mutate Authentik, Portal configuration, membership, credentials, sessions or database state;
- do not perform browser password/TOTP automation;
- no restore, exchange operation, trading, withdrawals or live capital.

## Acceptance inventory

- implementation PR changes only the four owned paths;
- focused tests prove login-only HTTP 500 detection, exception sanitization and exact-one-file request enforcement;
- required repository CI is green on the exact implementation head;
- after merge, a separate request-only PR adds exactly `deploy/synology/portal-oidc/run-requests/login-diagnostic-20260802-v1.json`;
- the trusted runner uploads a secret-free report containing at least one login HTTP 500 and one sanitized exception;
- the request-only PR closes without merge;
- the incident checkpoint records the exact root cause and one bounded repair next action.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-02T18:24:00+02:00
status: active
proven:
  - public Next.js login route reached the identity backend
  - identity backend returned non-JSON HTTP 500
  - previous target proof at 2026-08-02T12:25:00+02:00 is stale for current owner acceptance
  - no open Portal identity PR overlaps the diagnostic paths
  - diagnostic branch created from current develop
unknown:
  - exact control-plane exception type and message
  - whether the failure is database, filesystem, runtime configuration or OIDC URL generation
  - current login-flow database state after the failed request
conflicts:
  - prior checkpoint claimed the public login endpoint returned HTTP 307, while the owner now observes HTTP 500
first_failure: public login endpoint returns non-JSON HTTP 500
blockers: []
next_action: validate and merge the sanitized login diagnostic implementation, then run the exact-one-file trusted-runner request
```

```text
secret_values_recorded=false
live_capital_authorized=false
```
