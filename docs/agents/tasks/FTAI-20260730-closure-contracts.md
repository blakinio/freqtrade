---
task_id: FTAI-20260730-closure-contracts
status: ready
branch: agent/closure-contracts
base_branch: develop
created: 2026-07-30
updated: 2026-07-30
related_pr: null
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
updated_at: 2026-07-30T10:55:00+02:00
head: 1d347a785eddc900f4484c30e06c3ab4e8851b29
branch: agent/closure-contracts
pr: null
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
  - Existing v1 models, schemas and idempotency are proven, but `StrategyDefinition` condition groups remain untyped dictionaries and the product catalog contract contains only static summary fields. This is a real shared-contract gap.
derived:
  - The bounded implementation scope is restricted to 12 exact path entries.
unknown:
  - Exact implementation HEAD, PR number and CI run IDs until the worker starts.
conflicts: []
first_failure:
  marker: PRE_IMPLEMENTATION_GATE
  evidence: Implementation has not started; the Gate 0 dispatch condition is the first enforced gate.
rejected_hypotheses:
  - An unchecked backlog box alone proves missing implementation.
  - A downstream worker may redefine shared contracts.
  - Repository fixtures may be described as real external acceptance.
changed_paths: []
validation:
  - command: python tools/agents/checkpoint.py <task-path> --require-checkpoint
    result: PASS
    evidence: Gate 0 validates this compact checkpoint before dispatch.
blockers: []
next_action: Create the branch from current develop, implement the typed AST and portal closure contracts, run contract tests, and open one focused PR.
```
