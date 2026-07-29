---
task_id: FTAI-20260729-ase-fr-01-feature-registry-service
status: implementing
branch: agent/ase-fr-01-feature-registry-service
base_branch: develop
created: 2026-07-29
updated: 2026-07-29
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - ai_strategy_engine/ARCHITECTURE.md
  - ai_strategy_engine/TASKS.md
  - ai_strategy_engine/docs/FEATURE_REGISTRY_V1.md
  - docs/ai_platform/ASE_FR_01_FEATURE_REGISTRY.md
search_first:
  - ai_strategy_engine/src/strategy_engine/registry.py
  - ai_strategy_engine/configs/feature_registry.v1.yaml
  - ai_platform/portal/feature_registry/
  - tests/ai_platform/portal/feature_registry/
owned_paths:
  - ai_strategy_engine/schemas/feature-registry.v1.schema.json
  - ai_strategy_engine/fixtures/feature_registry_parity.v1.json
  - ai_strategy_engine/tests/integration/test_feature_registry_service_contract.py
  - ai_strategy_engine/TASKS.md
  - ai_platform/portal/feature_registry/
  - ai_platform/portal/control_plane/api.py
  - tests/ai_platform/portal/feature_registry/
  - tests/ai_platform_integration/test_ase_fr_01_feature_registry_e2e.py
  - docs/ai_platform/ASE_FR_01_FEATURE_REGISTRY.md
  - docs/agents/tasks/FTAI-20260729-ase-fr-01-feature-registry-service.md
  - .github/workflows/ai-strategy-engine.yml
  - .github/workflows/ai-platform.yml
---

# ASE-FR-01 Feature Registry service

## Goal

Expose the canonical Strategy Engine Feature Registry as a schema-validated,
deterministic and read-only service with dependency resolution, parity fixtures,
append-only replay evidence and Portal API listing.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-29T17:00:00+02:00
checkpoint_carrier: self
head: c5ab22aac7e6ca9f2bfd94368c20da7e3a8ca76e
branch: agent/ase-fr-01-feature-registry-service
base_head: c5ab22aac7e6ca9f2bfd94368c20da7e3a8ca76e
pr: pending
status: implementing
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - ai_strategy_engine/ARCHITECTURE.md
  - ai_strategy_engine/TASKS.md
  - docs/ai_platform/ASE_FR_01_FEATURE_REGISTRY.md
proven:
  - ASE-01 merged normally into develop as c5ab22aac7e6ca9f2bfd94368c20da7e3a8ca76e after every required exact-head workflow succeeded.
  - The existing FeatureRegistry loader already validates parameters, constraints, dependencies and cycles.
  - ASE-FR-01 reuses that loader and resolver rather than duplicating registry semantics.
  - The service is read-only, requires model.read and cannot grant execution authority.
derived:
  - Deterministic hashes and an append-only parity fixture provide a stable contract for later constrained optimization and AI candidate generation.
unknown:
  - Exact-head workflow conclusions for the implementation commit.
conflicts: []
first_failure: null
rejected_hypotheses:
  - Create a second registry store or loader.
  - Add registry mutation or execution write paths.
  - Add Optuna, AI candidate generation, deployment or live trading in this package.
blockers: []
next_action: Commit the complete read-only service, open a dedicated PR, run exact-head validation, fix only evidenced failures and merge normally after every required check succeeds.
```
