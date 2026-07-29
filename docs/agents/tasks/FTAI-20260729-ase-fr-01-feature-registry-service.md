---
task_id: FTAI-20260729-ase-fr-01-feature-registry-service
status: complete
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
updated_at: 2026-07-29T20:44:00+02:00
head: 436d2934e120dacf64c81d594059e37667eebcac
branch: develop
pr: 705
status: ready
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
  - PR 705 merged normally into develop as 89905f37747acd4389f34a78608a8aa1690c2e57.
  - Final validated implementation head was 474048754f016afda842aea0e805f8faa2e1cda9.
  - AI Strategy Engine 30471615712, AI Platform CI 30471615203, Freqtrade CI 30471622983 and Security Analysis 30471619274 passed on the final head.
  - The service reuses the canonical FeatureRegistry loader and exposes deterministic read-only model.read routes.
  - Registry mutation, execution authority, order submission, protected-holdout access, private credentials, eval and exec remain absent.
  - Current develop at handoff is 436d2934e120dacf64c81d594059e37667eebcac and contains the ASE-FR-01 merge.
derived:
  - ASE-FR-01 is complete and provides the approved registry dependency gate required by constrained research and candidate generation.
unknown: []
conflicts: []
first_failure:
  marker: FEATURE_REGISTRY_RUFF_FORMATTING
  evidence: The initial import-order and line-length failure was repaired before the final exact-head workflow set passed.
rejected_hypotheses:
  - Modify registry semantics to fix formatting-only failures.
  - Create a second registry store or loader.
  - Add mutation, execution, Optuna, candidate generation, deployment or live trading to ASE-FR-01.
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
  - command: Final exact-head workflow set on 474048754f016afda842aea0e805f8faa2e1cda9
    result: PASS
    evidence: Required AI Strategy Engine, AI Platform, Freqtrade and workflow-security runs completed successfully.
  - command: Normal merge of PR 705
    result: PASS
    evidence: GitHub recorded merge commit 89905f37747acd4389f34a78608a8aa1690c2e57 without force push or check bypass.
  - command: python tools/agents/checkpoint.py docs/agents/tasks/FTAI-20260729-ase-fr-01-feature-registry-service.md --require-checkpoint
    result: PASS
    evidence: Compact checkpoint v1 validates against docs/agents/GOVERNANCE_CONTRACT.json.
blockers: []
next_action: Create FTAI-20260729-ase-02-constrained-research-optimization from current develop and begin its bounded preflight without modifying the merged ASE-FR-01 implementation.
```
