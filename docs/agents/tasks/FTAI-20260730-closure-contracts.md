---
task_id: FTAI-20260730-closure-contracts
status: validating
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
updated_at: 2026-07-30T12:48:00+02:00
head: f376b1e29c5cf2cce5ff02ec84b66b237f7c819c
branch: agent/closure-contracts
pr: 781
status: validating
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
  - Existing v1 StrategyDefinition payloads parse into the typed recursive AST and preserve their JSON wire shape.
  - The typed AST remains compatible with the existing evaluator through read-only Mapping semantics.
  - Signal Wizard and Strategy Catalog v2 contracts require tenant, actor, target, provenance, idempotency and explicit capability evidence.
  - Portal closure contracts expose no execution, promotion or live-capital authority and reject secret-bearing metadata.
derived:
  - `f376b1e29c5cf2cce5ff02ec84b66b237f7c819c` is the pre-checkpoint implementation freeze candidate for downstream consumers.
  - PR #781 is the only open PR modifying the shared contract paths.
unknown:
  - Exact-head required CI conclusions after the checkpoint and normal develop synchronization commits.
  - Unresolved review-thread count at the final merge gate.
conflicts: []
first_failure:
  marker: EXACT_HEAD_VALIDATION_PENDING
  evidence: Repository CI is queued for PR #781 and the branch must include current develop before final validation.
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
  - command: python tools/agents/checkpoint.py docs/agents/tasks/FTAI-20260730-closure-contracts.md --require-checkpoint
    result: NOT_RUN
    evidence: The repository checkpoint validator will run in exact-head CI because the sandbox cannot clone the private repository.
blockers:
  - Exact-head required CI and review verification remain pending.
next_action: Synchronize current develop through PR #782, inspect PR #781 exact-head CI and review threads, repair only evidenced failures, and merge normally when every required gate is green.
```
