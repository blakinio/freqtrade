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
updated_at: 2026-07-24T11:25:00+02:00
head: 65ed0b0fccd8e0784d11f1edfeb9c83daa1b987a
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
  - PR 239 implements aggregate-only inference windows, source status and deterministic PSI-v1 assessments with exact tenant, model, feature-schema, bot-config, runtime and source attribution.
  - Raw feature values, individual predictions, credentials and private endpoints are excluded from the PI-03 persistence and browser contracts.
  - Missing, unavailable, stale, insufficient or bucket-incompatible evidence never produces HEALTHY.
  - Telemetry ingestion requires service or system identity with MODEL_TRAIN and rejects cross-tenant or mismatched attribution.
  - Duplicate telemetry identities are idempotent only for the same canonical payload; conflicting reuse is rejected.
  - Model Health API and UI expose window identities, sample counts, source availability and PSI or feature-quality evidence without lifecycle mutation.
  - Focused telemetry and control-plane API tests passed with 18 tests.
  - The latest standard AI Platform CI test step passed; its Ruff step failed.
  - Portal Web CI, Portal Universal E2E and zizmor passed on owner-authored head cf9521ffc66bdcea187e60872ce7478163454dd5.
  - Freqtrade documentation build and core test matrix passed except pre-commit and the Python 3.13 Ruff step.
  - The backlog PI-03 table row is already active; the remaining documentation replacements are partially applied and must be completed idempotently.
  - PR 239 currently contains four temporary handover or documentation artifacts that are not intended for merge.
derived:
  - The remaining code-quality failure is mechanical Ruff or formatting work rather than a failing PI-03 behavioral test.
  - The documentation patch must treat already-applied replacements as success before cleaning temporary artifacts.
  - A final owner-authored commit is required after cleanup so normal repository workflows run instead of action_required bot-head checks.
unknown:
  - Exact Ruff findings have not yet been captured in a compact durable file.
  - PR mergeability must be rechecked after temporary artifacts are removed and the branch is synchronized with current develop.
conflicts: []
first_failure:
  marker: RUFF_PRECOMMIT_AND_TEMP_DOC_PATCH
  evidence: AI tests pass but Ruff and Freqtrade pre-commit fail; the non-idempotent docs patch stopped after an already-applied backlog replacement and left temporary workflow, script, trigger and diagnostic files.
rejected_hypotheses:
  - Infer drift from model metadata age or training-window age.
  - Persist raw feature vectors or individual prediction values in the portal database.
  - Let drift status automatically promote, rollback or retrain a model.
  - Reuse protected final-holdout observations as iterative reference telemetry.
  - Combine reference and observation windows across runtime, config or source identities.
changed_paths:
  - .github/workflows/pi03-docs-patch.yml
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
  - docs/agents/tasks/PI03_DOCS_RUN_DIAGNOSTIC.txt
  - docs/agents/tasks/PI03_DOCS_TRIGGER.txt
  - docs/ai_platform/portal/DATA_AND_OBSERVABILITY_ARCHITECTURE.md
  - docs/ai_platform/portal/POST_P12_INTEGRATION_BACKLOG.md
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
  - tests/ai_platform/portal/control_plane/test_api.py
  - tests/ai_platform/portal/telemetry/test_inference_telemetry.py
  - tools/agents/pi03_docs_patch.py
validation:
  - command: focused PI-03 telemetry and control-plane API pytest
    result: PASS
    evidence: 18 tests passed after timezone and compatibility fixes.
  - command: AI Platform CI test step on owner head cf9521ffc66bdcea187e60872ce7478163454dd5
    result: PASS
    evidence: Full AI Platform pytest completed successfully before Ruff.
  - command: ruff check ai_platform tests/ai_platform
    result: FAIL
    evidence: Standard AI Platform CI run 934 failed at Ruff after tests passed.
  - command: Portal Web CI on owner head cf9521ffc66bdcea187e60872ce7478163454dd5
    result: PASS
    evidence: Workflow run 121 completed successfully.
  - command: Portal Universal E2E on owner head cf9521ffc66bdcea187e60872ce7478163454dd5
    result: PASS
    evidence: Workflow run 126 completed successfully.
  - command: GitHub Actions Security Analysis on owner head cf9521ffc66bdcea187e60872ce7478163454dd5
    result: PASS
    evidence: Workflow run 1023 completed successfully.
  - command: Freqtrade CI on owner head cf9521ffc66bdcea187e60872ce7478163454dd5
    result: FAIL
    evidence: Core tests and docs passed; pre-commit and Python 3.13 Ruff failed.
blockers:
  - Ruff and pre-commit failures must be fixed before PR 239 can become review-ready.
  - Temporary documentation workflow, patch script, trigger and diagnostic files must be removed before merge.
next_action: Capture exact Ruff findings, apply Ruff fix and format, make the documentation patch idempotent, remove all four temporary artifacts, then create one owner-authored commit and rerun required CI.
```
