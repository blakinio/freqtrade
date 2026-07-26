# PI-06 Product Identity and Session Decision

Status: **accepted**  
Decision date: `2026-07-26`  
Decision owner: repository owner  
Implementation status: **not started**

## 1. Decision

The portal will use **authentik** as the product identity provider for human users.

The application integration will use OpenID Connect Authorization Code Flow with PKCE through the portal BFF. Identity-provider tokens and refresh material remain server-side and are never stored in browser JavaScript-accessible storage.

**Cloudflare Access remains a supplemental ingress control for privileged administrative, research, infrastructure and E2E surfaces. It is not the product identity provider, tenant-membership source or application authorization boundary.**

The authoritative split is:

| Concern | Authority |
|---|---|
| Primary credentials, login, authenticator enrollment, MFA challenge, identity-provider session and recovery flow | authentik |
| Product user identity mapping | portal database keyed by immutable OIDC `iss` + `sub` |
| Tenant definitions, tenant membership, product roles and capabilities | portal database |
| Request authorization and tenant isolation | portal API/BFF on every protected request |
| Additional privileged ingress policy, device posture and independent edge MFA where configured | Cloudflare Access |
| Exchange credentials and runtime secret injection | future PI-07 only |

Email addresses, display names, IdP groups and Cloudflare claims are attributes, not authoritative product tenant identifiers. A browser-supplied `tenant_id`, email domain or route visibility never grants membership or capability.

## 2. Why authentik

The selected target is a small Linux-container deployment on Synology behind Cloudflare Tunnel. authentik provides the required OIDC provider, back-channel logout support, configurable authentication/recovery flows, WebAuthn/passkeys, TOTP, recovery codes and group administration while remaining deployable through Docker Compose.

The official Docker Compose guidance explicitly describes the deployment mode as suitable for test and small-scale production setups and specifies a minimum host of 2 CPU cores and 2 GB RAM. The portal will still treat a single Synology host as a single failure domain; this decision does not prove high availability, real P11 acceptance or P14 readiness.

The choice minimizes recurring managed-identity dependency for the current deployment while preserving standard OIDC boundaries so a later migration to another compliant IdP remains possible.

## 3. Alternatives considered

### Cloudflare Access as the only identity layer — rejected

Cloudflare Access is appropriate for controlling who can reach a protected application and can enforce IdP-based or independent MFA. It does not replace the portal's application-owned tenant membership, product session lifecycle, per-resource authorization and audit requirements. Using email rules or Access policy membership as the product tenancy source would couple customer authorization to infrastructure ingress policy and violate the existing security architecture.

### Auth0 — viable managed fallback, not selected

Auth0 provides OIDC, Organizations, MFA and session-management capabilities. It removes most self-hosting operations but introduces a managed external dependency and plan/organization/advanced-security limits that can change over time. It remains the preferred fallback if operating authentik becomes an unacceptable reliability or maintenance burden.

### Keycloak — viable scale-up fallback, not selected

Keycloak provides mature OIDC, session/token controls and organization capabilities. It is operationally heavier for the current small Synology deployment and has a broader administration surface than required for the first PI-06 package. It remains a viable migration target if future scale, federation or organization-administration requirements exceed the selected design.

### Microsoft Entra External ID — not selected

Entra External ID is suitable when the product is intentionally coupled to a Microsoft identity tenant and its administration model. The current portal has no approved Microsoft-tenant dependency, so introducing one would add an unnecessary external owner and licensing boundary.

## 4. OIDC client contract

The portal is a confidential OIDC client implemented at the BFF/server boundary.

Required protocol behavior:

- Authorization Code Flow with PKCE (`S256`).
- Exact issuer and audience/client validation.
- Signed ID-token validation using the issuer discovery/JWKS document.
- `state` and `nonce` generated with cryptographically secure randomness and consumed once.
- Redirect URI allow-listing; no wildcard callbacks.
- OIDC `iss` + `sub` is the immutable external identity key.
- `email`, `preferred_username`, groups and display-name claims are non-authoritative attributes.
- Refresh tokens, when enabled, are encrypted or stored only behind the server-side session/secret boundary.
- Front-channel logout is convenience only; back-channel logout and local revocation provide the security boundary.
- No access token, ID token or refresh token is written to `localStorage`, `sessionStorage`, browser-readable cookies, logs, audit payloads or URLs.

## 5. Portal session policy v1

The portal creates an opaque server-side session after successful OIDC validation.

### Cookie

- Name: `__Host-portal_session`.
- Attributes: `Secure`, `HttpOnly`, `SameSite=Lax`, `Path=/`, no `Domain` attribute.
- Value: at least 256 bits of cryptographically random entropy.
- Only a keyed hash of the session identifier is persisted.
- Session cookies are never accepted over HTTP in non-test deployments.

### Lifetimes

| Session class | Idle timeout | Absolute timeout |
|---|---:|---:|
| Standard authenticated human session | 30 minutes | 12 hours |
| Privileged human session | 15 minutes | 4 hours |
| Re-authentication window for high-impact actions | not applicable | 5 minutes since fresh IdP authentication |

The BFF should request short-lived OIDC access material, targeting a five-minute access-token lifetime where supported. A refresh token, when enabled, has a maximum seven-day lifetime, uses rotation where supported and remains server-side. The portal session limits above remain authoritative even if the IdP or Cloudflare session is longer.

A deployment may shorten these values without an architecture change. Increasing them requires a reviewed policy update and security tests.

### Immediate invalidation conditions

Every protected request fails closed when any of the following applies:

- local session is expired, idle-expired, revoked or structurally invalid;
- expected issuer, subject, audience or authentication context is missing or mismatched;
- mapped portal user is disabled;
- active tenant membership is absent, disabled or version-mismatched;
- requested capability is not present in the current server-side role mapping;
- back-channel logout or an administrative revocation has invalidated the IdP session;
- the session store or required membership source is unavailable for a privileged mutation.

Read-only behavior during a session-store outage may be introduced only by a separate reviewed availability policy. PI-06 v1 has no browser-trusted fallback.

## 6. Tenant and membership policy

The portal database is the source of truth for product tenancy and authorization.

Minimum records:

- `IdentityPrincipal`: portal user ID, OIDC issuer, OIDC subject, status and audit timestamps;
- `TenantMembership`: principal ID, tenant ID, role set, status, membership version and validity timestamps;
- `PortalSession`: hashed session ID, principal ID, active membership ID, IdP `sid` where available, authentication/MFA context, created/last-seen/absolute-expiry/revoked timestamps;
- `SessionRevocation`: principal/session/IdP-session scope, actor, reason and correlation context.

Rules:

- `(issuer, subject)` is globally unique within the portal identity store.
- One principal may have memberships in multiple tenants.
- Active tenant selection is allowed only from current server-side memberships.
- Tenant context is placed into the trusted request context by middleware, never copied from a browser `tenant_id` without validation.
- Role and capability evaluation uses the portal's current server-side permission model.
- IdP groups may assist bootstrap or operational routing but cannot silently create tenant membership on each login.
- Membership creation, role change, disable and deletion are audited.
- A membership or role change increments `membership_version` and synchronously revokes affected local sessions in v1.
- No positive authorization cache is used in v1. A later cache requires a maximum staleness bound, invalidation channel and denial tests.

The initial platform administrator is created through an explicit migration or restricted administrative command with audit evidence. First-login email matching does not create an administrator.

## 7. MFA and step-up policy

MFA is mandatory for every human principal holding at least one mutation or privileged capability, including current equivalents of:

- bot creation or lifecycle mutation;
- manual trade-intent submission;
- model training or promotion;
- risk-policy management;
- audit or platform administration where sensitive data is exposed;
- future exchange-secret, credential-broker or live-capital capabilities.

Preferred factor order:

1. WebAuthn/FIDO2/passkey or hardware security key;
2. TOTP as a compatibility fallback;
3. single-use recovery codes stored offline.

SMS and email OTP are not accepted as the sole MFA factor for privileged roles. Email may participate in account recovery but does not by itself satisfy privileged MFA.

High-impact actions require fresh authentication no older than five minutes. The initial list includes:

- adding/removing MFA authenticators;
- account recovery completion;
- tenant membership or role administration;
- future exchange credential creation/rotation/revocation;
- model promotion;
- any future live-capital authorization.

Normal page navigation is never evidence of MFA or authorization. The application validates authentication context and permission server-side.

## 8. Recovery and break-glass policy

The standard authentik recovery flow must use a generic response that does not reveal whether an account exists.

For a principal with MFA enrolled, recovery requires:

1. control of the verified recovery email channel;
2. successful validation of an existing MFA authenticator or a recovery code;
3. revocation of all prior portal sessions after credential recovery;
4. a security/audit event with no secret values.

When all MFA factors and recovery codes are unavailable, recovery is administrator-assisted. It requires separate identity verification, an audited reason, revocation of existing sessions and forced MFA re-enrollment. The portal must not implement security questions or an email-only privileged bypass.

A break-glass platform administrator is allowed only for recovery from IdP administration failure. It must:

- not be used for routine access;
- use at least two registered hardware authenticators where supported;
- have recovery material stored offline;
- be restricted by Cloudflare Access and network policy;
- generate alerts on every successful use;
- be reviewed and tested on a fixed schedule.

## 9. Revocation and logout policy

- Local logout revokes the local portal session first, then initiates IdP logout.
- `logout all` revokes every local session for the principal before attempting IdP-wide logout/revocation.
- authentik OIDC back-channel logout is registered and maps an IdP `sid` or subject to affected portal sessions.
- If authentik is unavailable during logout, local revocation still succeeds and future portal requests remain denied.
- Administrative user disable, membership disable, role reduction, suspected compromise and credential recovery revoke local sessions immediately.
- A service identity is not represented by a human browser session and requires a separate narrow machine identity contract.

Revocation events include actor, tenant where applicable, principal/session scope, reason code, request/correlation IDs and timestamps. Tokens, cookie values and recovery material are excluded.

## 10. Cloudflare Access boundary

Cloudflare Access is required as an additional gate for privileged deployment routes such as administration, research operations, infrastructure management and autonomous E2E control surfaces.

Policy requirements:

- explicit allow rules; no unrestricted one-time-password policy;
- MFA or an IdP authentication-method requirement for privileged users;
- short privileged Access session duration consistent with the four-hour portal maximum;
- service-auth credentials for machine clients, never reused human credentials;
- no Access `Bypass` policy on protected production-like routes;
- direct-origin ingress denied independently of Access;
- application session and RBAC checks still occur after Access succeeds.

Cloudflare identity headers or tokens may be validated as defense-in-depth context, but they do not create portal principals, memberships or capabilities.

## 11. Synology deployment posture

The selected target is a dedicated authentik Docker Compose stack on the Synology Linux container runtime or another Linux host.

Required deployment controls:

- pin an explicitly tested authentik image version and image digest; do not deploy an unbounded `latest` tag;
- dedicated PostgreSQL database/volume and dedicated application secret values;
- no committed passwords, client secrets, cookie keys or private endpoints;
- remove the Docker socket mount when automatic outpost management is not required, or use a narrowly configured socket proxy;
- expose authentik only through the intended Cloudflare Tunnel/private network route;
- restrict the administrative interface with Cloudflare Access;
- encrypted daily database/configuration backups and a quarterly restore exercise;
- stage upgrades before production-like use and follow supported sequential upgrade requirements;
- health checks for authentik server, worker and PostgreSQL;
- monitoring for login failures, MFA changes, session revocations and administrator actions.

Running authentik, the portal and their databases on one Synology host is accepted only for the current bounded development/test and small production-like target. It is a documented availability and blast-radius limitation. It cannot be used as evidence of high availability, P11 completion, PI-07 readiness or live-capital readiness.

## 12. PI-06 implementation sequence

A separate implementation task must use the following dependency order:

1. add versioned identity/session/membership contracts and database migrations;
2. implement server-side OIDC discovery, callback, PKCE/state/nonce validation and opaque local sessions;
3. replace the trusted development identity dependency on protected API routes;
4. enforce membership-derived tenant context and existing capabilities on every request;
5. implement CSRF protection for state-changing browser/BFF routes;
6. implement logout, logout-all, local revocation and OIDC back-channel logout;
7. add MFA/authentication-context and five-minute step-up enforcement for declared actions;
8. add audited membership administration and session revocation controls;
9. add deterministic IdP test doubles plus denied, expired, revoked, cross-tenant, recovery and back-channel-logout E2E;
10. add a separate Synology/authentik deployment package with secret placeholders and no credentials;
11. run real target-environment acceptance only after owner-managed authentik and Cloudflare resources exist.

The implementation must be split if one PR would combine database identity contracts, web login behavior and external deployment provisioning into an unreviewable change.

Recommended first implementation task:

`FTAI-YYYYMMDD-portal-pi06-product-identity-lifecycle`

## 13. PI-06 acceptance gates

PI-06 can be marked `done` only when:

1. protected APIs reject missing, expired and revoked sessions;
2. tenant context is derived exclusively from current portal membership;
3. cross-tenant requests fail closed in unit, integration and browser/security E2E;
4. privileged capabilities require the declared MFA context and step-up age;
5. membership and role changes revoke or invalidate affected sessions within the documented bound;
6. recovery does not reveal account existence or bypass privileged MFA;
7. local logout, logout-all and authentik back-channel logout are tested;
8. state-changing BFF routes have tested CSRF protection;
9. browser-visible storage and responses contain no IdP tokens, refresh tokens, client secrets or private endpoints;
10. unavailable identity/session infrastructure fails closed;
11. Cloudflare Access remains supplemental and direct origin remains denied in real P11 acceptance;
12. all required portal web, AI Platform, security, universal E2E and repository CI pass on the exact final implementation head.

## 14. Non-goals

- storing primary passwords in the portal database;
- using an email domain, IdP group or Cloudflare rule as automatic tenant authority;
- exposing authentik administration or tokens to browser code;
- implementing SCIM, enterprise federation or social login in the first package;
- implementing PI-05 external notification delivery;
- implementing PI-07 credential brokering or PI-08 execution submission;
- claiming real P11 acceptance from repository or fixture tests;
- enabling live capital.

## 15. Official references

- authentik OAuth2/OIDC provider: <https://docs.goauthentik.io/add-secure-apps/providers/oauth2/>
- authentik front-channel and back-channel logout: <https://docs.goauthentik.io/add-secure-apps/providers/oauth2/frontchannel_and_backchannel_logout/>
- authentik WebAuthn/FIDO2/passkeys: <https://docs.goauthentik.io/add-secure-apps/flows-stages/stages/authenticator_webauthn/>
- authentik TOTP: <https://docs.goauthentik.io/add-secure-apps/flows-stages/stages/authenticator_totp/>
- authentik authenticator validation and recovery-code support: <https://docs.goauthentik.io/add-secure-apps/flows-stages/stages/authenticator_validate/>
- authentik recovery-flow model: <https://docs.goauthentik.io/add-secure-apps/flows-stages/flow/>
- authentik Docker Compose deployment: <https://docs.goauthentik.io/install-config/install/docker-compose/>
- Cloudflare Access policies: <https://developers.cloudflare.com/cloudflare-one/access-controls/policies/>
- Cloudflare Access MFA enforcement: <https://developers.cloudflare.com/cloudflare-one/access-controls/policies/mfa-requirements/>
- Auth0 Organizations: <https://auth0.com/docs/manage-users/organizations>
- Auth0 session management: <https://auth0.com/docs/manage-users/sessions/manage-user-sessions-with-auth0-management-api>
- Keycloak server administration: <https://www.keycloak.org/docs/latest/server_admin/>
- Keycloak OIDC endpoints and revocation: <https://www.keycloak.org/securing-apps/oidc-layers>
