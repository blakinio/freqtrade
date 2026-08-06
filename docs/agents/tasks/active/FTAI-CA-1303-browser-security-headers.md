# FTAI-CA-1303 — Portal browser security headers

```yaml
task_id: FTAI-CA-1303-browser-security-headers
programme_id: FTAI-20260805-platform-continuous-assurance
parent_issue: 1114
issue: 1303
status: implementing
claim_id: ftaica-1303-20260806T133600Z-gpt56a
owner: repair-worker-1303-20260806T133600Z
session_id: repair-session-1303-20260806T133600Z-gpt56a
claimed_at: 2026-08-06T13:36:00Z
lease_expires_at: 2026-08-06T14:21:00Z
base_branch: develop
base_head: 6e7147c866d3b7f91545c0aad54eac924ba7fa71
branch: repair/1303-browser-security-headers
priority: P1
risk: medium
feature_scope:
  type: browser_security_boundary
  user_facing: true
  backend_required: false
  frontend_required: true
  integration_required: true
  e2e_required: true
  completion_claim: repository_application_boundary
owned_paths:
  - ai_platform/portal/web/next.config.ts
  - ai_platform/portal/web/proxy.ts
  - ai_platform/portal/web/lib/security-headers.ts
  - ai_platform/portal/web/e2e/specs/security/security-headers.spec.ts
  - docs/ai_platform/portal/BROWSER_SECURITY_HEADER_POLICY.md
  - docs/ai_platform/portal/FEATURE_COMPLETENESS_LEDGER.json
  - docs/ai_platform/portal/FEATURE_COMPLETENESS_LEDGER.md
  - docs/agents/tasks/active/FTAI-CA-1303-browser-security-headers.md
  - docs/agents/tasks/archive/FTAI-CA-1303-browser-security-headers.md
shared_paths: []
forbidden_paths:
  - .github/workflows/**
  - deploy/**
  - ai_platform/portal/identity/**
  - requirements*.txt
  - pyproject.toml
conflict_groups:
  - portal-web-proxy
  - portal-status-ledger
```

## Root cause

The Portal had no repository-owned application-layer policy for CSP, framing, MIME sniffing,
referrer leakage, browser permissions or cross-origin document/resource isolation. The only
`next.config.ts` hardening disabled the framework branding header. Repository tests therefore could
not prevent an authenticated browser boundary from regressing to an unbounded or missing policy.

## Bounded implementation contract

- generate one cryptographically unpredictable nonce for every applicable request;
- forward the nonce and exact CSP to Next.js rendering and return the same CSP to the browser;
- keep production `script-src` free of `unsafe-eval`, wildcards and private service origins;
- apply invariant framing, nosniff, referrer, permissions and compatible COOP/CORP headers;
- cover document, redirect, API/error and static-resource boundaries appropriately;
- preserve OIDC full-page redirects, same-origin BFF, local assets and required downloads;
- add direct-origin Playwright security regression tests and a canonical ownership document;
- update only the repository application-enforcement dimension of the completeness ledger;
- leave authenticated cache control to #1304 and HSTS/public-edge acceptance to #1305.

## Validation plan

```yaml
focused:
  - npm --prefix ai_platform/portal/web run lint
  - npm --prefix ai_platform/portal/web run typecheck
  - npm --prefix ai_platform/portal/web run build
  - npm --prefix ai_platform/portal/web run test:e2e:security
  - python tools/agents/check_portal_completeness_ledger.py
required_exact_head:
  - Freqtrade CI
  - Risk-aware component CI
  - CodeQL
  - zizmor
e2e:
  result: REQUIRED
  boundary: direct-origin Playwright browser-security policy
external_acceptance:
  result: NOT_CLAIMED
  owner: issue_1305
```

## Context checkpoint

```yaml
recovery:
  policy_version: 1
  generation: 1
  session_id: repair-session-1303-20260806T133600Z-gpt56a
  session_started_at: 2026-08-06T13:36:00Z
  checkpointed_at: 2026-08-06T13:38:00Z
  last_progress_at: 2026-08-06T13:38:00Z
  phase: implementation
  exact_head: pending-first-implementation-commit
  pull_request: none
  active_operation: none
  external_run_ids: []
  operation_started_at: null
  wait_deadline_at: null
  check_generation: null
  checks_used: 0
  status: active
  safe_to_resume: true
  resume_condition: claim remains unique and branch/path ownership is unchanged
  next_action: implement the nonce CSP helper and apply it at the Proxy/application boundary
```

## Safety boundary

This task cannot add browser access to private services, wildcard script/connect sources,
production `unsafe-eval`, secret-bearing CSP reporting, HSTS/public-edge claims, protected
infrastructure mutation, credentials, trading, withdrawals or live capital.
