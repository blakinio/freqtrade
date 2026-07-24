# AI Trading Portal — Data / Observability Foundation

## Scope

P4 implements the first executable event-publication, consumer-deduplication and telemetry foundations on top of the frozen P1 `EventEnvelope` and P2 transactional outbox.

Canonical implementation paths:

```text
ai_platform/portal/events/
ai_platform/portal/observability/
```

P4 does not own bot business transitions, does not deploy NATS/Redis/PostgreSQL/Prometheus/Grafana/trace backends and does not redefine P1 event schemas.

## Canonical event contract

P4 uses `ai_platform.portal.contracts.events.EventEnvelope` unchanged.

The canonical version field remains:

```text
event_version
```

P4 does not introduce a parallel `schema_version` field. Event subjects are derived deterministically as:

```text
portal.v<event_version>.<event_type>
```

Example:

```text
portal.v1.bot.created
```

Request, correlation and causation IDs remain inside the canonical envelope and are passed to transports/consumers unchanged.

## Transactional outbox publication

P2 already writes `EventEnvelope.canonical_json()` to `portal_outbox_events` in the same transaction as Control Plane state changes. P4 consumes those rows without changing bot business logic.

Publication flow:

```text
portal_outbox_events (published_at IS NULL)
        |
        v
lock next unpublished row
        |
        v
EventTransport.publish(subject, EventEnvelope)
        |
        v
set published_at
        |
        v
commit database transaction
```

`OutboxPublisher` uses `FOR UPDATE SKIP LOCKED` semantics where supported by the database so multiple publishers can avoid intentionally processing the same locked row.

The transport is an injected protocol. P4 does not select or deploy the final event bus.

## At-least-once guarantee

P4 explicitly treats publication as **at-least-once**.

A transport failure rolls back the database transaction and leaves `published_at` unset, so the row remains eligible for retry.

A process can also fail after the transport has accepted an event but before the database commit records `published_at`. The same event can therefore be delivered again. P4 does not claim exactly-once delivery.

Consumers must use `event_id` idempotency for side effects that cannot tolerate duplicates.

## Durable idempotent consumer reference

P4 adds the durable table:

```text
portal_event_inbox
```

Identity:

```text
PRIMARY KEY (consumer_name, event_id)
```

The marker also records:

- tenant ID;
- event type;
- correlation ID;
- processed timestamp.

Reference consumption flow:

```text
begin DB transaction
  -> insert inbox marker
  -> flush unique marker
  -> run handler side effects using the same SQLAlchemy Session
commit
```

Consequences:

- the same `event_id` is processed once per named consumer;
- a duplicate marker conflict is detected before the handler runs;
- handler side effects and inbox marker commit together;
- a handler failure rolls back both marker and side effects;
- an unrelated handler `IntegrityError` is propagated and is not misclassified as a duplicate event.

Redis is not used as authoritative deduplication state.

## Telemetry context

`TelemetryContext` carries stable operational identity:

```text
service
component
environment
request_id
correlation_id
causation_id
tenant_id (only when caller considers it safe)
actor_type
resource_type
resource_id
```

Domain correlation IDs complement trace/span IDs; they do not replace distributed tracing identity.

`TelemetryRecorder.operation()` emits a basic OpenTelemetry-compatible abstraction:

- start/success/failure structured log evidence;
- operation started/succeeded/failed counters;
- duration observation;
- trace span creation/end;
- exception type on failures.

The implementation intentionally does not log exception messages by default, because exception text can contain credentials or request content.

Final log/metric/trace backends remain injected protocols.

## Secret redaction

Operational telemetry recursively redacts sensitive fields before they reach log, metric or trace sinks.

Covered names include normalized variants of:

```text
api_key
api_secret
client_secret
access_token
refresh_token
session_token
websocket_token
password
passphrase
private_key
authorization
cookie
set-cookie
```

Compact/camel-style aliases such as `apiKey` and `clientSecret` are also redacted.

P1 `EventEnvelope` independently rejects sensitive event payload keys at contract construction time. P4 telemetry redaction is defense in depth for operational evidence and does not weaken that contract boundary.

Do not use P4 structured logs as the sole authoritative audit record. Audit events and operational telemetry have different retention and accountability purposes.

## Correlation invariant

A cross-plane operation can preserve the same domain correlation identity through:

```text
Control Plane outbox EventEnvelope
  -> EventTransport
  -> IdempotentEventConsumer
  -> correlated structured log / metric / trace attributes
```

The durable inbox retains `correlation_id` for consumer-side evidence lookup.

## Deployment boundaries

P4 does not deploy external infrastructure. Later deployment work can provide adapters for:

- NATS JetStream or another durable event transport;
- Prometheus-compatible metrics;
- OpenTelemetry trace export;
- centralized structured logs;
- Grafana-compatible dashboards/alerts.

Those adapters must preserve the stable event/correlation/redaction semantics defined here.

## PI-04 private runtime observability extension

PI-04 selects an OpenTelemetry Collector as the private OTLP ingress and fan-out boundary while preserving the P4 sink abstractions. The repository target routes:

```text
logs -> private Loki-compatible source
traces -> private Tempo-compatible source
metrics -> private Prometheus-compatible source
```

The runtime-log query boundary is separate from event transport and append-only audit storage. It requires `audit.read`, uses trusted tenant context and accepts only bounded filters for correlation, runtime, bot, service, component, level and time.

Repository contracts enforce:

- maximum query range of 24 hours;
- maximum response size of 200 records;
- explicit source `AVAILABLE` or `UNAVAILABLE` state;
- effective retention metadata;
- recursive redaction before source export and browser serialization;
- rejection of cross-tenant source records;
- no private backend endpoint or credential in browser contracts.

Initial retention targets are 14 days for logs, 7 days for traces and 30 days for metrics. Target-environment configuration may be stricter but must remain explicit. The default portal source fails closed as unavailable until private backend configuration is supplied.

`ai_platform/portal/deploy/observability/otel-collector.example.yaml` contains environment placeholders only. It does not provision infrastructure and cannot be represented as real P11 staging acceptance.

## Security and research invariants preserved

- no upstream `freqtrade/` core modification;
- no public Freqtrade or observability-backend route;
- no exchange/Freqtrade/observability credential values in events, telemetry or browser responses;
- no production-secret access;
- runtime logs do not replace append-only audit evidence;
- no live-capital activation;
- no protected final holdout use;
- no Phase 6 reopening;
- frozen thresholds `0.006/-0.009` unchanged;
- authoritative `selected_model = null` unchanged.
