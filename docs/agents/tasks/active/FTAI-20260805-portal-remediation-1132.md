---
task_id: FTAI-20260805-portal-remediation-1132
programme_id: FTAI-20260803-portal-remediation
repository: blakinio/freqtrade
issue: 1132
lane: freqtrade-portal
status: active
phase: implementation
branch: fix/portal-oidc-logout-replay-1132
pull_request: 1284
base_sha: 8ee4f6b2527b7bffb7d6967adb3c0f1abd1be56b
prompting_standard_version: 2.1
execution_mode: github_only
context_pressure: high
ownership:
  - ai_platform/portal/identity/models.py
  - ai_platform/portal/identity/repository.py
  - ai_platform/portal/identity/schema.py
  - ai_platform/portal/identity/oidc.py
  - ai_platform/portal/identity/service.py
  - ai_platform/portal/identity/http.py
  - ai_platform/portal/identity/public_runtime.py
  - ai_platform/portal/database/schema.py
  - docs/ai_platform/portal/SCHEMA_INTEGRITY.md
  - tests/ai_platform/portal/identity/**
  - tests/ai_platform/portal/database/**
  - .github/workflows/portal-oidc-logout-replay-postgresql.yml
live_capital_authorized: false
protected_authentik_authorized: false
secrets_recorded: false
---

# Portal OIDC back-channel logout replay protection — Issue #1132

## Objective

Implement durable, issuer/client/`jti`-scoped replay protection for OIDC back-channel logout without creating a competing general idempotency authority and without claiming protected Authentik acceptance.

## Required behavior

- require a non-empty bounded `jti` after signature, issuer, audience and event validation;
- return a validated logout identity containing issuer, configured client ID, `jti`, optional subject and optional IdP session ID;
- atomically reserve `(issuer, client_id, jti)` in the authoritative Portal database;
- persist a bounded request fingerprint and terminal result metadata without storing the raw logout token;
- exact replay returns the original terminal result without repeating session revocation or audit writes;
- same key with different validated semantics fails closed as a non-enumerating conflict;
- first reservation, revocation, audit and terminal result finalize in one transaction;
- concurrent independent PostgreSQL requests have exactly one mutation owner;
- restart preserves the terminal result and replay decision;
- malformed protocol input maps consistently to HTTP 400 in both identity runtimes; provider unavailability remains HTTP 502.

## Schema authority

Extend the existing `ai_platform.portal.database.schema` authority with an ordered revision `1→2`. Fresh databases must converge directly to revision 2, while a database at the exact revision-1 fingerprint must upgrade atomically under the existing advisory lock. Unknown, partial or divergent schemas remain fail-closed.

## Validation

- focused identity unit and HTTP tests;
- exact replay, conflicting replay and audit-count assertions;
- SQLite restart evidence for repository semantics;
- independent-connection PostgreSQL concurrency evidence through a bounded workflow;
- fresh-database and exact revision-1-to-2 migration tests;
- full exact-head required CI, risk-aware CI and workflow security analysis;
- independent final diff audit.

## Closeout boundary

The implementation PR references Issue #1132 but must not auto-close it unless protected Authentik staging acceptance is completed on the exact implementation head. Repository completion alone transitions the Issue to a truthful external-acceptance waiting state.

## Current checkpoint

- coordinator reconciliation PR #1275 merged as `8ee4f6b2527b7bffb7d6967adb3c0f1abd1be56b`;
- Issue #1250 closed;
- no competing active Issue #1132 task, branch or PR existed at dispatch;
- branch created from the exact merged coordinator head;
- exactly one draft implementation PR exists: #1284;
- next action: implement the bounded durable replay contract and ordered schema revision on PR #1284.
