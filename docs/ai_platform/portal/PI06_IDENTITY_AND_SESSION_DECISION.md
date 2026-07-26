# PI-06 Product Identity and Session Decision

Status: **accepted**  
Decision date: `2026-07-26`  
Decision owner: repository owner  
Implementation status: **active — repository backend and BFF/browser integration complete; target deployment pending**

## 1. Decision

The portal uses **Authen­tik** as the product identity provider for human users.

Application integration uses OpenID Connect Authorization Code Flow with PKCE through the portal BFF. Identity-provider tokens and refresh material remain server-side and are never stored in browser JavaScript-accessible storage.

**Cloudflare Access remains a supplemental ingress control for privileged administrative, research, infrastructure and E2E surfaces. It is not the product IdP, tenant-membership source or application authorization boundary.**

| Concern | Authority |
|---|---|
| Primary credentials, login, authenticator enrollment, MFA challenge, IdP session and recovery | Authentik |
| Product user mapping | portal database keyed by immutable OIDC `iss` + `sub` |
| Tenants, memberships, roles and capabilities | portal database |
| Request authorization and tenant isolation | portal API/BFF on every protected request |
| Additional privileged ingress/device posture | Cloudflare Access where configured |
| Exchange credentials/runtime injection | future PI-07 only |

Email, display name, IdP groups and Cloudflare claims are attributes, not authoritative product tenant identifiers. Browser-supplied `tenant_id`, email domain and route visibility never grant membership or capability.

## 2. Why Authentik

The selected target is a small Linux-container deployment on Synology behind Cloudflare Tunnel. Authentik provides OIDC, back-channel logout, configurable authentication/recovery flows, WebAuthn/passkeys, TOTP, recovery codes and group administration while remaining deployable through Docker Compose.

The single Synology host remains a documented single failure domain. Repository configuration or a small-host deployment does not prove high availability, P11 acceptance or P14 readiness.

Auth0 remains the managed fallback if Authentik operations become unacceptable. Keycloak remains a scale/federation fallback. Cloudflare Access-only identity, automatic email-domain tenancy and browser-trusted authorization remain rejected.

## 3. OIDC client contract

The portal is a confidential OIDC client implemented at the BFF/server boundary.

Required protocol behavior:

- Authorization Code Flow with PKCE `S256`;
- exact issuer and audience/client validation;
- signed ID-token validation through discovery/JWKS;
- cryptographically secure one-time `state` and `nonce`;
- redirect URI allow-listing with no wildcard callback;
- immutable external key `iss` plus `sub`;
- email, username, groups and display name treated as non-authoritative attributes;
- refresh tokens, when enabled, encrypted and server-side only;
- local revocation and back-channel logout as the security boundary;
- no access, ID or refresh token in localStorage, sessionStorage, browser-readable cookies, logs, audit payloads or URLs.

## 4. Portal session policy v1

The portal creates an opaque server-side session after successful OIDC validation.

### Cookie

- name `__Host-portal_session`;
- `Secure`, `HttpOnly`, `SameSite=Lax`, `Path=/`, no `Domain`;
- at least 256 bits of random entropy;
- only a keyed hash is persisted;
- non-test deployments never accept the session over HTTP.

### Lifetimes

| Session class | Idle timeout | Absolute timeout |
|---|---:|---:|
| Standard human | 30 minutes | 12 hours |
| Privileged human | 15 minutes | 4 hours |
| High-impact re-authentication | n/a | five minutes since fresh IdP authentication |

A deployment may shorten these values. Increasing them requires a reviewed policy update and security tests.

### Immediate invalidation

Every protected request fails closed when:

- the local session is expired, idle-expired, revoked or invalid;
- issuer, subject, audience or authentication context is missing/mismatched;
- the portal principal is disabled;
- active membership is absent, disabled or version-mismatched;
- required capability is absent;
- back-channel logout or administrative revocation invalidated the IdP session;
- required session/membership storage is unavailable for a privileged mutation.

PI-06 v1 has no browser-trusted fallback.

## 5. Tenant and membership policy

The portal database is the source of truth for product tenancy and authorization.

Minimum records:

- `IdentityPrincipal`;
- `TenantMembership` with role set, status, validity and membership version;
- `PortalSession` with hashed ID, active membership, IdP `sid`, authentication/MFA context and expiry/revocation timestamps;
- `SessionRevocation` with actor, reason and correlation context.

Rules:

- `(issuer, subject)` is globally unique;
- one principal may have memberships in multiple tenants;
- active tenant selection is allowed only from current server-side memberships;
- trusted request context derives tenant from membership, never unvalidated browser input;
- role/capability evaluation uses current portal permission mappings;
- IdP groups may assist controlled bootstrap but cannot silently create membership on login;
- membership/role changes are audited, increment `membership_version` and synchronously revoke affected sessions;
- v1 uses no positive authorization cache;
- initial platform administration requires an explicit migration/restricted command with audit evidence, never first-login email matching.

## 6. MFA and step-up policy

MFA is mandatory for every human principal holding mutation or privileged capabilities, including bot lifecycle changes, manual intents, model/risk administration, audit/platform administration and future credential or capital capabilities.

Preferred factor order:

1. WebAuthn/FIDO2/passkey or hardware key;
2. TOTP fallback;
3. offline single-use recovery codes.

SMS or email OTP cannot be the sole factor for privileged roles.

Fresh authentication no older than five minutes is required for MFA authenticator changes, recovery completion, membership/role administration, future credential administration, model promotion and any future live-capital authorization.

Page visibility is never MFA or authorization evidence.

## 7. Recovery and break-glass policy

The Authentik recovery flow uses a generic response that does not reveal account existence.

For an MFA-enrolled principal, recovery requires verified recovery-channel control plus an existing authenticator or recovery code, revokes all prior portal sessions and emits secret-free security/audit evidence.

When all factors/codes are unavailable, administrator-assisted recovery requires separate identity verification, audited reason, session revocation and forced MFA re-enrollment. Security questions and email-only privileged bypass are prohibited.

A break-glass administrator is reserved for IdP administration failure, uses multiple hardware authenticators where supported, stores recovery material offline, is restricted by Access/network policy, alerts on every use and is tested on a fixed schedule.

## 8. Revocation and logout

- local logout revokes the local session before IdP logout;
- logout-all revokes every local session before attempting IdP-wide logout/revocation;
- Authentik back-channel logout maps `sid` or subject to affected portal sessions;
- Authentik outage cannot prevent local revocation;
- user disablement, membership disablement, role reduction, suspected compromise and recovery revoke sessions immediately;
- service identities use a separate machine identity contract.

Revocation evidence excludes tokens, cookie values and recovery material.

## 9. Cloudflare Access boundary

Access is an additional gate for privileged administration, research, infrastructure and autonomous E2E control surfaces.

Requirements:

- explicit allow rules and no unrestricted OTP policy;
- MFA/authentication-method requirements for privileged users;
- short Access sessions consistent with the portal maximum;
- service-auth credentials for machines, never reused human credentials;
- no protected-route bypass policy;
- direct-origin denial independent of Access;
- application session/RBAC checks after Access succeeds.

Cloudflare headers/tokens may be defense-in-depth context but never create portal principals, memberships or capabilities.

## 10. Synology deployment posture

The selected target is a dedicated Authentik Docker Compose stack on Synology or another Linux host.

Required controls:

- pin explicitly tested image versions and digests; no unbounded `latest`;
- dedicated PostgreSQL database/volume and application secrets;
- no committed passwords, client secrets, cookie keys or private endpoints;
- no Docker socket mount unless required; otherwise use a narrow socket proxy;
- expose Authentik only through intended private/Tunnel routing;
- restrict administration with Access;
- encrypted daily backups and periodic restore exercise;
- stage sequential upgrades;
- health checks for server, worker and PostgreSQL;
- monitoring for login failures, MFA changes, revocation and administrator actions.

Running Authentik, portal and databases on one host is accepted only as a bounded small target and cannot prove HA, P11, PI-07 or live-capital readiness.

## 11. Implementation evidence

### Completed repository backend

Task `FTAI-20260726-portal-pi06-product-identity-lifecycle`, PR #341, merge `41834d18f3a05b0dfa44dc5af9b97942e685d2a1` implemented identity/session/membership persistence, OIDC discovery/PKCE/JWKS validation, opaque sessions, CSRF, MFA/step-up, logout, revocation, back-channel logout, migrations and deterministic security tests.

Exact backend head `c258567cabd1c9ddf3d90c63f36319be99463978` passed AI Platform CI #1415, Freqtrade CI #1713 and security #1580.

### Completed BFF and browser-session integration

Task `FTAI-20260726-portal-pi06-bff-browser-session-integration`, PR #361, merge `4f76eecadcb8dda964a8d247327db9dc6ef1c931` implemented same-origin login/callback/session/logout routes, safe redirects, opaque cookie forwarding, Proxy/Route Handler protection, browser CSRF, session controls and deterministic denied/expired/revoked/MFA/step-up/cross-tenant E2E.

Exact final head `ec1970a9272bec241a1bab3c447ebd36f53afa58` passed Portal Web CI #287, Portal Universal E2E #292, AI Platform CI #1521, Freqtrade CI #1837 and security #1702. Portal Web passed all 37 Chromium tests.

### Remaining deployment and real acceptance

Next task: `FTAI-YYYYMMDD-portal-pi06-authentik-synology-deployment`.

It must add secret-free pinned deployment definitions, private networking, restricted bootstrap, health/migration ordering, backup/restore, recovery and rollback runbooks, and deterministic configuration validation. Real owner-managed probes remain blocked until target resources, secrets, users and MFA devices exist.

Cloudflare P11 acceptance remains separate.

## 12. PI-06 acceptance gates

PI-06 can be marked `done` only when:

1. protected APIs and browser paths reject missing, expired and revoked sessions;
2. tenant context derives exclusively from current portal membership;
3. cross-tenant requests fail closed in unit, integration and browser/security E2E;
4. privileged capabilities require declared MFA context and step-up age;
5. membership/role changes invalidate affected sessions within the documented bound;
6. recovery does not reveal account existence or bypass MFA;
7. local logout, logout-all and Authentik back-channel logout are tested;
8. state-changing BFF routes have tested CSRF;
9. browser storage/responses contain no IdP tokens, refresh tokens, client secrets or private endpoints;
10. unavailable identity/session infrastructure fails closed;
11. owner-managed target evidence proves Authentik login, MFA enrollment/challenge, revocation, recovery and restore;
12. Cloudflare Access remains supplemental and direct origin is denied in real P11 acceptance;
13. required web, AI, security, universal E2E and repository CI pass on exact final implementation heads.

## 13. Non-goals

- storing primary passwords in the portal database;
- automatic tenancy from email domain, IdP group or Cloudflare rule;
- exposing Authentik administration or tokens to browser code;
- SCIM, enterprise federation or social login in the initial package;
- PI-05, PI-07 or PI-08;
- real P11 claims from repository/fixture tests;
- live capital.

## 14. Official references

- Authentik OAuth2/OIDC provider: <https://docs.goauthentik.io/add-secure-apps/providers/oauth2/>
- Authentik front/back-channel logout: <https://docs.goauthentik.io/add-secure-apps/providers/oauth2/frontchannel_and_backchannel_logout/>
- Authentik WebAuthn/passkeys: <https://docs.goauthentik.io/add-secure-apps/flows-stages/stages/authenticator_webauthn/>
- Authentik TOTP: <https://docs.goauthentik.io/add-secure-apps/flows-stages/stages/authenticator_totp/>
- Authentik authenticator/recovery-code validation: <https://docs.goauthentik.io/add-secure-apps/flows-stages/stages/authenticator_validate/>
- Authentik recovery flow: <https://docs.goauthentik.io/add-secure-apps/flows-stages/flow/>
- Authentik Docker Compose: <https://docs.goauthentik.io/install-config/install/docker-compose/>
- Cloudflare Access policies: <https://developers.cloudflare.com/cloudflare-one/access-controls/policies/>
- Cloudflare Access MFA: <https://developers.cloudflare.com/cloudflare-one/access-controls/policies/mfa-requirements/>
- Auth0 Organizations: <https://auth0.com/docs/manage-users/organizations>
- Auth0 session management: <https://auth0.com/docs/manage-users/sessions/manage-user-sessions-with-auth0-management-api>
- Keycloak administration: <https://www.keycloak.org/docs/latest/server_admin/>
- Keycloak OIDC endpoints: <https://www.keycloak.org/securing-apps/oidc-layers>
