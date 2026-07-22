# AI Trading Portal — Data and Observability Architecture

## 1. Objective

Provide durable, attributable evidence for every important user, model, risk, execution and autonomous-agent action without turning one database into an unbounded dumping ground.

The platform must answer questions such as:

- Which exact model/config/risk policy caused a trade intent?
- What did the model see at decision time?
- Why was an intent rejected or resized?
- Which Freqtrade runtime executed the order?
- What happened between portal click and exchange outcome?
- Which evidence produced an AI insight?
- Which agent changed which files after an E2E failure?

## 2. Data ownership

### PostgreSQL

Authoritative portal metadata:

- tenants/users/roles;
- exchange connection metadata and opaque secret references;
- bot instances and immutable config revisions;
- strategy/model/dataset/feature metadata;
- risk policy versions;
- training/validation job metadata;
- normalized trade/query mirrors;
- insight/analysis indexes;
- notification configuration;
- audit indexes.

### Freqtrade runtime storage

Authoritative runtime-local execution/trade lifecycle evidence for a specific runtime.

The portal may mirror/normalize this data for cross-bot queries but must preserve source runtime identity and reconciliation status.

### Object storage

Large immutable artifacts:

```text
datasets/
models/
feature-manifests/
experiments/
backtests/
validation-reports/
decision-snapshots/
trade-replays/
e2e-artifacts/
agent-diagnostics/
```

Objects are addressed by version and integrity hash where practical.

### Event bus

Real-time distribution and workflow decoupling. The event bus is not the only system of record for state that must survive arbitrary retention changes.

### Redis

Ephemeral cache, locks/coordination and short-lived rate/state helpers only. Redis is not the authoritative model registry, audit log or bot configuration store.

## 3. Core identifiers

Every cross-plane workflow uses stable identifiers:

```text
tenant_id
actor_id
bot_id
runtime_id
bot_config_revision_id
strategy_version_id
model_version_id
risk_policy_version_id
decision_id
trade_id
analysis_id
experiment_id
training_job_id
correlation_id
causation_id
```

Do not infer identity from display names.

## 4. Correlation model

Example user action:

```text
User clicks Start Bot
  correlation_id = C1
       |
       v
Portal command C1
       |
       v
Orchestrator reconciliation C1
       |
       v
Runtime provision/start C1
       |
       v
Freqtrade health observation C1
       |
       v
Bot healthy event C1
```

Example trade:

```text
Market decision D1
  correlation_id = C2
       |
       v
Prediction -> Strategy -> Risk -> Execution -> Order -> Trade
       |
       v
Post-trade analysis A1
  causation_id = D1 / trade event
```

Trace/span IDs complement domain correlation IDs; they do not replace them.

## 5. Event envelope

All domain events use a versioned envelope:

```json
{
  "event_id": "...",
  "event_type": "execution.trade.closed",
  "schema_version": 1,
  "occurred_at": "...",
  "correlation_id": "...",
  "causation_id": "...",
  "tenant_id": "...",
  "actor": {
    "type": "user|service|agent|system",
    "id": "..."
  },
  "resource": {
    "type": "trade",
    "id": "..."
  },
  "payload": {}
}
```

Forbidden payload content:

- exchange secret values;
- Freqtrade control credentials;
- session tokens;
- passwords;
- private keys.

## 6. Event publication reliability

State-changing portal transactions use an outbox pattern:

```text
DB transaction
  - update state
  - write outbox event
       |
       v
publisher
       |
       v
NATS JetStream
```

Consumers are idempotent and maintain inbox/deduplication state where duplicates would be harmful.

Delivery is treated as at-least-once unless a stronger property is explicitly proven.

## 7. Trade Decision Black Box

Decision evidence is recorded before execution outcome is known.

Storage split:

- searchable metadata in PostgreSQL;
- large feature/market snapshots in object storage;
- integrity hash and object reference in the metadata record.

A decision snapshot must preserve only information available at decision time. Post-outcome fields are stored separately.

## 8. Trade replay package

A replay package can contain:

```text
manifest.json
market-window.parquet
features.parquet
predictions.json
risk-decisions.json
execution-events.json
outcome.json
analysis.json
```

The manifest pins:

- bot/config revision;
- strategy/model/risk versions;
- timestamps/timezones;
- source runtime;
- data hashes;
- replay tool version.

Replays are analytical artifacts, not a mechanism for changing historical records.

## 9. Normalized trade mirror

Portal analytics require a cross-runtime read model.

`TradeMirror` includes:

```text
trade_id
source_runtime_id
source_trade_id
tenant_id
bot_id
opened_at
closed_at
pair
side
status
stake/exposure
entry_price
exit_price
fees
realized_pnl
exit_reason
last_reconciled_at
reconciliation_status
```

Reconciliation status makes gaps explicit:

```text
SYNCED
PENDING
SOURCE_UNAVAILABLE
MISMATCH
```

The portal never silently presents stale mirrored state as strongly current when reconciliation is degraded.

## 10. Observability stack

Instrument all portal-owned services with OpenTelemetry-compatible traces, metrics and structured logs.

Target outputs:

- metrics -> Prometheus-compatible backend;
- logs -> centralized searchable log backend;
- traces -> distributed trace backend;
- dashboards/alerts -> Grafana-compatible presentation or equivalent.

Technology may evolve; telemetry field contracts remain stable.

## 11. Structured logging

Minimum structured fields:

```text
timestamp
level
service
component
environment
correlation_id
trace_id
span_id
tenant_id where safe
actor_type
resource_type
resource_id
event/action
result
reason_code
```

Sensitive values are redacted before emission.

Do not log full request bodies by default on credential, authentication, webhook-secret or model-artifact endpoints.

## 12. Metrics

### Portal/control

- request rate/error/latency;
- auth failures;
- rate-limit/WAF-adjacent application rejections where visible;
- bot lifecycle transition duration/failure;
- job queue depth/age;
- event publish/consume lag.

### Execution

- runtime health;
- exchange/API error rate;
- order latency;
- fill/partial-fill counts;
- reconciliation mismatches;
- new-entry kill-switch status.

### AI

- inference latency/success/rejection;
- `do_predict` accepted/rejected;
- model age;
- feature/data drift;
- prediction distribution drift;
- training job duration/failure;
- validation gate results.

### Trade intelligence

- analyses queued/completed/failed;
- diagnosis distribution;
- unresolved severe insights;
- evidence age;
- counterfactual job failures.

### E2E

- scenario pass/fail;
- flake rate;
- browser/platform matrix health;
- mean diagnosis time;
- agent patch success rate;
- rejected unsafe repair attempts.

## 13. Alerts

Alert classes:

```text
P0 capital/security risk
P1 execution unavailable or materially degraded
P2 AI/data/model degradation
P3 product/workflow degradation
```

Examples:

- unauthorized access anomaly;
- exchange secret access anomaly;
- kill switch triggered;
- daily loss/drawdown threshold crossed;
- exchange connectivity failure;
- widespread Freqtrade runtime failure;
- stale data/model;
- event backlog exceeding SLO;
- model artifact integrity mismatch;
- E2E critical journey failure on staging.

Alerts include runbook links and correlation IDs where possible.

## 14. Audit vs operational logs

Audit records and operational logs have different purposes.

- Operational logs may be sampled/rotated and are optimized for diagnosis.
- Audit records preserve security/business accountability and have stricter retention/immutability requirements.

Do not rely on ordinary debug logs as the sole proof of a model promotion or exchange credential rotation.

## 15. Retention classes

Define retention by data class rather than one global value:

- security/audit evidence;
- trading/execution evidence;
- model/experiment evidence;
- market/raw feature data;
- E2E videos/traces/screenshots;
- ordinary operational logs.

Exact durations are deployment/legal/product decisions and are intentionally deferred. Deletion/retention policies must preserve reproducibility obligations and user privacy requirements.

## 16. Privacy

Private user/profile information is minimized in diagnostics.

Rules:

- use internal IDs instead of email where possible;
- redact uploaded screenshots before publication;
- keep raw authenticated third-party UI captures outside public repository history;
- restrict access to evidence containing account/profile data;
- separate observability identifiers from unnecessary PII.

## 17. Observability invariants

1. A cross-plane incident can be followed by correlation ID.
2. A trade can be attributed to exact strategy/model/config/risk versions.
3. Decision-time and outcome-time data are not mixed silently.
4. Mirrored execution data exposes staleness/reconciliation state.
5. Secrets are absent from logs/events/traces.
6. Negative model/trade evidence remains durable.
7. Autonomous-agent repairs leave auditable evidence and PR history.
