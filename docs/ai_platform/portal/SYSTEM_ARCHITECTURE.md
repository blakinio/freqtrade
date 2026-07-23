# AI Trading Portal — System Architecture

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
                           | events               | commands
                           v                      v
                 +------------------+    +-----------------------------+
                 | Event Bus        |    | Execution Adapter Boundary  |
                 | NATS JetStream   |    | Freqtrade API/WS private    |
                 +---------+--------+    +--------------+--------------+
                           |                            |
                           v                            v
+----------------------------------------------------------------------------------+
|                               EXECUTION PLANE                                    |
|                                                                                  |
|      Freqtrade Runtime A       Freqtrade Runtime B       Freqtrade Runtime N      |
|      strategy/model pin        strategy/model pin        strategy/model pin       |
|      private network           private network           private network          |
|             |                         |                         |                 |
|             +-------------------------+-------------------------+                 |
|                                       |                                           |
|                                    Exchanges                                      |
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

A module becomes a separate service only when scaling, security or independent release requirements justify it.

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

Technology selection must not weaken the domain boundaries in this document.

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

A running bot is always attributable to one exact revision.

### 5.3 Execution adapter

The canonical private internal interface is versioned by the portal contracts and currently exposes:

```text
ExecutionAdapter
  provision_bot(bot, context)
  start_bot(bot, context)
  pause_bot(tenant_id, bot_id, context)
  stop_bot(tenant_id, bot_id, context)
  get_health(tenant_id, bot_id, context)
  get_runtime_status(tenant_id, bot_id, context)
  submit_approved_intent(ApprovedExecutionIntent, context)
  get_open_positions(tenant_id, bot_id, context)
  get_orders(tenant_id, bot_id, context)
  get_trades(tenant_id, bot_id, context)
```

The first implementation is `FreqtradeExecutionAdapter`. It implements private dry-run runtime lifecycle and health, but current order submission and portfolio/order/trade queries deliberately fail closed. `submit_approved_intent` raises `ORDER_SUBMISSION_NOT_IMPLEMENTED`; the P10 deterministic simulator is the only implemented `ApprovedExecutionIntent` submitter used for simulated trade acceptance.

This prevents portal API contracts from becoming coupled to Freqtrade endpoint details and leaves room for future bounded private Freqtrade submission integration or alternative execution engines without creating a browser-to-runtime path.

## 6. Execution Plane

### 6.1 Isolation unit

The default initial isolation unit is:

```text
one BotInstance -> one isolated Freqtrade runtime
```

Reasons:

- independent restart and rollout;
- per-bot strategy/model pinning;
- clear resource and log attribution;
- fault containment;
- safer secret injection;
- easier rollback and incident isolation.

Later optimization may group compatible workloads only after proving that isolation and attribution remain intact.

### 6.2 Runtime rules

Each runtime must:

- be reachable only on private networking;
- default to dry-run unless a separately approved lifecycle state authorizes otherwise;
- receive exchange credentials at runtime from the secret boundary;
- use an immutable strategy/model/config revision;
- expose health/telemetry only to trusted internal collectors;
- emit correlation-aware events;
- be replaceable rather than manually mutated in place.

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

## 8. AI / Research Plane

The AI plane remains separate from execution authority.

```text
Data -> Features -> Training -> Candidate -> Validation -> Registry -> Promotion
                                                        |
                                                        v
                                                production-eligible
```

The portal may request training, display experiments and manage approved promotions, but the production runtime only consumes immutable promoted artifacts allowed by lifecycle policy.

Research compute must use credentials and networking separate from production exchange connectivity.

## 9. Data Plane

Authoritative ownership:

- **Portal PostgreSQL:** users, tenants, bots, revisions, policies, model metadata, audit indexes.
- **Freqtrade runtime DB:** runtime-local trade lifecycle evidence for that execution instance.
- **Portal trade mirror:** normalized cross-runtime query model; not a hidden rewrite of runtime truth.
- **Object storage:** model artifacts, datasets, manifests, backtests, E2E artifacts and large reports.
- **Event bus:** real-time domain/event distribution, not the only durable system of record.
- **Telemetry backend:** operational metrics/logs/traces.

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

No secret values are permitted in event payloads.

## 11. Deployment evolution

### Stage A — local/development

```text
Docker Compose
  portal-web
  portal-api
  portal-worker
  postgres
  redis
  nats
  object-storage
  simulator
  freqtrade-test-runtimes
```

### Stage B — production-like staging

- Cloudflare edge and Tunnel;
- isolated staging identity/tenant space;
- Vault/KMS-backed secrets;
- deterministic exchange simulator by default;
- optional exchange sandbox/testnet where safe;
- centralized observability;
- Playwright E2E through the external protected route.

Production-like staging acceptance requires real protected external ingress validation. Repository-side P11 policy/verifier/workflow evidence and simulation-first P12 evidence do not satisfy this requirement by themselves.

### Stage C — production execution

Requires a separate explicit work package and lifecycle approval. Deployment may remain container-based or move to Kubernetes. Architecture contracts must not require public container ports or direct browser-to-runtime access.

## 12. Multi-tenancy

Design all portal-owned business entities with a tenant boundary from the beginning.

Requirements:

- `tenant_id` on tenant-owned records;
- authorization enforced server-side on every access path;
- PostgreSQL row-level security considered as defense in depth for sensitive tables;
- tenant-scoped encryption context for high-value secrets where supported;
- cross-tenant access included in security E2E tests;
- background workers carry explicit tenant context.

A single-user initial deployment is treated as one tenant, not as an excuse to omit tenancy boundaries.

## 13. Failure handling

The architecture prefers explicit states over hidden retries.

Examples:

- runtime provisioning failure -> `ERROR` with machine-readable reason;
- exchange unavailable -> risk/execution gate closes new entries;
- stale model/data -> inference rejected or deterministic fallback according to policy;
- event consumer retry -> idempotent processing;
- model artifact unavailable -> runtime does not silently switch versions;
- portal unavailable -> existing execution runtime follows predeclared safe behavior, not arbitrary remote commands.

## 14. Architectural invariants

1. No public path reaches Freqtrade directly.
2. No AI model has unrestricted execution authority.
3. No execution intent bypasses deterministic risk approval before reaching a private submitter boundary.
4. No research job can directly mutate production configuration or access production exchange credentials.
5. No model is identified only by a mutable filename.
6. No trade is unattributable to strategy/model/config/risk versions.
7. No autonomous repair bypasses branch/CI/PR controls or patches production directly.
8. No live-capital state is entered implicitly.
9. No completed research contract or protected holdout boundary is retroactively rewritten by portal implementation.
10. No simulated or repository-only evidence is represented as real production-like staging acceptance.
