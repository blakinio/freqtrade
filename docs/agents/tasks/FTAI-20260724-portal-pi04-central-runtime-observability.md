---
task_id: FTAI-20260724-portal-pi04-central-runtime-observability
status: ready
branch: feat/portal-pi04-central-runtime-observability-20260724
base_branch: develop
created: 2026-07-24
updated: 2026-07-24
related_pr: 261
owned_paths:
  - ai_platform/portal/observability/**
  - ai_platform/portal/deploy/observability/**
  - ai_platform/portal/control_plane/api.py
  - ai_platform/portal/web/app/operations/execution-logs/page.tsx
  - ai_platform/portal/web/lib/product-api.ts
  - ai_platform/portal/web/lib/product-contracts.ts
  - ai_platform/portal/web/e2e/shell.spec.ts
  - tests/ai_platform/portal/observability/**
  - tests/ai_platform/portal/control_plane/test_api.py
  - docs/ai_platform/portal/DATA_OBSERVABILITY_FOUNDATION.md
  - docs/ai_platform/portal/DATA_AND_OBSERVABILITY_ARCHITECTURE.md
  - docs/ai_platform/portal/POST_P12_INTEGRATION_BACKLOG.md
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
  - docs/ai_platform/portal/runbooks/RUNTIME_OBSERVABILITY.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/agents/tasks/FTAI-20260724-portal-pi04-central-runtime-observability.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/README.md
  - docs/ai_platform/portal/POST_P12_INTEGRATION_BACKLOG.md
  - docs/ai_platform/portal/SYSTEM_ARCHITECTURE.md
  - docs/ai_platform/portal/SECURITY_ARCHITECTURE.md
  - docs/ai_platform/portal/DATA_OBSERVABILITY_FOUNDATION.md
  - docs/ai_platform/portal/DATA_AND_OBSERVABILITY_ARCHITECTURE.md
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
---

# PI-04 — Centralized Runtime Observability

## Goal

Provide a private, tenant-scoped runtime observability boundary for searchable structured logs, correlation-aware trace linkage, Prometheus-compatible metrics routing and explicit backend availability without treating operational telemetry as immutable audit evidence.

## Selected repository target

- OpenTelemetry Collector is the canonical private OTLP ingress and fan-out boundary.
- Structured logs use a private Loki-compatible query source.
- Distributed traces use a private Tempo-compatible source and trace identifiers.
- Metrics use a Prometheus-compatible source.
- Grafana-compatible dashboards and runbook links are presentation targets.
- Private backend endpoints, authorization headers and credentials are server-side configuration only and are never committed or returned to the browser.
- Repository and CI acceptance use injected deterministic sources; the production default fails closed as unavailable until private backend configuration exists.

## Declared policy

- Runtime log reads require `audit.read` and are always tenant-scoped server-side.
- Log records must carry service, component, environment, tenant, runtime, bot, timestamp and correlation identity where applicable.
- Query windows are bounded to 24 hours, result count is bounded to 200 and backend retention is represented explicitly.
- Initial target retention is 14 days for logs, 7 days for traces and 30 days for metrics; target-environment overrides must remain explicit and server-side.
- Secret-like fields are recursively redacted before export and again before browser serialization.
- Audit events remain append-only business/security evidence; runtime logs, traces and metrics are operational evidence with independent retention and availability.

## Deliverables

- versioned runtime-log query, result and source-availability contracts;
- private Loki-compatible source adapter with bounded timeout, body size and fail-closed protocol validation;
- tenant/permission-enforced control-plane search and availability APIs;
- correlation/runtime/bot/service/component/level/time filters with deterministic limits;
- OpenTelemetry Collector repository configuration for log/trace/metric fan-out without embedded endpoints or secrets;
- execution-activity UI integration that shows raw logs only when the source is available and keeps audit evidence separate;
- retention, redaction, source-unavailability, tenant-isolation and correlation tests;
- architecture, backlog, status and operations runbook updates.

## Acceptance criteria

1. A portal-to-runtime incident can be searched by one correlation ID without returning another tenant's records.
2. Secret-like keys are redacted before export and before browser serialization, including nested structures.
3. Backend unavailability is explicit and does not remove or relabel audit evidence.
4. Raw log reads require `audit.read`, enforce a maximum 24-hour range and return at most 200 records.
5. Browser responses contain no private backend endpoint, authorization header or credential.
6. OpenTelemetry Collector configuration routes logs, traces and metrics through environment-provided private destinations.
7. Required targeted and repository CI pass before merge.

## Non-goals

- using runtime logs as the sole audit, trade or security proof;
- public browser access to Loki, Tempo, Prometheus, Grafana or Freqtrade;
- provisioning real external infrastructure or satisfying P11;
- service extraction, Kubernetes or P13 activation;
- execution submission, credential brokering, live capital or P14;
- modifying frozen thresholds, Phase 6 evidence or protected final-holdout policy.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-24T19:39:00+02:00
head: b5d7e53a95bb12a32edd5834a407850ee241dab2
branch: feat/portal-pi04-central-runtime-observability-20260724
pr: 261
status: ready
context_routes:
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/POST_P12_INTEGRATION_BACKLOG.md
  - docs/ai_platform/portal/DATA_OBSERVABILITY_FOUNDATION.md
  - docs/ai_platform/portal/DATA_AND_OBSERVABILITY_ARCHITECTURE.md
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
owned_paths:
  - ai_platform/portal/observability/**
  - ai_platform/portal/deploy/observability/**
  - ai_platform/portal/control_plane/api.py
  - ai_platform/portal/web/app/operations/execution-logs/page.tsx
  - ai_platform/portal/web/lib/product-api.ts
  - ai_platform/portal/web/lib/product-contracts.ts
  - ai_platform/portal/web/e2e/shell.spec.ts
  - tests/ai_platform/portal/observability/**
  - tests/ai_platform/portal/control_plane/test_api.py
  - docs/ai_platform/portal/DATA_OBSERVABILITY_FOUNDATION.md
  - docs/ai_platform/portal/DATA_AND_OBSERVABILITY_ARCHITECTURE.md
  - docs/ai_platform/portal/POST_P12_INTEGRATION_BACKLOG.md
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
  - docs/ai_platform/portal/runbooks/RUNTIME_OBSERVABILITY.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/agents/tasks/FTAI-20260724-portal-pi04-central-runtime-observability.md
proven:
  - PR 261 implements versioned tenant-scoped runtime-log query, record, result and source-status contracts without creating a parallel audit model.
  - Runtime log availability and search require trusted tenant context plus AUDIT_READ; cross-tenant source records fail closed.
  - Queries are bounded to a 24-hour window and 200 results and preserve service, component, environment, runtime, bot, correlation, trace/span, timestamp, source and retention identity.
  - The private Loki-compatible source includes a concrete server-side HTTP transport with HTTP(S) hostname validation, embedded-credential rejection, a five-second default timeout and a one-MiB default response limit.
  - Retryable backend failure and timeout are represented as UNAVAILABLE with stable reason evidence rather than a false empty success or unhandled browser-facing backend response.
  - P4 recursively redacts producer fields, the OpenTelemetry Collector Contrib example applies redaction before every log/trace/metric exporter, and the query service redacts again before browser serialization.
  - Collector destination endpoints and authorization values are environment-provided only; no private backend endpoint or credential is committed or returned through portal contracts.
  - Execution Activity displays bounded raw runtime evidence separately from append-only audit evidence and truthfully exposes source availability and retention.
  - Focused runtime observability, API, collector-configuration, redaction, tenant-isolation, transport-boundary and outage tests pass.
  - Temporary Ruff and formatter diagnostic workflows were removed from the final merge candidate.
  - AI Platform CI 1110, Portal Web CI 177, Portal Universal E2E 182, zizmor 1227 and Freqtrade CI 1297 passed on implementation head b5d7e53a95bb12a32edd5834a407850ee241dab2.
derived:
  - PI-04 satisfies its bounded repository-side acceptance without provisioning external observability infrastructure or satisfying P11.
  - Operational logs, traces and metrics remain independent from immutable audit evidence and cannot authorize execution or live capital.
unknown: []
conflicts: []
first_failure:
  marker: RESOLVED
  evidence: The initial exact OpenAPI-path assertion omitted the two PI-04 routes; later Ruff E501/S107 and formatter findings were isolated with temporary diagnostics, fixed without behavioral broadening and the diagnostics were removed before the final all-green matrix.
rejected_hypotheses:
  - Store centralized runtime logs in append-only AuditEvent records.
  - Expose private observability backend URLs directly to browser clients.
  - Treat backend unavailability as an empty successful log result.
  - Rely only on query-time redaction without producer and collector defense in depth.
  - Leave the Loki transport as an unbounded injected protocol without timeout or response-size enforcement.
changed_paths:
  - ai_platform/portal/control_plane/api.py
  - ai_platform/portal/deploy/observability/README.md
  - ai_platform/portal/deploy/observability/otel-collector.example.yaml
  - ai_platform/portal/observability/__init__.py
  - ai_platform/portal/observability/runtime.py
  - ai_platform/portal/web/app/operations/execution-logs/page.tsx
  - ai_platform/portal/web/e2e/shell.spec.ts
  - ai_platform/portal/web/lib/product-api.ts
  - ai_platform/portal/web/lib/product-contracts.ts
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/agents/tasks/FTAI-20260724-portal-pi04-central-runtime-observability.md
  - docs/ai_platform/portal/DATA_AND_OBSERVABILITY_ARCHITECTURE.md
  - docs/ai_platform/portal/DATA_OBSERVABILITY_FOUNDATION.md
  - docs/ai_platform/portal/POST_P12_INTEGRATION_BACKLOG.md
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
  - docs/ai_platform/portal/runbooks/RUNTIME_OBSERVABILITY.md
  - tests/ai_platform/portal/control_plane/test_api.py
  - tests/ai_platform/portal/observability/test_collector_config.py
  - tests/ai_platform/portal/observability/test_runtime.py
  - tests/ai_platform/portal/observability/test_runtime_api.py
  - tests/ai_platform/portal/observability/test_runtime_outage.py
validation:
  - command: AI Platform CI 30112758845 / run 1110
    result: PASS
    evidence: AI platform tests, compile, Ruff, Ruff format, codespell and contract validations passed on implementation head b5d7e53a95bb12a32edd5834a407850ee241dab2.
  - command: Portal Web CI 30112758870 / run 177
    result: PASS
    evidence: Typecheck, lint, production build and Chromium browser E2E passed on the implementation head.
  - command: Portal Universal E2E 30112758851 / run 182
    result: PASS
    evidence: Backend universal scenario and critical Chromium path passed on the implementation head.
  - command: GitHub Actions Security Analysis with zizmor 30112758838 / run 1227
    result: PASS
    evidence: Required workflow security analysis passed on the implementation head.
  - command: Freqtrade CI 30112758848 / run 1297
    result: PASS
    evidence: Pre-commit, documentation, full multi-platform core matrix, coverage, smoke checks, Ruff, formatter, mypy and CI gate passed on the implementation head.
blockers: []
next_action: Review and merge PR 261 after approval; select the next package only after durable merge evidence exists on develop.
```
