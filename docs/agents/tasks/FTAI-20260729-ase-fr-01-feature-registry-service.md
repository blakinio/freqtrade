---
task_id: FTAI-20260729-ase-fr-01-feature-registry-service
status: validating
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
updated_at: 2026-07-29T17:26:00+02:00
checkpoint_carrier: self
validated_parent_head: 8257633e45d04e2e8fa97c74b47642863992732f
branch: agent/ase-fr-01-feature-registry-service
base_head: c5ab22aac7e6ca9f2bfd94368c20da7e3a8ca76e
pr: 705
status: validating
exact_head_resolution: Resolve checkpoint_carrier from the current PR 705 head; required GitHub checks and the PR body attached to that commit are authoritative.
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - ai_strategy_engine/ARCHITECTURE.md
  - ai_strategy_engine/TASKS.md
  - ai_strategy_engine/docs/FEATURE_REGISTRY_V1.md
  - docs/ai_platform/ASE_FR_01_FEATURE_REGISTRY.md
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
proven:
  - ASE-01 merged normally into develop as c5ab22aac7e6ca9f2bfd94368c20da7e3a8ca76e after every required exact-head workflow succeeded.
  - PR 705 is open, ready for review, mergeable and synchronized with develop at behind_by 0.
  - The existing FeatureRegistry loader validates parameters, constraints, dependencies and cycles; ASE-FR-01 reuses it rather than introducing a second registry implementation.
  - A public Draft 2020-12 schema, deterministic manifest/definition/snapshot/replay hashes, a 21-feature append-only prefix and semantic parity fixtures are present.
  - Read models expose snapshot, list, detail, dependency resolution and replay through GET-only model.read Portal routes.
  - The service rejects execution authority and introduces no mutation endpoint, execution write path, order submission, protected-holdout access, private credentials, eval or exec.
  - Package and Portal tests passed before Ruff on the first implementation validation run.
derived:
  - The Feature Registry contract is a safe dependency gate for later constrained optimization and schema-bound AI candidate generation.
unknown:
  - Final conclusions of required workflows attached to the checkpoint carrier head.
conflicts: []
first_failure:
  marker: FEATURE_REGISTRY_RUFF_FORMATTING
  evidence: AI Strategy Engine run 30465460734 passed package and Portal research tests, then failed Ruff on two import-order findings and one 101-character line.
rejected_hypotheses:
  - Modify registry semantics to fix formatting-only failures.
  - Create a second registry store or loader.
  - Add registry mutation or execution write paths.
  - Add Optuna, AI candidate generation, deployment or live trading in this package.
changed_paths:
  - ai_strategy_engine/schemas/feature-registry.v1.schema.json
  - ai_strategy_engine/fixtures/feature_registry_parity.v1.json
  - ai_strategy_engine/tests/integration/test_feature_registry_service_contract.py
  - ai_strategy_engine/TASKS.md
  - ai_platform/portal/feature_registry/
  - ai_platform/portal/control_plane/api.py
  - tests/ai_platform/portal/feature_registry/
  - tests/ai_platform_integration/test_ase_fr_01_feature_registry_e2e.py
  - docs/ai_platform/ASE_FR_01_FEATURE_REGISTRY.md
  - .github/workflows/ai-strategy-engine.yml
  - .github/workflows/ai-platform.yml
validation:
  - command: First implementation AI Strategy Engine run 30465460734
    result: FAIL
    evidence: Package and Portal research tests passed; Ruff reported only import organization and one line-length violation.
  - command: Evidenced formatting repair
    result: PASS
    evidence: Service imports and long line fixed in 5fae5899798031c57e7dbd54f33803fd9cf22ea9; contract-test imports fixed in 8257633e45d04e2e8fa97c74b47642863992732f.
  - command: Final checkpoint-carrier workflow suite
    result: REQUIRED
    evidence: AI Strategy Engine, AI Platform CI, Freqtrade CI and GitHub Actions Security Analysis must all succeed on the current PR head before normal merge.
known_limitations:
  - Read-only registry service; no mutation, optimization, generation, deployment or execution authority.
  - Parity fixtures cover the canonical append-only prefix and selected semantics, not proprietary implementation parity.
missing_functions:
  - ASE-02 immutable dataset manifest, constrained Optuna, trial lineage, robustness score and registry-restricted AI candidate generation.
blockers: []
next_action: Verify every required workflow on the current PR 705 head, update the PR body with exact-head evidence, confirm develop remains unchanged and merge normally without bypassing checks.
```
