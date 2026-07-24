---
task_id: FTAI-20260724-portal-pi03-inference-drift-telemetry
status: active
branch: feat/portal-pi03-inference-drift-telemetry-20260724
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
updated_at: 2026-07-24T10:55:00+02:00
head: 8a747cf05d6affdb21e2d0c5599521c6941450be
branch: feat/portal-pi03-inference-drift-telemetry-20260724
pr: 239
status: validating
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
  - develop preflight head was 12383471a0e2d1b3d8278504b5dfc7f7ccab3f38 after PI-01 closure; develop later advanced to 49167cdf9ab6fd126de72613101c35fef6cc07e2 through disjoint RL documentation PR 237.
  - Open PR 236 owns only liquidation research paths and does not overlap PI-03 portal telemetry ownership.
  - Versioned aggregate-only telemetry preserves exact tenant, ModelVersion, feature-schema, bot, immutable config revision, runtime and source identity.
  - Durable reference/observation windows, source availability and drift assessments are stored separately with canonical JSON payloads and indexed attribution fields.
  - PSI-v1 records minimum samples, attention/degraded thresholds, feature-quality thresholds and smoothing epsilon; incompatible or insufficient evidence never reports HEALTHY.
  - Ingestion requires service/system identity plus MODEL_TRAIN and rejects tenant, model, feature-schema, bot and config-revision mismatches.
  - Duplicate telemetry IDs are idempotent only for the same canonical payload; conflicting reuse is rejected.
  - Model Health API/UI exposes window identities, sample counts, source availability and PSI/feature-quality evidence without raw features or individual predictions.
  - Telemetry ingestion and reads leave ModelVersion lifecycle and promotion slots unchanged.
  - Focused telemetry and API validation passed with 18 tests.
  - Full AI suite reached 493 passed and 1 skipped; its sole compatibility failure was the historical unavailable reason code and that reason code has been restored.
derived:
  - Exact scope grouping prevents reference and observation evidence from different runtime/config/source identities from being compared or aggregated together.
  - A separate aggregate-only telemetry module avoids coupling PI-03 to raw runtime logging, PI-04 or product settings.
  - Drift status remains operational evidence only and cannot authorize promotion, retraining, risk or execution changes.
unknown:
  - Final repository CI result after the compatibility fix and canonical documentation update.
conflicts: []
first_failure:
  marker: resolved
  evidence: SQLite returned a naive checked_at column and an existing public unavailable reason code changed; repository comparison now uses canonical JSON timestamps and the historical reason code is preserved.
rejected_hypotheses:
  - Infer drift from model metadata age or training-window age.
  - Persist raw feature vectors or individual prediction values in the portal database.
  - Let drift status automatically promote, rollback or retrain a model.
  - Reuse protected final-holdout observations as iterative reference telemetry.
  - Combine reference and observation windows across runtime, config or source identities.
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
  - tests/ai_platform/portal/control_plane/test_api.py
  - tests/ai_platform/portal/telemetry/test_inference_telemetry.py
  - docs/agents/tasks/FTAI-20260724-portal-pi03-inference-drift-telemetry.md
validation:
  - command: focused PI-03 telemetry and control-plane API pytest
    result: PASS
    evidence: 18 passed on the compatibility-fixed implementation path.
  - command: full AI Platform pytest before final compatibility rerun
    result: PASS
    evidence: 493 tests passed and 1 skipped; the single historical reason-code assertion was identified and fixed before final repository CI.
blockers: []
next_action: Apply the canonical PI-03 documentation patch, remove its temporary workflow, then resolve only concrete final repository CI findings before marking PR 239 ready.
```
