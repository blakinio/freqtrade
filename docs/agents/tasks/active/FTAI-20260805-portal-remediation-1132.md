---
task_id: FTAI-20260805-portal-remediation-1132
programme_id: FTAI-20260803-portal-remediation
repository: blakinio/freqtrade
issue: 1132
lane: freqtrade-portal
status: active
phase: final_exact_head_validation
branch: fix/portal-oidc-logout-replay-1132
pull_request: 1284
base_sha: 8ee4f6b2527b7bffb7d6967adb3c0f1abd1be56b
head_sha: 3b15834d487d30a5a7213427bd49f4ba0900ce64
prompting_standard_version: 2.1
execution_mode: github_only
context_pressure: high
ownership:
  - ai_platform/portal/identity/models.py
  - ai_platform/portal/identity/repository.py
  - ai_platform/portal/identity/schema.py
  - ai_platform/portal/identity/oidc.py
  - ai_platform/portal/identity/runtime.py
  - ai_platform/portal/identity/service.py
  - ai_platform/portal/identity/http.py
  - ai_platform/portal/identity/public_runtime.py
  - ai_platform/portal/database/schema.py
  - docs/ai_platform/portal/SCHEMA_INTEGRITY.md
  - tests/ai_platform/portal/identity/**
  - tests/ai_platform/portal/database/**
  - .github/workflows/portal-schema-integrity.yml
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
- malformed protocol input maps consistently to HTTP 400 in both identity runtimes; provider unavailability remains HTTP 502;
- compatibility mode accepts reviewed legacy/untyped logout JWTs, while the canonical runtime can enable strict `typ=logout+jwt` enforcement through `PORTAL_IDENTITY_REQUIRE_LOGOUT_TOKEN_TYP`.

## Schema authority

Extend the existing `ai_platform.portal.database.schema` authority with an ordered revision `1→2`. Fresh databases must converge directly to revision 2, while a database at the exact revision-1 fingerprint must upgrade atomically under the existing advisory lock. Unknown, partial or divergent schemas remain fail-closed.

## Validation

- focused identity unit and HTTP tests;
- exact replay, conflicting replay and audit-count assertions;
- SQLite restart evidence for repository semantics;
- independent-connection PostgreSQL concurrency evidence through the canonical Portal schema workflow;
- fresh-database and exact revision-1-to-2 migration tests;
- full exact-head required CI, risk-aware CI and workflow security analysis;
- independent final diff audit.

## Independent audit

`FTAI-1132-AUD-001` — **remediated on head `3b15834d487d30a5a7213427bd49f4ba0900ce64`**.

The first audit found that `OidcClientConfig.require_logout_token_typ` existed only for direct/test construction. `IdentityRuntimeConfig` and `build_identity_service()` did not expose or forward it, so the protected rollout could not enable the declared strict policy. The repair:

- adds `PORTAL_IDENTITY_REQUIRE_LOGOUT_TOKEN_TYP` with explicit `true|false|1|0` parsing;
- forwards the value into the canonical `OidcClientConfig`;
- keeps compatibility mode as the default;
- adds focused tests for strict propagation, compatibility default and invalid configuration.

No other material finding was proven in the reviewed replay, transaction, schema, HTTP or test boundaries. Final zero-finding status remains conditional on exact-head CI and a final post-remediation diff check.

## Closeout boundary

The implementation PR references Issue #1132 but must not auto-close it unless protected Authentik staging acceptance is completed on the exact implementation head. Repository completion alone transitions the Issue to a truthful external-acceptance waiting state.

## Current checkpoint

```yaml
checkpoint_version: 9
updated_at: 2026-08-06T14:53:00Z
status: active
phase: final_exact_head_validation
branch: fix/portal-oidc-logout-replay-1132
pull_request: 1284
head: 3b15834d487d30a5a7213427bd49f4ba0900ce64
proven:
  - prior head d63f6073d413c2a5dce6735c4be3fbecc4318068 passed all required CI after a targeted retry of one unrelated flaky Python 3.14 job
  - PR is mergeable and has zero unresolved review threads
  - independent audit finding FTAI-1132-AUD-001 was remediated in runtime.py and focused tests
  - no protected Authentik, credential, deployment, trading, withdrawal or live-capital authority was used
unknown:
  - final exact-head required CI outcome for 3b15834d487d30a5a7213427bd49f4ba0900ce64
  - final post-remediation zero-finding audit result
  - protected Authentik staging acceptance outcome
blockers: []
next_action: Wait for exact-head CI to become terminal, inspect the first relevant failure if any, then perform the final post-remediation audit and merge only if all repository gates are green.
```
