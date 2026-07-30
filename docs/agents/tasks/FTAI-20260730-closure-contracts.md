---
task_id: FTAI-20260730-closure-contracts
status: ready
branch: agent/closure-contracts
base_branch: develop
created: 2026-07-30
updated: 2026-07-30
related_pr: 781
dependencies:
  - none
owned_paths:
  - docs/agents/tasks/FTAI-20260730-closure-contracts.md
  - ai_strategy_engine/src/strategy_engine/domain/models.py
  - ai_strategy_engine/src/strategy_engine/domain/__init__.py
  - ai_strategy_engine/src/strategy_engine/dsl/ast.py
  - ai_strategy_engine/src/strategy_engine/dsl/__init__.py
  - ai_strategy_engine/src/strategy_engine/dsl/validator.py
  - ai_strategy_engine/schemas/strategy-definition.v2.schema.json
  - ai_strategy_engine/tests/unit/test_dsl_ast.py
  - ai_platform/portal/contracts/strategy_closure.py
  - ai_platform/portal/contracts/__init__.py
  - ai_platform/portal/product/schema.py
  - tests/ai_platform/portal/test_strategy_closure_contracts.py
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260730-ai-program-closure-orchestration.md
  - docs/ai_platform/PROGRAM_CLOSURE_MATRIX.md
  - ai_strategy_engine/TASKS.md
search_first:
  - current develop, open PRs and exact owned-path conflicts
  - canonical implementation and tests before adding code
  - shared contract freeze commit and dependency state
---

# Closure shared contracts

## Goal

Freeze the one canonical typed Strategy DSL AST and the versioned Signal Wizard/Strategy Catalog read and command contracts required by downstream work.

## Evidence at Gate 0

Existing v1 models, schemas and idempotency are proven, but `StrategyDefinition` condition groups remain untyped dictionaries and the product catalog contract contains only static summary fields. This is a real shared-contract gap.

## Deliverables

- Typed recursive condition AST with stable reason codes and no arbitrary code execution.
- Versioned v2 StrategyDefinition schema with explicit compatibility from v1.
- Signal Wizard preview/submit contracts with tenant, actor, provenance, idempotency and research-only authority.
- Strategy Catalog history/approval/deployment/rollback/provenance contracts with capability requirements.
- Backward-compatibility, secret-exclusion, tenant-scope and idempotency tests.
- A recorded contract freeze commit for downstream workers.

## Non-negotiable boundaries

- Paper, shadow or dry-run only; no live-capital authority.
- No browser-to-Freqtrade, exchange or Vault path.
- No protected-holdout reuse and no changes to frozen thresholds `0.006/-0.009`.
- Stay inside exact `owned_paths`; stop on the first incompatible shared-contract requirement.
- Add tests at the same layer and merge only through normal green CI.
- This task is the exclusive mutable owner of shared contracts until its PR merges.

## Acceptance criteria

- One canonical import path exists for each new contract.
- Existing v1 payloads remain readable or receive a deterministic migration result.
- Breaking semantic changes require a new version; additive optional fields require compatibility tests.
- No contract grants execution, promotion or live-capital authority.

## Validation

Run narrow tests first, then all repository workflows required by the changed paths. Validate this task checkpoint before every handoff.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-30T13:29:00+02:00
head: 5a3aa56114f4d03979ed868e94e5dadd3a5cddaa
branch: agent/closure-contracts
pr: 781
status: ready
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260730-ai-program-closure-orchestration.md
  - docs/ai_platform/PROGRAM_CLOSURE_MATRIX.md
owned_paths:
  - docs/agents/tasks/FTAI-20260730-closure-contracts.md
  - ai_strategy_engine/src/strategy_engine/domain/models.py
  - ai_strategy_engine/src/strategy_engine/domain/__init__.py
  - ai_strategy_engine/src/strategy_engine/dsl/ast.py
  - ai_strategy_engine/src/strategy_engine/dsl/__init__.py
  - ai_strategy_engine/src/strategy_engine/dsl/validator.py
  - ai_strategy_engine/schemas/strategy-definition.v2.schema.json
  - ai_strategy_engine/tests/unit/test_dsl_ast.py
  - ai_platform/portal/contracts/strategy_closure.py
  - ai_platform/portal/contracts/__init__.py
  - ai_platform/portal/product/schema.py
  - tests/ai_platform/portal/test_strategy_closure_contracts.py
proven:
  - Gate 0 is terminal and the contract workstream is READY with exclusive ownership of all 12 declared paths.
  - Contract freeze commit 549ba3afddba39ce455fce5eebbd4d67bea813a6 adds the canonical typed recursive Strategy DSL AST, stable reason codes and strict v2 JSON Schema while retaining readable v1 payloads and evaluator Mapping compatibility.
  - The same freeze commit adds versioned Signal Wizard and Strategy Catalog contracts with tenant, actor, target, provenance, idempotency and explicit capability evidence.
  - Portal closure contracts expose no execution, promotion or live-capital authority and reject secret-bearing metadata.
  - Focused compatibility and safety validation passed with 11 tests, Python compilation and Draft 2020-12 schema validation.
  - Exact freeze head passed AI Platform CI run 30537501408, AI Strategy Engine run 30537501338, Freqtrade CI run 30537501286 and security analysis run 30537501418.
  - Synchronization PR 786 merged current develop normally as 5a3aa56114f4d03979ed868e94e5dadd3a5cddaa after Freqtrade CI run 30537660168 passed pre-commit, documentation and Python 3.11-3.14 core gates.
  - PR 781 is zero commits behind develop, changes exactly the 12 owned paths and has no review comments or unresolved threads.
derived:
  - `549ba3afddba39ce455fce5eebbd4d67bea813a6` is the immutable shared-contract freeze commit downstream workers must consume after PR 781 merges.
  - The task-record-only readiness commit may be merged after its exact-head required checks pass.
unknown:
  - Exact squash merge commit until PR 781 is merged normally.
conflicts: []
first_failure:
  marker: NONE
  evidence: No implementation, compatibility, CI, ownership, synchronization or review failure remains at the validated readiness head.
rejected_hypotheses:
  - An unchecked backlog box alone proves missing implementation.
  - A downstream worker may redefine shared contracts.
  - Repository fixtures may be described as real external acceptance.
changed_paths:
  - docs/agents/tasks/FTAI-20260730-closure-contracts.md
  - ai_strategy_engine/src/strategy_engine/domain/models.py
  - ai_strategy_engine/src/strategy_engine/domain/__init__.py
  - ai_strategy_engine/src/strategy_engine/dsl/ast.py
  - ai_strategy_engine/src/strategy_engine/dsl/__init__.py
  - ai_strategy_engine/src/strategy_engine/dsl/validator.py
  - ai_strategy_engine/schemas/strategy-definition.v2.schema.json
  - ai_strategy_engine/tests/unit/test_dsl_ast.py
  - ai_platform/portal/contracts/strategy_closure.py
  - ai_platform/portal/contracts/__init__.py
  - ai_platform/portal/product/schema.py
  - tests/ai_platform/portal/test_strategy_closure_contracts.py
validation:
  - command: pytest -q ai_strategy_engine/tests/unit/test_dsl_ast.py tests/ai_platform/portal/test_strategy_closure_contracts.py
    result: PASS
    evidence: 11 focused compatibility and safety contract tests passed in the isolated validation harness.
  - command: python -m compileall -q strategy_engine ai_platform
    result: PASS
    evidence: All changed Python modules compiled successfully in the isolated validation harness.
  - command: Draft202012Validator.check_schema(strategy-definition.v2.schema.json)
    result: PASS
    evidence: The published v2 JSON Schema is valid Draft 2020-12.
  - command: AI Platform CI run 30537501408
    result: PASS
    evidence: Exact freeze head passed the full portal contract suite, Ruff and format checks.
  - command: AI Strategy Engine run 30537501338
    result: PASS
    evidence: Exact freeze head passed package tests, Ruff, mypy, compile, deterministic E2E, schemas and security-boundary checks.
  - command: Freqtrade CI runs 30537501286 and 30537660168
    result: PASS
    evidence: Exact freeze and synchronized heads passed pre-commit, documentation, Python 3.11-3.14 core tests, coverage, generated-file checks, smoke tests, Ruff and mypy.
  - command: GitHub Actions Security Analysis run 30537501418
    result: PASS
    evidence: Exact freeze head completed zizmor security analysis successfully.
  - command: PR 781 changed-file, live-base, comments and review-thread inspection
    result: PASS
    evidence: Exactly 12 owned paths, zero commits behind develop, mergeable draft, zero comments and zero unresolved review threads.
blockers: []
next_action: Mark PR 781 ready and squash-merge it normally after the task-record-only exact-head required checks pass, then return contract freeze commit 549ba3afddba39ce455fce5eebbd4d67bea813a6 to the closure coordinator for downstream synchronization.
```
