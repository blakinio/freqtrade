# PI-06 Product Identity Lifecycle — Repository Implementation

Status: **repository backend implemented; browser BFF and target deployment remain separate**

## 1. Scope

This package replaces the fail-closed trusted-development identity provider with an optional real product-identity application factory for the Python portal control plane.

Delivered repository behavior:

- immutable OIDC `iss` + `sub` principal mapping;
- portal-owned tenant memberships, roles, membership versions and validity windows;
- OIDC Authorization Code Flow with PKCE, discovery, JWKS signature verification, issuer/audience/nonce validation and one-time state;
- opaque server-side sessions using a 256-bit browser token and only a keyed token hash in storage;
- `Secure`, `HttpOnly`, `SameSite=Lax`, host-only session cookie;
- server-verified double-submit CSRF protection for every unsafe portal method;
- membership-derived tenant and permission context for all existing protected control-plane routes;
- MFA requirement for any role with mutation/privileged capabilities;
- five-minute authentication-age enforcement for membership administration;
- local logout, logout-all, membership-change revocation and OIDC back-channel logout;
- identity-specific security audit records without tokens, client secrets or recovery material;
- deterministic runtime configuration that fails closed when required IdP or key settings are absent.

The existing `create_app(...)` factory remains available for isolated tests and explicit trusted-boundary consumers. Product deployments use `create_identity_enabled_app(...)` with an `IdentityService`.

## 2. Authority boundaries

| Concern | Authority |
|---|---|
| Primary login, MFA enrollment/challenge and recovery | authentik |
| OIDC token validation | server-side PI-06 OIDC adapter |
| Product principal mapping | portal identity database, unique by `issuer + subject` |
| Tenant membership, roles and permissions | portal identity database |
| Active tenant request context | validated current membership stored in the local session |
| CSRF | portal session plus server-hashed double-submit token |
| Session revocation | portal identity database |
| Privileged edge ingress | Cloudflare Access, supplemental only |
| Exchange credentials and order submission | not part of PI-06 |

## 3. Storage contracts

Migration `ai_platform/portal/identity/migrations/0001_identity_lifecycle.sql` creates:

- `portal_identity_principals`;
- `portal_tenant_memberships`;
- `portal_identity_sessions`;
- `portal_oidc_login_flows`;
- `portal_session_revocations`;
- `portal_identity_audit_events`.

No primary password, IdP access token, ID token, refresh token, client secret, session token or raw CSRF token is persisted.

Short-lived PKCE verifier material is encrypted server-side and tied to a one-time, expiring state record.

## 4. Session policy enforcement

The accepted policy is encoded by `IdentityPolicy`:

| Session | Idle | Absolute |
|---|---:|---:|
| read-only human | 30 minutes | 12 hours |
| mutation/privileged human | 15 minutes | 4 hours |
| high-impact step-up | — | authentication no older than 5 minutes |

A request fails closed when the local session is absent, malformed, expired or revoked; the principal is disabled; the membership is missing, disabled, expired or version-mismatched; required MFA is absent; or permissions do not contain the required capability.

Role or membership changes increment `membership_version` and synchronously revoke every affected local session. No positive authorization cache is introduced.

## 5. HTTP surface

The identity-enabled application adds:

- `GET /v1/identity/login`;
- `GET /v1/identity/callback`;
- `GET /v1/identity/session`;
- `POST /v1/identity/logout`;
- `POST /v1/identity/logout-all`;
- `POST /v1/identity/backchannel-logout`;
- `POST /v1/identity/memberships`;
- `PUT /v1/identity/memberships/{membership_id}/roles`;
- `POST /v1/identity/memberships/{membership_id}/disable`.

The back-channel endpoint requires `application/x-www-form-urlencoded`, validates the signed logout token and accepts only a standards-compatible event with `sub` or `sid`.

All other unsafe methods, including pre-existing bot, signal, terminal, notification and telemetry mutations, are covered by the identity CSRF middleware when the identity-enabled factory is used.

## 6. Runtime configuration

Required environment variables:

- `PORTAL_IDENTITY_ISSUER`;
- `PORTAL_IDENTITY_CLIENT_ID`;
- `PORTAL_IDENTITY_CLIENT_SECRET`;
- `PORTAL_IDENTITY_REDIRECT_URI`;
- `PORTAL_IDENTITY_SESSION_HMAC_KEY_B64`;
- `PORTAL_IDENTITY_FLOW_ENCRYPTION_KEY_B64`.

Both key variables must decode to at least 32 bytes. Values are injected at runtime and must not be committed, logged or returned to browser clients.

## 7. Bootstrap

The first principal and membership are created through the explicit restricted bootstrap methods. First-login email matching, IdP group claims and email-domain rules never create an administrator or tenant membership.

Deployment automation must replace direct bootstrap calls with a one-shot restricted command or migration wrapper that records operator evidence.

## 8. Tests and evidence

Focused tests cover:

- OIDC discovery, signed JWT/JWKS validation, issuer, audience, nonce and PKCE parameters;
- logout-token event validation;
- missing-session denial;
- host-only secure session and CSRF flow;
- one-time OIDC state consumption;
- MFA denial for privileged membership;
- idle expiry;
- logout and back-channel revocation;
- role-change session invalidation;
- open-redirect denial;
- migration table coverage and forbidden secret-column checks.

## 9. Remaining PI-06 work

This backend package does not claim full PI-06 completion. Remaining dependency-ordered work:

1. wire same-origin Next.js BFF login/logout/session routes and protected navigation to this backend contract;
2. add browser E2E for denied, expired, revoked, cross-tenant and re-authentication states against deterministic identity fixtures;
3. add authentik/Synology Compose deployment with pinned image digest and secret placeholders;
4. provision real owner-managed authentik and Cloudflare resources;
5. execute target-environment acceptance and recovery/restore runbooks.

No PI-07 credential broker, PI-08 order submission, P11 acceptance or live-capital authority is introduced.
