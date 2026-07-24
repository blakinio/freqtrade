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
  - tests/ai_platform_integration/test_liquidation_symbol_universe.py
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
updated_at: 2026-07-24T13:51:39+02:00
head: 50dfa88048ba00e30cb44843ac297221ae4f2be6
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
  - tests/ai_platform_integration/test_liquidation_symbol_universe.py
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
  - Every intended PI-03 backlog, architecture, UI-status and program documentation replacement is already present, so cleanup is idempotent and no temporary patch runner is required.
  - The temporary documentation workflow, patch script, trigger and diagnostic files are removed from the merge candidate.
  - Required AI Platform, Portal Web, Portal Universal E2E, zizmor and Freqtrade CI passed on synchronized PI-03 head 9b9b138d62244711ab8fc148514cce576f415bab.
  - Develop advanced to 9fdacb856cc9a26bc0783d567f7f919e9e053013 and introduced test_require_new_output_checks_every_multi_source_target, whose mkdir call deterministically failed on an already-created pytest tmp_path across all six core-test jobs.
  - Commit 50dfa88048ba00e30cb44843ac297221ae4f2be6 applies the minimal test-only correction by using exist_ok=True; no PI-03 production or browser contract changed.
derived:
  - The PI-03 implementation and Ruff cleanup remain behaviorally unchanged after synchronization with current develop.
  - The new required-CI blocker is an external base-test regression rather than a telemetry implementation failure.
unknown:
  - Final required CI result on the synchronized test-fix head.
conflicts: []
first_failure:
  marker: LIQUIDATION_TMP_PATH_ALREADY_EXISTS
  evidence: Freqtrade CI run 1174 failed tests/ai_platform_integration/test_liquidation_symbol_universe.py:99 with FileExistsError because tmp_path already existed and mkdir used exist_ok=False.
rejected_hypotheses:
  - Infer drift from model metadata age or training-window age.
  - Persist raw feature vectors or individual prediction values in the portal database.
  - Let drift status automatically promote, rollback or retrain a model.
  - Reuse protected final-holdout observations as iterative reference telemetry.
  - Combine reference and observation windows across runtime, config or source identities.
  - Treat Freqtrade CI run 1174 as an intermittent runner or xdist-only failure; the same test also failed in the single-process coverage job.
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
  - tests/ai_platform_integration/test_liquidation_symbol_universe.py
validation:
  - command: focused PI-03 telemetry and control-plane API pytest
    result: PASS
    evidence: 18 tests passed after timezone and compatibility fixes.
  - command: Ruff 0.15.21 diagnostic and cleanup
    result: PASS
    evidence: I001, E501 and formatting were auto-fixed; C901 was removed by bounded validator helpers and exact Ruff plus format checks passed.
  - command: required repository CI on synchronized head 9b9b138d62244711ab8fc148514cce576f415bab
    result: PASS
    evidence: AI Platform CI 996, Portal Web CI 133, Portal Universal E2E 138, zizmor 1093 and Freqtrade CI 1163 completed successfully.
  - command: Freqtrade CI run 1174 on merge ref 3e5a4278f3db9cc7e16c5af4e08019300dcfa4ef
    result: FAIL
    evidence: All six core-test jobs failed the same newly merged liquidation-universe test because pathlib.mkdir used exist_ok=False on pytest tmp_path.
  - command: required repository CI on owner head after base-test correction
    result: NOT_RUN
    evidence: Pending on the current checkpoint commit.
blockers:
  - Required repository CI has not completed on the synchronized test-fix head.
next_action: Complete required CI on the synchronized test-fix head; if green, update the checkpoint to ready and mark PR 239 ready for review.
```
