---
task_id: FTAI-20260805-portal-remediation-1132
programme_id: FTAI-20260803-portal-remediation
repository: blakinio/freqtrade
issue: 1132
lane: freqtrade-portal
status: repository_complete_waiting_external
phase: archived_repository_delivery
branch: fix/portal-oidc-logout-replay-1132
pull_request: 1284
implementation_head: 48726c3f799661065c379945ac7b010c06cc121b
prompting_standard_version: 2.1
execution_mode: github_only
ownership_released: true
live_capital_authorized: false
protected_authentik_authorized: false
secrets_recorded: false
---

# Portal OIDC back-channel logout replay protection — Issue #1132

## Repository result

The Portal now implements durable issuer/client/`jti`-scoped replay protection for OIDC back-channel logout without introducing a competing general idempotency authority.

Implemented invariants:

- signed logout tokens require bounded `jti`, `iat`, `exp`, issuer, audience, logout event and subject and/or `sid`;
- validated identity retains issuer, client ID, `jti`, subject/`sid`, time bounds, normalized `typ`, signing `kid` and `alg`;
- first delivery atomically reserves the replay identity, revokes matching sessions, writes one safe audit event and stores the terminal result;
- exact replay returns the stored result without another revocation or success audit;
- conflicting reuse fails closed without principal/session enumeration;
- replay state survives restart and independent PostgreSQL concurrency has one mutation owner;
- no raw logout token is stored;
- revision `1→2` is part of the canonical Portal migration/schema authority;
- compatibility mode remains the default, while `PORTAL_IDENTITY_REQUIRE_LOGOUT_TOKEN_TYP=true` enables strict `typ=logout+jwt` enforcement in the canonical runtime;
- both identity runtimes expose bounded non-cached success/failure semantics.

## Validation

Exact repository implementation head:

```text
48726c3f799661065c379945ac7b010c06cc121b
```

Terminal exact-head evidence:

- Freqtrade CI run `31113093309`: PASS;
- Risk-aware component CI run `31113096890`: PASS;
- CodeQL run `31113093459`: PASS;
- zizmor run `31113092947`: PASS;
- zero unresolved pull-request review threads;
- mergeable PR state confirmed.

Focused and integration coverage includes SQLite restart/replay, exact conflict behavior, audit cardinality, canonical schema migration, independent-connection PostgreSQL concurrency and backup/restore readiness.

## Independent audit

Initial finding `FTAI-1132-AUD-001` identified that strict logout-token typing existed only in direct/test configuration and could not be enabled by the product runtime.

Remediation:

- added bounded environment parsing for `PORTAL_IDENTITY_REQUIRE_LOGOUT_TOKEN_TYP`;
- forwarded the value through `IdentityRuntimeConfig` into `OidcClientConfig`;
- added strict, compatibility-default and invalid-configuration tests.

Final post-remediation result:

```text
PASS_ZERO_MATERIAL_FINDINGS
```

The final audit reviewed replay identity/fingerprint semantics, transaction ownership, restart/concurrency behavior, migration authority, HTTP mapping, strict-type rollout and secret exclusion. No remaining material repository finding was proven.

## External acceptance boundary

Issue #1132 must remain open in `WAITING_EXTERNAL_ACCEPTANCE` until an owner-authorized protected Authentik staging exercise proves login/logout compatibility and key rotation on the exact deployed candidate.

Repository merge authority does not authorize protected identity mutation, credentials, production deployment, trading, withdrawals or live capital.

## Terminal checkpoint

```yaml
checkpoint_version: 10
updated_at: 2026-08-06T15:31:00Z
status: repository_complete_waiting_external
implementation_head: 48726c3f799661065c379945ac7b010c06cc121b
pull_request: 1284
independent_audit: PASS_ZERO_MATERIAL_FINDINGS
required_ci: PASS
review_threads: 0
ownership_released: true
blocker: owner-authorized protected Authentik staging acceptance
next_action: Merge PR 1284 after archive-only exact-head checks pass, then label Issue 1132 as waiting external acceptance without closing it.
```
