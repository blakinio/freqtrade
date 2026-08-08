# AI Trading Portal — System Architecture

> [!IMPORTANT]
> ADR-020 and `RUNTIME_ISOLATION_AND_SUPERVISOR_CONTRACT.md` are the binding execution-plane overlay for Portal-managed dry-run runtimes. Where older generic execution-adapter, credential, runtime-identity or container-isolation wording conflicts, the ADR-020 contracts take precedence. Target wording does not prove implementation.

## 1. Architectural objective

Build a modern, secure and evolvable trading platform that presents a coherent product experience while keeping Freqtrade, model training, execution credentials and autonomous agents behind explicit trust and policy boundaries.

The architecture must support:

- multiple users/organizations in the future;
- multiple exchange connections per tenant;
- independently managed AI and non-AI bots;
- isolated Freqtrade execution runtimes;
- deterministic risk gates;
- reproducible training and model promotion;
- post-trade diagnosis and continual-learning inputs;
- real-time telemetry and notifications;
- full-platform E2E and autonomous diagnosis/repair workflows;
- Cloudflare-protected public access with no direct public Freqtrade exposure.

## 2. Target logical architecture

```text
                                      INTERNET
                                         |
                                         v
                              +-----------------------+
                              |      Cloudflare       |
                              | DNS/TLS/DDoS/WAF/Rate |
                              +-----------+-----------+
                                          |
                               Cloudflare Tunnel
                                          |
                                          v
+----------------------------------------------------------------------------------+
|                              PORTAL / UX PLANE                                   |
|                                                                                  |
|  Next.js Web Portal ---> Portal BFF/API ---> Identity session / tenant context   |
+-------------------------------+--------------------------------------------------+
                                |
                                v
+----------------------------------------------------------------------------------+
|                                CONTROL PLANE                                     |
|                                                                                  |
| Bot Service | Exchange Connection Service | Risk Policy | Model Assignment       |
| Analytics API | Notification Service | Audit | Workflow / Bot Orchestrator       |
+--------------------------+----------------------+--------------------------------+
                           |                      |
                           | events               | desired state / lifecycle
                           v                      v
                 +------------------+    +-----------------------------+
                 | Event Bus        |    |       Portal Worker         |
                 | NATS JetStream   |    | orchestration/reconcile     |
                 +---------+--------+    +--------------+--------------+
                           |                            |
                           |                    +-------+-------+
                           |                    |               |
                           |                    v               v
                           |             Runtime Gateway   Runtime Supervisor
                           |                    |               |
                           |                    v               v
+----------------------------------------------------------------------------------+
|                               EXECUTION PLANE                                    |
|                                                                                  |
|      RuntimeGeneration A      RuntimeGeneration B      RuntimeGeneration N       |
|      Gateway + Freqtrade      Gateway + Freqtrade      Gateway + Freqtrade       |
|      immutable isolation      immutable isolation      immutable isolation       |
|      private generation net   private generation net   private generation net    |
|             |                         |                         |                 |
|             +-------------------------+-------------------------+                 |
|                                       |                                           |
|                         approved public market-data egress                       |
+----------------------------------------------------------------------------------+

+----------------------------------------------------------------------------------+
|                              AI / RESEARCH PLANE                                 |
|                                                                                  |
| Market Data -> Dataset Registry -> Feature Pipeline -> Training Jobs              |
|                                             |                                     |
|                              LightGBM / XGBoost / PyTorch / RL                   |
|                                             |                                     |
| Experiment Registry -> Validation Gates -> Model Registry -> Promotion           |
+----------------------------------------------------------------------------------+

+----------------------------------------------------------------------------------+
|                                  DATA PLANE                                      |
|                                                                                  |
| PostgreSQL/Timescale | Object Storage | Redis | Event Store | Audit | Telemetry   |
+----------------------------------------------------------------------------------+

+----------------------------------------------------------------------------------+
|                        QUALITY & AUTONOMOUS VALIDATION                           |
|                                                                                  |
| Exchange Simulator | Market Scenarios | Playwright E2E | Security E2E            |
| Failure Evidence -> AI Diagnosis -> Regression Test -> Patch Branch -> PR         |
+----------------------------------------------------------------------------------+
```

`Runtime Supervisor` is the only Portal component with container-engine authority. The per-generation Gateway is the only Portal-to-Freqtrade application boundary. These security-oriented process profiles refine, rather than abandon, the modular-monolith control-plane architecture.

## 3. Architectural style

### 3.1 Modular monolith first

The initial control plane should be one deployable backend with strict internal module boundaries. This minimizes operational complexity while preserving later service extraction.

Initial backend modules:

```text
identity_context
organizations
exchange_connections
bots
bot_configs
execution
risk
strategies
models
training_control
analytics
trade_intelligence
notifications
audit
admin
```

Rules:

- modules communicate through explicit application interfaces;
- shared database access does not authorize cross-module table ownership violations;
- external contracts are versioned;
- domain events are emitted through an outbox pattern;
- long-running work is asynchronous and idempotent;
- no frontend code knows Freqtrade-specific credentials or internal runtime addresses.

A module becomes a separate service only when scaling, security or independent release requirements justify it. ADR-020 exercises that criterion only for the narrow Runtime Supervisor and per-generation Gateway trust boundaries; it does not authorize broad domain microservice decomposition.

### 3.2 Recommended technology baseline

Target baseline, subject to implementation validation:

- **Web:** Next.js + React + TypeScript.
- **Portal API/control plane:** FastAPI + Python.
- **Primary metadata database:** PostgreSQL.
- **Time-series extension:** TimescaleDB where justified; plain PostgreSQL first is acceptable.
- **Event transport:** NATS JetStream.
- **Cache/ephemeral coordination:** Redis.
- **Artifact storage:** S3-compatible object storage.
- **Workflow execution:** durable background worker abstraction; adopt a dedicated workflow engine only when provisioning/training workflows require durable multi-step orchestration beyond the initial worker model.
- **Observability:** OpenTelemetry instrumentation with Prometheus-compatible metrics and centralized logs/traces.
- **Execution packaging:** Docker initially; Kubernetes-compatible contracts without requiring Kubernetes for MVP.

Technology selection must not weaken the domain boundaries in this document or the accepted runtime isolation contract.

## 4. Portal / UX Plane

The browser communicates only with the portal BFF/API.

Responsibilities:

- authentication/session handling;
- tenant context;
- coarse UI authorization hints;
- dashboard aggregation;
- bot and model management workflows;
- trading terminal commands;
- AI insight presentation;
- logs and observability views;
- notifications;
- administrative surfaces.

The browser must never receive:

- exchange API secrets;
- Freqtrade REST credentials;
- Freqtrade WebSocket tokens;
- private runtime hostnames;
- Runtime Supervisor endpoints/credentials;
- infrastructure service credentials;
- model-registry write credentials.

## 5. Control Plane

### 5.1 Bot domain

A portal bot is a declarative resource, not a direct representation of an internal Freqtrade process.

Canonical shape:

```text
BotInstance
  id
  tenant_id
  name
  strategy_version_id
  model_version_id | null
  exchange_connection_id
  pair_policy
  timeframe_policy
  capital_policy_id
  risk_policy_id
  runtime_version
  desired_state
  observed_state
  config_revision
```

Desired states:

```text
CREATED
RUNNING
PAUSED
STOPPED
RETIRED
```

Observed runtime states:

```text
PENDING
PROVISIONING
STARTING
HEALTHY
DEGRADED
PAUSED
STOPPING
STOPPED
ERROR
```

The orchestrator reconciles desired and observed state. UI requests change intent; they do not directly manipulate containers.

ADR-020 additionally separates latest/authored revision, desired revision/generation and observed active generation. `RuntimeGeneration` is the immutable execution identity; a saved draft does not become executable automatically.

### 5.2 Bot configuration revisions

Every material bot configuration change creates an immutable revision:

```text
BotConfigRevision
  bot_id
  revision
  strategy_version_id
  model_version_id
  feature_schema_version
  risk_policy_version
  exchange_connection_ref
  normalized_config
  artifact_hashes
  created_by
  created_at
```

A running bot is always attributable to one exact revision and one exact `RuntimeGeneration`.

### 5.3 Execution adapter

Portal-facing execution contracts remain engine-independent. The historical/internal `ExecutionAdapter` abstraction may expose lifecycle/read/submit semantics, but ADR-020 splits their privileged implementation across two narrower boundaries:

```text
lifecycle materialization
  Portal Worker -> Runtime Supervisor -> container engine

application/runtime reads and approved commands
  Portal Worker -> generation Gateway -> Freqtrade private API
```

Normal Portal processes do not call Docker/container-engine APIs and do not call Freqtrade directly.

Logical product capabilities remain equivalent to:

```text
provision exact generation
start/pause/stop exact generation
get lifecycle/health evidence
submit approved generation-bound intent
get open positions/orders/trades through Gateway
```

The Gateway is not a raw reverse proxy and the Supervisor is not an arbitrary container API.

At the trusted task base, the existing `FreqtradeExecutionAdapter` still represents pre-ADR-020 implementation state: it implements bounded private dry-run lifecycle/health, while direct approved-intent order submission and portfolio/order/trade query coverage remain fail-closed/incomplete as recorded by exact current code and tests. That legacy state is evidence of implementation progress, not the final ADR-020 security topology.

Current implementation completeness must be established from exact code/test/deployment evidence. Older repository adapters that predate ADR-020 must not be represented as the final composed security boundary merely because their interface exists.

## 6. Execution Plane

### 6.1 Isolation unit

The default initial isolation unit is:

```text
one BotInstance -> one active RuntimeGeneration -> one isolated Freqtrade runtime + Gateway
```

Reasons:

- independent restart and rollout;
- per-bot strategy/model/config/isolation-plan pinning;
- clear resource and log attribution;
- fault containment;
- generation-local runtime API secret scoping;
- easier rollback and incident isolation.

Later optimization may group compatible workloads only after proving that isolation and attribution remain intact and after a separate architecture decision.

### 6.2 Runtime rules

Each Portal-managed dry-run runtime must:

- be reachable only through its private generation-local relationship;
- default to dry-run unless a separately approved lifecycle state authorizes otherwise;
- use `PUBLIC_DATA` exchange connectivity without private exchange trading credentials in the current dry-run scope;
- use immutable strategy/model/config/image/risk/isolation identities;
- bind an immutable `RuntimeIsolationProfile` and resolved `RuntimeIsolationPlan`;
- expose Freqtrade application access only to its generation-local Gateway;
- expose lifecycle state only through the Runtime Supervisor boundary;
- emit correlation/generation-aware evidence;
- be replaceable rather than manually mutated in place;
- use engine restart policy `NO`, with recovery owned by desired-state reconciliation.

Private exchange trading credentials remain a separately governed future authority and are not introduced by dry-run runtime provisioning.

### 6.3 Runtime isolation and Supervisor contract

`RUNTIME_ISOLATION_AND_SUPERVISOR_CONTRACT.md` is binding for the detailed dry-run execution envelope. Its required shape includes:

```text
RuntimeIsolationProfile (immutable/versioned)
        +
RuntimeHostCapabilityReport (Supervisor evidence)
        -> deterministic resolved RuntimeIsolationPlan
        -> immutable RuntimeGeneration with profile + plan digests
        -> EnsureProvisioned / structural attestation
        -> EnsureRunning / effective enforcement attestation
```

Security invariants have no fallback. Capability-resolved alternatives must be pre-approved and preserve the required hard bound. Missing effective CPU, memory/swap, PID, storage, log, tmpfs or network containment makes the host incompatible for the Portal runtime.

Configured Docker/Compose flags alone are not sufficient evidence. Post-create/post-start attestation must verify effective host/kernel enforcement. This rule is informed by current WH09 Synology evidence where CPU CFS/NanoCPUs was unavailable and a later diagnostic run reported the configured PID limit was discarded.

Runtime filesystem/storage classes are:

```text
control-owned evidence     NOT runtime writable / preferably not mounted
immutable runtime inputs   RO
durable Freqtrade state    RW, generation-scoped, hard bounded
ephemeral tmp/cache        bounded tmpfs/log resources
generation secrets         separate ephemeral secret boundary
```

Every generation has isolated networking and a versioned market-data egress policy. Freqtrade has no host/public port and cannot reach Portal DB, Vault, Redis, NATS, the container engine, host-management endpoints or unrelated generations.

## 7. Risk Plane

AI and strategy output a `TradeIntent`. The deterministic risk layer produces an `ApprovedExecutionIntent` or `RejectedExecutionIntent`.

```text
Prediction / strategy signal
          |
          v
      TradeIntent
          |
          v
       Risk Engine
      /           \
approved           rejected
    |                |
    v                v
ApprovedExecutionIntent   RejectedExecutionIntent
    |                |
    v                v
private execution    audit/reason
submitter boundary
```

Initial policy families:

- maximum exposure per bot/asset/tenant;
- maximum open positions;
- maximum leverage where leverage is later authorized;
- daily and rolling loss limits;
- maximum drawdown;
- stale data/model rejection;
- exchange health gate;
- liquidity/spread gate where data exists;
- cooldown after repeated losses;
- emergency kill switch.

Risk policy versions are immutable and independently auditable from model versions.

ADR-020 additionally requires exact generation and monotonic `ExecutionSafetyEpoch` fencing for exposure-increasing commands. Runtime/container state is not authoritative proof of orders, positions or execution success; Gateway plus reconciliation remains authoritative.

## 8. AI / Research Plane

The AI plane remains separate from execution authority.

```text
Data -> Features -> Training -> Candidate -> Validation -> Registry -> Promotion
                                                        |
                                                        v
                                                production-eligible
```

The portal may request training, display experiments and manage approved promotions, but the production runtime only consumes immutable promoted artifacts allowed by lifecycle policy.

Research compute must use credentials and networking separate from production exchange connectivity. Training/research workers have no Runtime Supervisor/container-engine authority for Portal-managed runtimes.

## 9. Data Plane

Authoritative ownership:

- **Portal PostgreSQL:** users, tenants, bots, revisions, `RuntimeGeneration`, desired/rollout state, policies, model metadata and audit indexes.
- **Freqtrade runtime DB:** generation-local execution evidence/state; durable writable storage is explicitly generation-scoped and bounded.
- **Portal trade mirror:** normalized cross-runtime query model; not a hidden rewrite of runtime truth.
- **Object storage:** model artifacts, datasets, manifests, backtests, E2E artifacts and large reports.
- **Event bus:** real-time domain/event distribution, not the only durable system of record.
- **Telemetry backend:** operational metrics/logs/traces.

The Runtime Supervisor may receive only a dedicated minimal read-only generation view required for safe materialization. It does not receive general Portal DB write authority.

Use an outbox/inbox pattern for state-changing event publication and idempotent consumers.

## 10. Real-time event model

Canonical event families:

```text
bot.lifecycle.*
execution.order.*
execution.trade.*
risk.decision.*
model.lifecycle.*
training.job.*
intelligence.analysis.*
notification.*
security.*
e2e.*
```

Every event must include:

```text
event_id
schema_version
occurred_at
correlation_id
causation_id
tenant_id where applicable
actor_type
actor_id
resource_type
resource_id
```

Runtime/execution events additionally bind exact `RuntimeGeneration` where applicable. No secret values are permitted in event payloads.

## 11. Deployment evolution

### Stage A — local/development

```text
Docker Compose / host-local processes
  portal-web
  portal-api
  portal-worker
  runtime-supervisor
  per-generation gateways/test runtimes where exercised
  postgres
  redis
  nats
  object-storage
  simulator
```

The Runtime Supervisor is a security process boundary, not a public service. Same-host transport uses UDS + ACL/peer identity according to ADR-020.

### Stage B — production-like staging

- Cloudflare edge and Tunnel;
- isolated staging identity/tenant space;
- Vault/KMS-backed secrets where the relevant boundary requires them;
- deterministic exchange simulator by default;
- Portal dry-run Freqtrade uses `PUBLIC_DATA` and no private exchange trading credentials;
- Runtime Supervisor remains private and is the sole Portal engine-authority process;
- generation isolation/effective-enforcement acceptance is required on the real host;
- optional exchange sandbox/testnet only where separately safe and authorized;
- centralized observability;
- Playwright E2E through the external protected route.

Production-like staging acceptance requires real protected external ingress validation. Repository-side policy/workflow evidence and simulation-first evidence do not satisfy real target acceptance by themselves.

### Stage C — production execution

Requires a separate explicit work package and lifecycle approval. Deployment may remain container-based or move to Kubernetes. Architecture contracts must not require public container ports or direct browser-to-runtime access. No live-capital authority follows from the dry-run architecture.

## 12. Multi-tenancy

Design all portal-owned business entities with a tenant boundary from the beginning.

Requirements:

- `tenant_id` on tenant-owned records;
- authorization enforced server-side on every access path;
- PostgreSQL row-level security considered as defense in depth for sensitive tables;
- tenant-scoped encryption context for high-value secrets where supported;
- object-storage keys/namespaces include non-guessable tenant scope;
- events include tenant scope but never secrets;
- logs avoid cross-tenant payload leakage;
- E2E includes User A -> User B denial tests;
- background workers carry explicit tenant context;
- RuntimeGeneration/Supervisor operations are exact tenant+bot+generation bound;
- unrelated runtime networks cannot communicate.

A single-user initial deployment is treated as one tenant, not as an excuse to omit tenancy boundaries.

## 13. Failure handling

The architecture prefers explicit states over hidden retries.

Examples:

- host lacks a required hard isolation control -> `HOST_INCOMPATIBLE` or a narrower reason; generation does not start;
- runtime provisioning/attestation failure -> `ERROR` with machine-readable reason;
- isolation plan/spec mismatch -> conflict/fail closed;
- exchange public data unavailable -> risk/execution gate closes new entries;
- stale model/data -> inference rejected or deterministic fallback according to policy;
- event consumer retry -> idempotent processing;
- model artifact unavailable -> runtime does not silently switch versions;
- stale/retired generation message -> cannot resurrect the generation;
- portal unavailable -> engine restart policy does not independently resurrect historical runtimes; recovery follows explicit desired-state reconciliation.

## 14. Architectural invariants

1. No public path reaches Freqtrade directly.
2. No public/browser path reaches Runtime Supervisor.
3. Runtime Supervisor is the only Portal component with raw container-engine lifecycle authority.
4. No AI model has unrestricted execution authority.
5. No execution intent bypasses deterministic risk approval before reaching a private submitter boundary.
6. No research job can directly mutate production configuration, control Portal-managed runtimes or access production exchange credentials.
7. No model is identified only by a mutable filename and no Portal runtime image is identified only by a mutable tag.
8. No trade is unattributable to strategy/model/config/risk/runtime-generation identities.
9. No executable RuntimeGeneration lacks immutable isolation profile and plan identity.
10. Requested container-engine controls are not considered effective until attested at the actual host/kernel boundary.
11. No autonomous repair bypasses branch/CI/PR controls or patches production directly.
12. No live-capital state is entered implicitly.
13. No completed research contract or protected holdout boundary is retroactively rewritten by portal implementation.
14. No simulated, repository-only or target-architecture evidence is represented as real production-like staging/host enforcement acceptance.
