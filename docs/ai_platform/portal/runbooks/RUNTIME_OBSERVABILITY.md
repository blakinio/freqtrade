# Runtime Observability Runbook

## Purpose

Operate and diagnose the private PI-04 runtime observability path without confusing logs, traces or metrics with immutable portal audit evidence.

## Expected topology

```text
private portal/control/runtime workloads
        -> OpenTelemetry Collector
        -> Loki-compatible structured logs
        -> Tempo-compatible traces
        -> Prometheus-compatible metrics
```

The browser talks only to the portal/BFF and control-plane query API. It never receives a backend endpoint or backend credential.

## Source states

`AVAILABLE` means the configured private source responded with current status and may be queried within the declared retention window.

`UNAVAILABLE` means the portal cannot prove source availability. The UI must show the reason code and return no raw-log records. It must not convert source failure into a successful empty result or remove durable audit events.

## First checks

1. Confirm the portal source-status response and `checked_at` timestamp.
2. Confirm the OpenTelemetry Collector health endpoint is reachable only from the intended private network.
3. Confirm OTLP pipelines are accepting logs, traces and metrics without exporter queue growth or repeated failures.
4. Confirm destination credentials and endpoints exist in the deployment secret/configuration boundary, not in Git or application responses.
5. Query by one exact `correlation_id`, then narrow by tenant, runtime and bot identity.
6. Compare operational telemetry with append-only audit evidence; never overwrite one source with the other.

## Missing records

Check, in order:

- the producer emitted `tenant_id`, `runtime_id`, `bot_id`, `service.name`, environment and correlation identity;
- the record timestamp is within backend retention and the portal's maximum 24-hour query range;
- the collector log pipeline is healthy;
- the Loki-compatible source accepted the tenant-scoped stream;
- the portal identity has `audit.read`;
- the selected tenant matches the trusted application identity context.

Do not broaden a query by removing tenant isolation.

## Redaction incident

If a secret-like value appears in telemetry:

1. disable or isolate the affected exporter/query source;
2. revoke or rotate the exposed credential through the owning secret system;
3. preserve a security audit event containing references only, never the secret value;
4. correct producer-side field names and redaction coverage;
5. remove affected operational records according to backend incident procedures;
6. add a regression test before restoring the source.

## Backend outage

- Return `UNAVAILABLE` with a stable reason code.
- Keep audit, risk and reconciliation evidence independently available.
- Do not infer runtime health from absence of logs.
- Do not retry unboundedly from browser requests.
- Restore the private source, then verify a known correlation ID across log and trace evidence.

## Retention

Initial target retention:

- logs: 14 days;
- traces: 7 days;
- metrics: 30 days.

The portal exposes effective retention metadata but enforces a maximum 24-hour log query and 200 records per request. Retention changes require documentation and an access/privacy review.

## Escalation boundaries

PI-04 does not authorize:

- public access to Loki, Tempo, Prometheus, Grafana, the collector or Freqtrade;
- production credential retrieval;
- execution submission or live capital;
- representing repository configuration as real P11 Cloudflare staging acceptance.
