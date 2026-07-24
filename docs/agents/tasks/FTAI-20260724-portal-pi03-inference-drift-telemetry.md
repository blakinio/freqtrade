---
task_id: FTAI-20260724-portal-pi03-inference-drift-telemetry
status: done
branch: develop
base_branch: develop
created: 2026-07-24
updated: 2026-07-24
related_pr: 239
owned_paths:
  - ai_platform/portal/telemetry/**
  - ai_platform/portal/control_plane/api.py
  - ai_platform/portal/control_plane/database.py
  - ai_platform/portal/web/app/ai/model-health/page.tsx
  - ai_platform/portal/web/lib/product-api.ts
  - ai_platform/portal/web/lib/product-contracts.ts
  - ai_platform/portal/web/e2e/shell.spec.ts
  - tests/ai_platform/portal/telemetry/**
  - tests/ai_platform/portal/control_plane/test_api.py
  - docs/ai_platform/portal/POST_P12_INTEGRATION_BACKLOG.md
  - docs/ai_platform/portal/DATA_AND_OBSERVABILITY_ARCHITECTURE.md
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/agents/tasks/FTAI-20260724-portal-pi03-inference-drift-telemetry.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/README.md
  - docs/ai_platform/portal/POST_P12_INTEGRATION_BACKLOG.md
  - docs/ai_platform/portal/SYSTEM_ARCHITECTURE.md
  - docs/ai_platform/portal/SECURITY_ARCHITECTURE.md
  - docs/ai_platform/portal/DATA_AND_OBSERVABILITY_ARCHITECTURE.md
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
---

# PI-03 — Canonical Inference and Drift Telemetry

## Goal

Add a tenant-scoped, aggregate-only inference telemetry boundary and deterministic drift assessment so Model Health reports attributable measured evidence rather than inferring health from model age or returning only a generic unavailable state.

## Deliverables

- versioned inference telemetry window and source-status contracts;
- exact ModelVersion, feature-schema, bot, immutable bot-config revision and runtime attribution;
- accepted/rejected prediction counts with bounded reason aggregates;
- aggregate feature quality and comparable prediction/feature distributions without raw feature values or individual predictions;
- durable reference and observation windows plus reproducible PSI-v1 assessments;
- explicit `HEALTHY`, `ATTENTION`, `DEGRADED`, `INSUFFICIENT_EVIDENCE` and `UNAVAILABLE` states;
- model-health API/UI integration and focused tenant, attribution, idempotency, privacy and no-promotion tests;
- architecture/backlog/status documentation.

## Entry gates and declared policy

- telemetry source identity is a service/system identity with `model.train` permission;
- each envelope is attributable to one tenant/model/feature-schema/bot/config-revision/runtime scope;
- only aggregate counts and bucket distributions are retained; raw feature values and individual predictions are forbidden;
- reference windows are explicitly labelled and must match observation bucket identities;
- drift method is PSI-v1 with versioned minimum-sample, attention and degraded thresholds;
- telemetry and drift assessments are evidence only and cannot mutate model lifecycle, promotion slots, risk rules or execution authority;
- protected final holdout `20260801-20260930` is forbidden as iterative telemetry/reference evidence.

## Non-goals

- automatic retraining, model promotion, rollback or lifecycle mutation;
- changing Phase 5 thresholds or completed Phase 6 evidence;
- raw event/log storage, centralized observability backend selection or PI-04;
- order submission, credential brokering, live trading or P14;
- causal claims from drift alone.

## Acceptance criteria

1. Matching reference and observation windows reproduce the same PSI-v1 result from persisted contracts and policy parameters.
2. Missing source status, missing windows, incompatible buckets and insufficient samples never produce `HEALTHY`.
3. Cross-tenant ingestion/read and mismatched model/bot/config attribution fail closed; reference and observation windows from different runtime scopes are never combined.
4. Duplicate telemetry IDs are idempotent only for byte-equivalent canonical payloads; conflicting reuse is rejected.
5. Public responses contain no raw features, individual predictions, credentials, private endpoints or secret-bearing payloads.
6. Ingestion and health reads do not change ModelVersion lifecycle or promotion slots.
7. Required targeted and repository CI pass before merge.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-24T16:31:52+02:00
head: d85ed2c7700a10833aa32d84e7d10cc0a623179c
branch: develop
pr: 239
status: ready
context_routes:
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/POST_P12_INTEGRATION_BACKLOG.md
  - docs/ai_platform/portal/DATA_AND_OBSERVABILITY_ARCHITECTURE.md
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
owned_paths:
  - ai_platform/portal/telemetry/**
  - ai_platform/portal/control_plane/api.py
  - ai_platform/portal/control_plane/database.py
  - ai_platform/portal/web/app/ai/model-health/page.tsx
  - ai_platform/portal/web/lib/product-api.ts
  - ai_platform/portal/web/lib/product-contracts.ts
  - ai_platform/portal/web/e2e/shell.spec.ts
  - tests/ai_platform/portal/telemetry/**
  - tests/ai_platform/portal/control_plane/test_api.py
  - docs/ai_platform/portal/POST_P12_INTEGRATION_BACKLOG.md
  - docs/ai_platform/portal/DATA_AND_OBSERVABILITY_ARCHITECTURE.md
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/agents/tasks/FTAI-20260724-portal-pi03-inference-drift-telemetry.md
proven:
  - PR 239 implements aggregate-only inference windows, source status and deterministic PSI-v1 assessments with exact tenant, model, feature-schema, bot-config, runtime and source attribution.
  - Raw feature values, individual predictions, credentials and private endpoints are excluded from the PI-03 persistence and browser contracts.
  - Missing, unavailable, stale, insufficient or bucket-incompatible evidence never produces HEALTHY.
  - Telemetry ingestion requires service or system identity with MODEL_TRAIN and rejects cross-tenant or mismatched attribution.
  - Duplicate telemetry identities are idempotent only for the same canonical payload; conflicting reuse is rejected.
  - Model Health API and UI expose window identities, sample counts, source availability and PSI or feature-quality evidence without lifecycle mutation.
  - Focused telemetry and control-plane API tests passed with 18 tests.
  - Exact Ruff 0.15.21 findings were I001 in telemetry package imports, C901 in InferenceTelemetryEnvelope.validate_envelope and E501 in the telemetry test helper; Ruff format identified five Python files.
  - Ruff auto-fix and format resolved the import, line-length and formatting findings; the remaining C901 was removed by splitting the validator into bounded helpers without changing validation order or error semantics.
  - Every intended PI-03 backlog, architecture, UI-status and program documentation replacement is present, so cleanup is idempotent and no temporary patch runner is required.
  - The temporary documentation workflow, patch script, trigger and diagnostic files are absent from the merge candidate.
  - The external liquidation tmp-path regression was resolved on develop without leaving that test in PI-03 ownership.
  - Required AI Platform CI 1052, Portal Web CI 139, Portal Universal E2E 144, zizmor 1158 and Freqtrade CI 1228 passed on owner head a9fe77a0d030ed0db1d988d848bd8577697bf9da.
  - PR 239 was squash-merged to develop as d85ed2c7700a10833aa32d84e7d10cc0a623179c.
derived:
  - PI-03 satisfies its declared acceptance gates and is durably complete.
  - The next portal integration package must be declared as a separate bounded task and must not reopen PI-03.
unknown: []
conflicts: []
first_failure:
  marker: NONE
  evidence: The prior Ruff findings and external liquidation tmp-path regression are resolved; all required workflows passed before merge.
rejected_hypotheses:
  - Infer drift from model metadata age or training-window age.
  - Persist raw feature vectors or individual prediction values in the portal database.
  - Let drift status automatically promote, rollback or retrain a model.
  - Reuse protected final-holdout observations as iterative reference telemetry.
  - Combine reference and observation windows across runtime, config or source identities.
  - Treat the liquidation tmp-path regression as an intermittent runner-only failure.
changed_paths:
  - ai_platform/portal/control_plane/api.py
  - ai_platform/portal/control_plane/database.py
  - ai_platform/portal/telemetry/__init__.py
  - ai_platform/portal/telemetry/drift.py
  - ai_platform/portal/telemetry/migrations/0001_inference_drift_telemetry.sql
  - ai_platform/portal/telemetry/models.py
  - ai_platform/portal/telemetry/repository.py
  - ai_platform/portal/telemetry/schema.py
  - ai_platform/portal/telemetry/service.py
  - ai_platform/portal/web/app/ai/model-health/page.tsx
  - ai_platform/portal/web/e2e/shell.spec.ts
  - ai_platform/portal/web/lib/product-api.ts
  - ai_platform/portal/web/lib/product-contracts.ts
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/agents/tasks/FTAI-20260724-portal-pi03-inference-drift-telemetry.md
  - docs/ai_platform/portal/DATA_AND_OBSERVABILITY_ARCHITECTURE.md
  - docs/ai_platform/portal/POST_P12_INTEGRATION_BACKLOG.md
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
  - tests/ai_platform/portal/control_plane/test_api.py
  - tests/ai_platform/portal/telemetry/test_inference_telemetry.py
validation:
  - command: focused PI-03 telemetry and control-plane API pytest
    result: PASS
    evidence: 18 tests passed after timezone and compatibility fixes.
  - command: Ruff 0.15.21 diagnostic and cleanup
    result: PASS
    evidence: I001, E501 and formatting were auto-fixed; C901 was removed by bounded validator helpers and exact Ruff plus format checks passed.
  - command: required repository CI on owner head a9fe77a0d030ed0db1d988d848bd8577697bf9da
    result: PASS
    evidence: AI Platform CI 1052, Portal Web CI 139, Portal Universal E2E 144, zizmor 1158 and Freqtrade CI 1228 completed successfully, including pre-commit, documentation and the full core-test matrix.
  - command: squash merge PR 239
    result: PASS
    evidence: GitHub merged the reviewed owner head to develop as d85ed2c7700a10833aa32d84e7d10cc0a623179c.
blockers: []
next_action: Do not reopen this completed task; declare a separate bounded task for the next integration package while P11, P13 and P14 retain their existing gates.
```
