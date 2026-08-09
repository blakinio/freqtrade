# AI Trading Portal — Security Architecture

> [!IMPORTANT]
> ADR-020 and `RUNTIME_ISOLATION_AND_SUPERVISOR_CONTRACT.md` are the binding security overlay for Portal-managed Freqtrade dry-run runtimes. They require generation-bound isolation, a narrow Runtime Supervisor, generation-local Gateway/API credentials, public-data-only exchange connectivity in current dry-run scope and effective host-enforcement attestation. Documentation does not prove deployment or authorize live capital.

## 1. Security objective

Protect four distinct high-value assets:

1. user identity and tenant data;
2. exchange credentials and capital authority;
3. production execution/control surfaces;
4. AI/model lifecycle integrity.

Security is fail-closed. A component that cannot prove identity, tenant, authorization, artifact integrity, generation identity, required isolation or runtime health must not silently continue a privileged operation.

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

Public browser traffic terminates at the portal boundary. There is no public route to Freqtrade runtimes, Runtime Gateway, Runtime Supervisor, databases, event brokers, model registries, workers or secret stores.

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

Runtime Supervisor is not one of these browser/admin surfaces. It is a host-local/private machine boundary reachable only by the authorized runtime-lifecycle worker identity through the ADR-020 transport contract.

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
- emergency stop may be granted more broadly than restart/re-enable;
- application capabilities do not imply raw container-engine authority;
- only the Runtime Supervisor service identity owns Portal runtime container-engine lifecycle authority.

## 6. Tenant isolation

Every tenant-owned resource carries `tenant_id`.

Defense-in-depth controls:

- request-scoped tenant context established from authenticated identity;
- repository/query APIs require tenant scope;
- PostgreSQL row-level security evaluated for sensitive tables;
- object-storage keys/namespaces include non-guessable tenant scope;
- events include tenant scope but never secrets;
- logs avoid cross-tenant payload leakage;
- E2E includes User A -> User B denial tests;
- `RuntimeGeneration` and Supervisor operations bind exact tenant + bot + generation identity;
- one bot cannot have two different generations simultaneously in execution-owned active states;
- runtime networks cannot reach unrelated tenant/bot generations.

No administrative bypass is hidden inside normal application code paths.

## 7. Exchange credential boundary

Exchange credentials are among the highest-value secrets.

The generic future private-trading secret flow is:

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
separately authorized private-trading credential boundary
  |
  v
Specific authorized execution runtime
```

Rules:

- the secret value is never returned to the browser after storage;
- plaintext secrets are not written to Git, logs, events or audit payloads;
- credentials are injected only into a runtime explicitly authorized to use them;
- withdrawal permission must be disabled;
- research/training workloads cannot read production exchange credentials;
- rotation produces auditable secret-version changes;
- secret references are tenant-scoped;
- compromise response includes immediate credential revocation and bot kill switch.

### Current Portal dry-run rule

ADR-020 distinguishes:

```text
PUBLIC_DATA
PRIVATE_TRADING
```

Portal-managed dry-run Freqtrade uses `PUBLIC_DATA` and does **not** receive private exchange key/secret material. `PRIVATE_TRADING` remains a separate future authority and is not activated by the dry-run architecture, runtime isolation profile or Supervisor.

## 8. Freqtrade, Gateway and Runtime Supervisor security boundaries

Freqtrade remains private.

```text
Public Internet     X----> Freqtrade
Browser             X----> Freqtrade
Portal API          X----> Freqtrade
Research worker     X----> Freqtrade control API
Portal worker       X----> direct Freqtrade API

Portal worker ----generation UDS----> Runtime Gateway ----private----> Freqtrade
Portal worker ----Supervisor UDS----> Runtime Supervisor ----> container engine
```

### Freqtrade requirements

- no published host/public Freqtrade control port;
- exact generation-local Gateway relationship only;
- generation-local Freqtrade API credential;
- private generation networking;
- deny-by-default network policy;
- request/generation correlation and audit at the Gateway boundary;
- rate/command limiting for high-impact Gateway operations;
- no general reverse-proxy exposure;
- no Docker/container-engine socket;
- no Portal DB, Vault, Redis, NATS or unrelated-runtime reachability.

### Generation-local API credential

The Freqtrade API credential:

- is rotated per generation;
- is available only to Freqtrade and its Gateway;
- is absent from Docker labels and CLI;
- is not stored in inspectable environment variables;
- is not part of canonical `RuntimeGeneration` evidence;
- is carried through an approved ephemeral generation-secret boundary.

The Supervisor may manage lifecycle/reference plumbing for this secret boundary but must not receive plaintext credential material through its API or persist plaintext in Supervisor state.

### Runtime Supervisor requirements

Runtime Supervisor is the sole Portal component with container-engine authority and has no:

- exchange trading credentials;
- Vault token/SecretID/general secret-store authority;
- browser/OIDC session;
- training/model credentials;
- general NATS/Redis credentials;
- arbitrary Portal DB write authority;
- git/registry credentials;
- live-capital authority.

Its logical API accepts exact generation identity/lifecycle operations only. Raw image, mount, command, environment, port, network, capability, privileged/device or engine parameters are not accepted request fields.

Single-host transport uses Unix domain socket + filesystem ACL + OS peer credentials. Future multi-host transport requires mTLS/workload identity and explicit service authorization. Public/plain-HTTP Supervisor endpoints are forbidden.

## 9. Runtime process/filesystem/resource isolation

Every executable `RuntimeGeneration` binds an immutable `RuntimeIsolationProfile` and a resolved immutable `RuntimeIsolationPlan`.

### Security invariants

The baseline has no downgrade fallback for:

- non-root process;
- `privileged=false`;
- `no-new-privileges`;
- capability drop `ALL` / add none;
- read-only root filesystem;
- no host network/PID/IPC/UTS namespace;
- no host device passthrough;
- no Docker/container-engine socket;
- no arbitrary mount/host path;
- no `seccomp=unconfined`;
- immutable image content identity;
- no public/host Freqtrade port.

If the host cannot enforce a required invariant, the runtime does not start.

### Resource hard containment

The resolved profile/plan requires effective hard containment for:

- CPU;
- memory;
- swap disabled or explicitly bounded;
- PID/process count;
- generation-scoped durable state;
- logs;
- tmpfs/ephemeral storage.

Host-capability alternatives may be selected only from profile-approved mechanisms that preserve the required semantic bound. CPU shares/weight alone are not a hard CPU limit. Monitoring disk/log growth without a hard backend is not hard containment.

### Trust-separated storage

```text
CONTROL-OWNED
  RuntimeGeneration / canonical manifest / provenance
  not writable by Freqtrade; preferably not mounted

IMMUTABLE INPUT
  non-secret config / strategy / model
  read-only

DURABLE WRITABLE
  Freqtrade DB/state
  generation-scoped + hard bounded

EPHEMERAL
  tmp/cache/run/log resources
  explicitly bounded

SECRET
  generation-local runtime API material
  separate ephemeral boundary
```

Mount paths are derived by the Supervisor from fixed approved roots and trusted digests/IDs. Request-supplied host paths do not exist in the API. Implementations must prevent `..`, symlink or equivalent escape from approved roots.

### Hardened Portal image

The repository root Freqtrade Dockerfile is not the Portal security baseline because it currently gives `ftuser` sudo membership and passwordless `/bin/chown` capability. Portal-managed Freqtrade uses a separate approved immutable hardened runtime image with dedicated non-root user and no runtime dependency on sudo/NOPASSWD, compiler/build chain, registry credentials or package-manager mutation.

Launch-time `no-new-privileges`, capability drop and read-only-root controls remain mandatory even with the hardened image.

## 10. Host capability and effective isolation attestation

The Control Plane does not guess host support. Runtime Supervisor produces a point-in-time `RuntimeHostCapabilityReport` containing host/boot identity, engine/cgroup information and supported hard-control mechanisms.

A versioned resolver combines the approved profile with the capability report to create a stable abstract `RuntimeIsolationPlan`. The plan digest describes canonical resolved security/resource semantics, not volatile report timestamps/IDs or host identity.

Provisioning uses two attestation stages:

1. **structural/static attestation** after creation: image/user/security options/capabilities/namespaces/mounts/networks/ports/requested resource controls/restart policy;
2. **effective enforcement attestation** before operational acceptance: actual cgroup CPU/memory/swap/PID controls, storage quota/bounded volume, tmpfs/log bound and active network/egress enforcement.

Configured Compose/Docker values and `docker inspect` output are insufficient where the host/kernel may silently discard or fail to enforce them.

Current WH09 evidence demonstrates the risk:

- PR #1392 records the Synology target rejecting CPU CFS/NanoCPUs;
- diagnostic PR #1394 reports the later host run discarded the configured PID limit.

These observations do not authorize weaker Portal isolation. They require capability-aware fail-closed planning and effective attestation.

## 11. Network segmentation and market-data egress

Minimum logical zones remain:

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
- authorized runtime-lifecycle worker -> Runtime Supervisor UDS: allowed;
- authorized worker -> exact generation Gateway UDS: allowed;
- Gateway -> its exact Freqtrade runtime: allowed;
- Freqtrade -> approved public market-data endpoints: allowed under versioned egress policy;
- generation -> Portal DB/Vault/NATS/Redis/container-engine/management: denied;
- generation -> unrelated runtime: denied;
- research -> production secret store: denied;
- browser -> data plane/Freqtrade/Gateway/Supervisor: denied.

Every generation has its own isolated network relationship and binds a versioned `MarketDataEgressPolicy`.

Baseline egress intent:

```text
ALLOW
  required public exchange/market-data connectivity
  approved DNS resolution

DENY
  Portal/control/data/management networks
  host-management endpoints
  container engine
  Vault/PostgreSQL/Redis/NATS
  unrelated generations
  private/link-local/metadata endpoints
```

The deny boundary applies to IPv4 and IPv6. DNS must not provide a bypass to forbidden ranges. A normal Docker bridge alone is not proof of deny-by-default egress; the resolved isolation plan identifies an approved effective firewall/eBPF/proxy or equivalent enforcement backend.

## 12. Runtime lifecycle safety

Portal-managed Freqtrade uses engine restart policy:

```text
restart = NO
```

Container engine restart must not resurrect historical generations independently. Recovery is owned by Control Plane desired state + reconciliation + Runtime Supervisor.

Replacement is explicit stop-then-provision/start. There is no raw/magical `Replace` or `Restart` operation that hides rollout state transitions.

For one tenant+bot, a second generation cannot enter an execution-owned active state while another distinct generation remains active. Supervisor returns a conflict and does not auto-stop the incumbent generation.

Retired generations cannot be reprovisioned/restarted by stale queued work. Idempotency/command identities replay safely and conflicting reuse fails closed.

Runtime Supervisor lifecycle/container state is not authoritative trading truth. Positions, orders, trades, valuation and execution success come from generation Gateway + authoritative reconciliation.

## 13. AI/model supply-chain security

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

Runtime generations load only exact artifacts allowed by policy. A missing or mismatched hash fails closed.

The same immutable-content rule applies to the Portal-managed Freqtrade image. The Runtime Supervisor does not pull/build images; a missing exact pre-delivered image returns `IMAGE_NOT_PRESENT`.

A training worker cannot directly relabel itself as `production` or mutate a running generation.

## 14. Autonomous-agent security

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
- protected-host/runtime mutation;
- exchange-secret retrieval;
- live-capital enablement;
- CI bypass;
- branch-protection bypass;
- deleting negative evidence;
- weakening assertions merely to turn tests green;
- self-approving a model promotion where independent approval is required.

Agent actions are auditable with actor type, task ID and correlation ID.

## 15. WAF and rate-limiting policy families

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

Runtime Supervisor and Gateway are not routed through public WAF/browser ingress; they are private machine boundaries with their own transport/identity controls.

Rate-limit keys may include authenticated identity, tenant, API token and IP depending on route semantics. Limits must not become the only authorization mechanism.

Webhook ingestion additionally requires:

- unguessable endpoint identity;
- request authentication/signature where integration permits;
- replay protection/idempotency key;
- timestamp/nonce policy;
- per-tenant rate limits;
- strict schema validation.

## 16. Audit architecture

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
- bot lifecycle / rollout / generation changes;
- isolation plan/profile and attestation results;
- risk policy changes;
- manual trading intents;
- model promotion/rollback;
- kill-switch activation;
- autonomous-agent patch/PR actions.

## 17. Kill switches

Provide hierarchical emergency controls:

```text
platform kill switch
  -> tenant kill switch
      -> exchange-connection kill switch
          -> bot kill switch
```

A kill switch blocks new risk exposure. Exit/position-reduction behavior is separately defined so an emergency stop does not accidentally prevent risk-reducing actions.

ADR-020 additionally requires a monotonic `ExecutionSafetyEpoch`. Exposure-increasing generation-bound commands carry the current epoch; stale epochs fail closed. Release creates a new epoch so old pending approvals cannot replay.

Activation is immediate, auditable and visible in the portal.

## 18. Security validation

Required automated scenarios retain the existing identity/tenant/model/risk acceptance and add the ADR-020 runtime-isolation suite.

Baseline security scenarios include:

- unauthenticated access denied;
- expired/revoked session denied;
- invalid MFA denied;
- CSRF attempt denied;
- tenant cross-access denied;
- role escalation denied;
- browser cannot reach Freqtrade, Runtime Gateway or Runtime Supervisor;
- public Internet cannot reach Freqtrade, Runtime Gateway or Runtime Supervisor;
- research worker cannot obtain production exchange secret;
- webhook replay rejected;
- invalid model artifact hash rejected;
- unauthorized model promotion rejected;
- kill switch blocks new entries;
- audit event emitted for every privileged action.

Minimum negative runtime scenarios include:

- root/privileged/capability-add/no-new-privileges bypass denied;
- writable root/host PID/IPC/UTS/network/device access denied;
- Docker socket, `/etc`, arbitrary bind mount and path/symlink escape denied;
- arbitrary image/tag-only image/command/env/network/port controls denied;
- Portal DB/Vault/NATS/Redis/other-generation/private/metadata network access denied;
- immutable config/control evidence write denied;
- PID/memory/swap/CPU/state/log/tmpfs exhaustion contained;
- stale capability report or plan mismatch denied;
- configured-but-not-effective host enforcement fails attestation;
- stale/retired generation restart denied;
- concurrent G1/G2 activation denied;
- conflicting idempotency/command replay denied.

Minimum positive runtime scenarios include:

- hardened Freqtrade boot;
- approved `PUBLIC_DATA` market connectivity;
- exact generation Gateway path;
- provision/start/pause/stop idempotency;
- generation-local durable state persistence;
- Supervisor restart/recovery;
- exact-plan recovery on a compatible host;
- new generation required when the isolation/security envelope changes.

Production-like staging should exercise the real external Cloudflare-protected path and real target-host isolation attestation while using simulated/dry-run capital authority only.

## 19. Security invariants

1. Edge protection cannot be bypassed through an accidentally exposed origin path.
2. Cloudflare Access is not a substitute for application RBAC.
3. Freqtrade, Runtime Gateway and Runtime Supervisor are not public APIs.
4. Runtime Supervisor is the only Portal component with container-engine lifecycle authority.
5. Secrets do not cross into browser-visible, event, log, Docker-label, CLI or canonical-generation payloads.
6. Current Portal dry-run uses public exchange data and no private exchange trading credentials.
7. Research/training and private execution credentials/authorities are separated.
8. Every executable RuntimeGeneration binds immutable isolation profile and resolved-plan identity.
9. Missing or unverifiable hard runtime containment fails closed; requested configuration alone is not enforcement proof.
10. Runtime control evidence is not runtime-writable; durable Freqtrade state is generation-scoped and bounded.
11. Freqtrade has no host/public port and generation egress cannot reach Portal/control/data/management services.
12. AI cannot bypass deterministic risk controls or execution-safety fencing.
13. Agents cannot bypass CI/promotion/deployment policy.
14. Supervisor/container state never substitutes for Gateway/reconciliation trading truth.
15. Live capital requires an explicit separately reviewed authorization boundary.
