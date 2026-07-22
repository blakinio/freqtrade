# AI Trading Portal — Security Architecture

## 1. Security objective

Protect four distinct high-value assets:

1. user identity and tenant data;
2. exchange credentials and capital authority;
3. production execution/control surfaces;
4. AI/model lifecycle integrity.

Security is fail-closed. A component that cannot prove identity, tenant, authorization, artifact integrity or runtime health must not silently continue a privileged operation.

## 2. External edge

Target public ingress:

```text
Internet
   |
   v
Cloudflare
  - authoritative/proxied DNS
  - TLS
  - DDoS protection
  - WAF
  - rate limiting
  - bot/abuse controls where appropriate
   |
   v
Cloudflare Tunnel
  - outbound origin connection
  - no required public inbound application port
   |
   v
Private origin ingress
   |
   +--> portal-web
   +--> portal-api
```

The origin should not expose a separate direct path that bypasses Cloudflare protections. Firewall and network policy must reject unintended public ingress.

Public browser traffic terminates at the portal boundary. There is no public route to Freqtrade runtimes, databases, event brokers, model registries, workers or secret stores.

## 3. Privileged surfaces

Privileged surfaces are separated from the customer/user portal:

```text
Admin
Research console
Model promotion
Infrastructure operations
E2E control surface
        |
        v
Cloudflare Access / Zero Trust
        |
        +--> IdP identity
        +--> MFA
        +--> group/role policy
        +--> device posture where available
        |
        v
Privileged private application
```

Cloudflare Access supplements application authorization; it does not replace server-side RBAC or tenant checks.

Machine-to-machine clients that must cross an Access boundary use dedicated non-human service credentials with narrow policies and rotation/revocation procedures. Human credentials are not reused by automation.

## 4. Identity and session security

The product identity layer must support OIDC/OAuth2-compatible identity and MFA.

Application requirements:

- secure, HttpOnly, SameSite session cookies;
- CSRF protection for state-changing browser operations;
- short-lived access/session material with controlled refresh;
- session revocation;
- MFA for privileged roles;
- re-authentication for high-impact operations where appropriate;
- server-side authorization on every protected resource;
- login and recovery abuse controls;
- security event emission for authentication anomalies.

Cloudflare Access is intended for administrative/research surfaces. End-user product identity remains an application concern so the platform is not coupled to an infrastructure access product for customer authentication.

## 5. Authorization model

Initial roles:

```text
viewer
trader
analyst
model_reviewer
operator
security_admin
platform_admin
```

Authorization is capability-based, not only page-based.

Examples:

```text
bot.read
bot.configure
bot.start_stop
terminal.submit_intent
exchange.create
exchange.rotate_secret
model.read
model.train
model.validate
model.promote
risk_policy.manage
audit.read
platform.admin
```

Rules:

- frontend visibility is never the enforcement boundary;
- background jobs preserve actor and tenant context;
- privilege escalation paths require explicit authorization;
- model promotion and live-capital authorization are separate capabilities;
- emergency stop may be granted more broadly than restart/re-enable.

## 6. Tenant isolation

Every tenant-owned resource carries `tenant_id`.

Defense-in-depth controls:

- request-scoped tenant context established from authenticated identity;
- repository/query APIs require tenant scope;
- PostgreSQL row-level security evaluated for sensitive tables;
- object-storage keys/namespaces include non-guessable tenant scope;
- events include tenant scope but never secrets;
- logs avoid cross-tenant payload leakage;
- E2E includes User A -> User B denial tests.

No administrative bypass is hidden inside normal application code paths.

## 7. Exchange credential boundary

Exchange credentials are among the highest-value secrets.

Required flow:

```text
Browser
  |
  | one-time secret submission over TLS
  v
Portal API
  |
  v
Secret Store / KMS envelope encryption
  |
  +--> opaque secret reference stored in Portal DB
  |
  v
Runtime credential broker/injection
  |
  v
Specific Freqtrade runtime
```

Rules:

- the secret value is never returned to the browser after storage;
- plaintext secrets are not written to Git, logs, events or audit payloads;
- credentials are injected only into the runtime that needs them;
- withdrawal permission must be disabled;
- research/training workloads cannot read production exchange credentials;
- rotation produces auditable secret-version changes;
- secret references are tenant-scoped;
- compromise response includes immediate credential revocation and bot kill switch.

## 8. Freqtrade security boundary

Freqtrade remains private.

```text
Public Internet     X----> Freqtrade
Browser             X----> Freqtrade
Research worker     X----> production Freqtrade control API

Portal execution adapter ----private authenticated path----> Freqtrade
Internal event collector ----private authenticated path----> Freqtrade WS/events
```

Requirements:

- no published Freqtrade control port;
- per-runtime or per-environment credentials;
- private DNS/networking;
- deny-by-default network policy;
- API/WS credentials stored in secret management;
- request correlation and audit at the adapter boundary;
- rate/command limiting for high-impact control operations.

## 9. Network segmentation

Minimum logical zones:

```text
edge
portal
control
execution
research
training-gpu
data
observability
management
```

Expected communication is allow-listed.

Examples:

- `portal-web -> portal-api`: allowed;
- `portal-api -> postgres`: allowed;
- `portal-api -> execution adapter`: allowed;
- `execution adapter -> Freqtrade runtimes`: allowed;
- `Freqtrade -> exchange Internet endpoints`: allowed under egress policy;
- `research -> production secret store`: denied;
- `browser -> data plane`: denied;
- `browser -> Freqtrade`: denied.

## 10. AI/model supply-chain security

Model artifacts are executable-adjacent supply-chain inputs and require integrity controls.

Each model version records:

- immutable model ID/version;
- artifact hash;
- code revision;
- feature schema version;
- target definition;
- training dataset identity;
- training job identity;
- validation evidence;
- lifecycle state;
- signer/provenance metadata where available.

Production runtimes load only artifacts allowed by policy. A missing or mismatched hash fails closed.

A training worker cannot directly relabel itself as `production`.

## 11. Autonomous-agent security

Autonomous agents are treated as untrusted-but-useful operators with bounded capabilities.

Allowed, subject to task scope:

- read repository and evidence;
- create isolated branches;
- add regression tests;
- modify owned paths;
- run validation;
- create/update PRs.

Not allowed by default:

- direct production deployment;
- exchange-secret retrieval;
- live-capital enablement;
- CI bypass;
- branch-protection bypass;
- deleting negative evidence;
- weakening assertions merely to turn tests green;
- self-approving a model promotion where independent approval is required.

Agent actions are auditable with actor type, task ID and correlation ID.

## 12. WAF and rate-limiting policy families

Edge controls should be risk-based rather than one global threshold.

High-priority protected routes:

- authentication and password recovery;
- MFA enrollment/challenge;
- exchange credential creation/rotation;
- bot create/start/stop;
- terminal order-intent submission;
- webhook/signal ingestion;
- model promotion;
- admin APIs.

Rate-limit keys may include authenticated identity, tenant, API token and IP depending on route semantics. Limits must not become the only authorization mechanism.

Webhook ingestion additionally requires:

- unguessable endpoint identity;
- request authentication/signature where integration permits;
- replay protection/idempotency key;
- timestamp/nonce policy;
- per-tenant rate limits;
- strict schema validation.

## 13. Audit architecture

Security-sensitive operations produce append-only audit events.

Minimum fields:

```text
audit_id
occurred_at
actor_type
actor_id
tenant_id
session_or_service_identity
action
resource_type
resource_id
request_correlation_id
result
reason_code
source_ip_metadata where lawful/appropriate
before_hash
after_hash
```

Secrets and raw credentials are forbidden in audit payloads.

High-value events include:

- authentication and MFA changes;
- role/capability changes;
- exchange credential changes;
- bot lifecycle changes;
- risk policy changes;
- manual trading intents;
- model promotion/rollback;
- kill-switch activation;
- autonomous-agent patch/PR actions.

## 14. Kill switches

Provide hierarchical emergency controls:

```text
platform kill switch
  -> tenant kill switch
      -> exchange-connection kill switch
          -> bot kill switch
```

A kill switch blocks new risk exposure. Exit/position-reduction behavior is separately defined so an emergency stop does not accidentally prevent risk-reducing actions.

Activation is immediate, auditable and visible in the portal.

## 15. Security validation

Required automated scenarios include:

- unauthenticated access denied;
- expired/revoked session denied;
- invalid MFA denied;
- CSRF attempt denied;
- tenant cross-access denied;
- role escalation denied;
- browser cannot reach Freqtrade;
- public Internet cannot reach Freqtrade;
- research worker cannot obtain production exchange secret;
- webhook replay rejected;
- invalid model artifact hash rejected;
- unauthorized model promotion rejected;
- kill switch blocks new entries;
- audit event emitted for every privileged action.

Production-like staging should exercise the real external Cloudflare-protected path while using simulated exchange capital by default.

## 16. Security invariants

1. Edge protection cannot be bypassed through an accidentally exposed origin path.
2. Cloudflare Access is not a substitute for application RBAC.
3. Freqtrade is not a public API.
4. Secrets do not cross into browser-visible, event or log payloads.
5. Research and production credentials are separated.
6. AI cannot bypass deterministic risk controls.
7. Agents cannot bypass CI/promotion policy.
8. Live capital requires an explicit separately reviewed authorization boundary.
