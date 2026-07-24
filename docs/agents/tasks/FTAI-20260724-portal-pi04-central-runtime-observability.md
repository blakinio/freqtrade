---
task_id: FTAI-20260724-portal-pi04-central-runtime-observability
status: active
branch: feat/portal-pi04-central-runtime-observability-20260724
base_branch: develop
created: 2026-07-24
updated: 2026-07-24
related_pr: null
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
updated_at: 2026-07-24T16:31:52+02:00
head: ee6c8c36272e5b565515692ddb1c834c4ff6a88c
branch: feat/portal-pi04-central-runtime-observability-20260724
pr: null
status: active
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
  - PI-03 was durably completed and its closure PR 260 was squash-merged to develop as ee6c8c36272e5b565515692ddb1c834c4ff6a88c.
  - P4 already provides correlation-aware TelemetryContext, structured operation logs, counters, duration observations, trace-sink abstraction and recursive redaction.
  - The current Execution Activity UI exposes durable audit evidence and truthfully reports centralized runtime stdout/stderr as unavailable.
  - Open PR 248 owns RL-v2 paired-attribution paths and open draft PR 109 owns a sanitized design reference; neither owns the declared PI-04 implementation paths.
derived:
  - PI-04 can extend the existing observability abstraction without changing P4 event contracts or creating a parallel audit system.
  - Real target-environment provisioning remains separate from repository-side contracts and does not satisfy P11.
unknown:
  - Final required CI result for the PI-04 implementation branch.
conflicts: []
first_failure:
  marker: NOT_RUN
  evidence: PI-04 implementation and validation have not run yet.
rejected_hypotheses:
  - Store centralized runtime logs in append-only AuditEvent records.
  - Expose private observability backend URLs directly to browser clients.
  - Treat backend unavailability as an empty successful log result.
changed_paths:
  - docs/agents/tasks/FTAI-20260724-portal-pi04-central-runtime-observability.md
validation: []
blockers: []
next_action: Implement the bounded private runtime-log source, search/availability API, collector configuration, UI integration and focused tests, then run required CI.
```
