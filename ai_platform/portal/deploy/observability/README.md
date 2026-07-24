# Portal runtime observability deployment boundary

This directory contains the repository-side PI-04 deployment contract for private runtime logs, traces and metrics.

## Selected topology

```text
portal/control/runtime workloads
        |
        | OTLP over private networking
        v
OpenTelemetry Collector Contrib
        |-- logs --> private Loki-compatible OTLP endpoint
        |-- traces --> private Tempo-compatible OTLP endpoint
        `-- metrics --> private Prometheus-compatible remote-write endpoint
```

The collector is a private infrastructure component. It is not a public portal API and is not exposed to browser clients. The example requires a Collector distribution containing the `redaction` processor, such as OpenTelemetry Collector Contrib.

## Required workload identity

Runtime telemetry producers must emit these resource or record attributes where applicable:

- `service.name`;
- `service.namespace=ai-trading-portal`;
- `deployment.environment`;
- `tenant_id`;
- `runtime_id`;
- `bot_id`;
- `correlation_id`;
- trace and span identifiers for traced operations.

Missing tenant, runtime or bot attribution must not be mapped to another scope. Records that cannot be safely attributed are rejected or isolated from portal queries.

## Environment-provided configuration

`otel-collector.example.yaml` contains no destination or credential value. The deployment environment must provide:

- `PORTAL_ENVIRONMENT`;
- `PORTAL_OTEL_LOGS_ENDPOINT`;
- `PORTAL_OTEL_LOGS_AUTHORIZATION`;
- `PORTAL_OTEL_TRACES_ENDPOINT`;
- `PORTAL_OTEL_TRACES_AUTHORIZATION`;
- `PORTAL_OTEL_METRICS_ENDPOINT`;
- `PORTAL_OTEL_METRICS_AUTHORIZATION`.

Values are injected through the deployment secret/configuration boundary. They must not be committed, logged, included in audit payloads or returned by portal APIs.

## Retention target

The initial declared target is:

- structured runtime logs: 14 days;
- distributed traces: 7 days;
- runtime metrics: 30 days.

An environment may use stricter retention, but the effective values must be exposed through the server-side source-status contract. Portal log search remains bounded to 24 hours and 200 records per request regardless of backend retention.

## Security boundary

- Runtime-log queries require `audit.read` and tenant scope from trusted identity context.
- Loki/Tempo/Prometheus endpoints and credentials remain server-side.
- P4 producers recursively redact secret-like fields before they reach telemetry sinks.
- The collector `redaction/sensitive` processor masks sensitive top-level attributes in every logs, traces and metrics pipeline before batch/export as defense in depth.
- The portal query service recursively redacts structured fields again before browser serialization.
- Runtime telemetry is operational evidence and does not replace append-only audit events.
- This repository configuration does not provision external infrastructure and does not satisfy P11 production-like staging acceptance.
