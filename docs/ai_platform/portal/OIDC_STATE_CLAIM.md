# Atomic OIDC Login-State Claim

Status: normative Portal identity callback contract.

## State transition

The existing `portal_oidc_login_flows.consumed_at` column is the sole claim marker for the current schema. A login flow is:

- **PENDING** while `consumed_at IS NULL` and `expires_at > now`;
- **TERMINALLY CLAIMED** after one conditional update sets `consumed_at`;
- **INVALID** when missing, expired or already claimed.

`IdentityRepository.consume_login_flow()` performs one conditional update whose predicate includes the state hash, `consumed_at IS NULL` and the unexpired boundary. It returns the claimed row only when that statement owns the transition. A zero-row result maps to one bounded invalid/expired response and does not reveal whether the state was missing, expired, in progress or previously completed.

## Transaction boundary

The claim transaction is short and commits before any OIDC provider request. Provider exchange, token validation and identity/session materialization never execute while a login-flow row or SQLite writer transaction is held.

A transaction rollback before commit does not create a durable claim and no provider exchange may have started. After the claim commits, the browser state is never reopened. Provider timeout, provider rejection or process death therefore requires a new login flow rather than reusing the original state or authorization code.

## Concurrency outcome

For two independent callbacks carrying the same browser state:

1. exactly one database transaction can own the conditional update;
2. only that owner decrypts the PKCE verifier and calls the provider;
3. every loser fails before provider exchange;
4. at most one Portal session and one login-success audit event can result from the state.

Different authorization codes do not create separate authority when they share one state transaction.

## Database semantics

The statement is compiled and tested against the supported PostgreSQL dialect and executed through independent file-backed SQLite connections. SQLite uses its bounded busy timeout; a waiting writer reevaluates the conditional predicate after the winning commit and receives a zero-row result.

No migration is introduced by this task. Shared production migration authority remains with Issue #1122.

## Evidence and privacy

Tests and errors may record only bounded outcome labels and existing request/correlation identifiers. They must never record or expose:

- raw browser state;
- authorization code;
- PKCE verifier or challenge source;
- ID/access/refresh token;
- provider response payload;
- session or CSRF token.

Protected Authentik staging validation must use synthetic test identities, prove one provider exchange owner and one resulting Portal session, and remain separate from production or live-capital authorization.
