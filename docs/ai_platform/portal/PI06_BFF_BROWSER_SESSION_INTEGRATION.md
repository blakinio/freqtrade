# PI-06 BFF and Browser Session Integration

Snapshot date: `2026-07-26`.

## Purpose

This package connects the same-origin Next.js portal boundary to the merged PI-06 Python identity backend from PR #341 without provisioning a real identity provider or exposing private control-plane details to browser code.

It is repository and deterministic browser evidence only. It is not evidence that Authentik, Synology, Cloudflare Access or real recovery flows are deployed.

## Browser boundary

The browser communicates only with same-origin portal routes:

- `GET /api/identity/login`;
- `GET /api/identity/callback`;
- `GET /api/identity/session`;
- `POST /api/identity/logout`;
- `POST /api/identity/logout-all`;
- existing same-origin product BFF routes.

The BFF forwards identity and application requests to `PORTAL_CONTROL_PLANE_URL` on the server. The browser never receives that private origin and never addresses Freqtrade, an exchange, a secret store or an observability backend directly.

## OIDC flow

1. The browser requests the same-origin login route with a safe relative `return_to` path.
2. The BFF calls the backend login route and accepts only an HTTPS authorization redirect.
3. The configured IdP redirects the browser to the same-origin BFF callback registered in `PORTAL_IDENTITY_REDIRECT_URI`.
4. The BFF sends only `code` and `state` to the private identity backend.
5. The backend performs PKCE token exchange and signed ID-token validation.
6. The BFF copies the backend's opaque session and CSRF `Set-Cookie` headers and accepts only a relative application redirect.

IdP access, ID and refresh tokens are neither returned by the backend contract nor stored in browser-readable storage.

## Session and CSRF

Product cookies retain the backend contract:

- `__Host-portal_session`: `Secure`, `HttpOnly`, `SameSite=Lax`, opaque session identifier;
- `__Host-portal_csrf`: `Secure`, browser-readable, `SameSite=Lax`, random CSRF value;
- `x-csrf-token`: required matching header for `POST`, `PUT`, `PATCH` and `DELETE`.

The browser helper reads only the CSRF cookie and adds the double-submit header to unsafe same-origin requests. It cannot read the session cookie.

The Next.js Proxy performs only optimistic, bounded checks:

- missing session redirects protected pages to `/login`;
- missing session returns `401` for protected APIs;
- missing or mismatched CSRF returns `403` for unsafe APIs.

Every changed Route Handler repeats the session and mutation-boundary checks. In API mode it forwards the original cookies and verified CSRF header to the identity-enabled backend, which remains authoritative for expiry, revocation, tenant membership, roles, capabilities, MFA and step-up.

Page visibility and Proxy decisions are never treated as authorization proof.

## Deterministic fixture identity

Browser acceptance uses fixture identity only when all three conditions are true:

```text
PORTAL_WEB_DATA_MODE=fixture
PORTAL_ENVIRONMENT=test
PORTAL_IDENTITY_FIXTURE_MODE=enabled
```

The test-only same-origin fixture route can select:

- `authenticated`;
- `anonymous`;
- `expired`;
- `revoked`;
- `mfa_missing`;
- `step_up_stale`;
- `cross_tenant`.

The fixture endpoint returns `404` outside this explicit mode. Fixture cookies are deliberately distinct from product `__Host-*` cookies and contain no IdP token or credential.

## Covered browser evidence

The Playwright suite proves deterministic handling for:

- anonymous protected-page redirect;
- fixture login and callback completion;
- session display with tenant and MFA state;
- missing and mismatched CSRF denial;
- MFA-required mutation denial;
- step-up-required mutation denial;
- expired and revoked session redirect;
- logout-all revocation;
- cross-tenant page and API denial;
- preservation of existing bot, signal, lifecycle, notification and terminal behavior.

These tests are CI evidence for the BFF and browser contract. They do not exercise a real Authentik instance, real MFA enrollment, real recovery or real Cloudflare ingress.

## Required deployment configuration

A later deployment-owned package must inject, without committing values:

- `PORTAL_CONTROL_PLANE_URL`;
- backend `PORTAL_IDENTITY_ISSUER`;
- backend `PORTAL_IDENTITY_CLIENT_ID`;
- backend `PORTAL_IDENTITY_CLIENT_SECRET`;
- backend `PORTAL_IDENTITY_REDIRECT_URI` pointing at the public same-origin callback;
- backend session hash, CSRF and encryption keys;
- database connection and migration state.

The real callback URL must be registered exactly in Authentik. Browser and backend origins must use HTTPS so `__Host-*` cookies are accepted.

## Non-goals

This package does not:

- deploy or configure Authentik, PostgreSQL, Redis or Synology containers;
- provision users, MFA devices, recovery data, Cloudflare Tunnel, DNS or Access;
- expose a browser membership administration flow;
- implement PI-05, PI-07 or PI-08;
- claim P11 production-like staging acceptance;
- enable live capital or withdrawals;
- alter frozen thresholds, Phase 6 evidence or protected final holdout policy.

## Next package after merge

After this repository package is complete, the next identity step is a separately declared Authentik/Synology deployment package with pinned images, runtime-injected secrets, restricted bootstrap, backup/restore and recovery runbooks, and explicit real-environment probes. It must remain distinct from P11 Cloudflare acceptance and from any capital authorization.
