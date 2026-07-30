---
task_id: FTAI-20260730-closure-contracts
status: completed
branch: agent/closure-contracts-terminal
base_branch: develop
created: 2026-07-30
updated: 2026-07-30
related_pr: 781
terminal_pr: null
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

## Terminal result

- PR #781 merged normally into `develop` as `6e489f7e10199120424cbcd01b3e125711630243`.
- The immutable contract freeze commit for downstream compatibility is `549ba3afddba39ce455fce5eebbd4d67bea813a6`.
- Existing StrategyDefinition `1.0.0` payloads remain readable and migrate deterministically to the typed `2.0.0` contract.
- Signal Wizard and Strategy Catalog contracts fail closed on tenant, actor, target, environment, idempotency and capability context.
- The contracts grant no execution, promotion or live-capital authority and expose no browser-to-Freqtrade, exchange or Vault path.

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
- No downstream worker may redefine the frozen shared contracts.

## Acceptance evidence

- One canonical import path exists for each new contract.
- Existing v1 payloads remain readable and deterministic migration evidence exists.
- Breaking semantic changes require a new version; additive optional changes retain compatibility tests.
- Focused and repository-wide CI passed on the exact synchronized implementation head.
- PR #781 had exactly the 12 owned paths, zero unresolved review threads and was zero commits behind `develop` before merge.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-30T16:31:00+02:00
head: 6e489f7e10199120424cbcd01b3e125711630243
branch: agent/closure-contracts-terminal
pr: 781
status: completed
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
  - PR 781 merged normally into develop as 6e489f7e10199120424cbcd01b3e125711630243.
  - Contract freeze commit 549ba3afddba39ce455fce5eebbd4d67bea813a6 is the immutable compatibility anchor for downstream workers.
  - Exact synchronized head 764eeac79fd7ea807b4845500bcd4bd05ca900c1 passed AI Platform CI run 30550888968, AI Strategy Engine run 30550890438, Freqtrade CI run 30550888947 and security analysis run 30550893131.
  - Freqtrade CI passed pre-commit, documentation, Python 3.11 through 3.14 core tests, coverage, generated-file checks, smoke tests, Ruff and mypy.
  - The merged change contains exactly the 12 declared owned paths and had zero unresolved review threads.
  - Typed AST, v2 JSON Schema, portal lifecycle contracts, v1 compatibility, secret exclusion, tenant scope and idempotency tests are merged on develop.
derived:
  - Downstream workers may now synchronize normally to develop at or after 6e489f7e10199120424cbcd01b3e125711630243 and consume the canonical contract imports.
  - The shared-contract workstream has no remaining autonomous implementation, validation, review or merge action.
unknown: []
conflicts: []
first_failure:
  marker: NONE
  evidence: All implementation, compatibility, synchronization, exact-head CI, review and merge gates passed.
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
  - command: AI Platform CI run 30550888968
    result: PASS
    evidence: Exact synchronized implementation head passed portal contract tests, Ruff and formatting.
  - command: AI Strategy Engine run 30550890438
    result: PASS
    evidence: Exact synchronized implementation head passed package tests, mypy, deterministic E2E, schema and security-boundary checks.
  - command: Freqtrade CI run 30550888947
    result: PASS
    evidence: Exact synchronized implementation head passed all required core, coverage, documentation and static-analysis gates.
  - command: GitHub Actions Security Analysis run 30550893131
    result: PASS
    evidence: Exact synchronized implementation head passed zizmor security analysis.
  - command: PR 781 live-base, changed-file and review-thread inspection
    result: PASS
    evidence: Zero commits behind develop, exactly 12 owned paths, mergeable and zero unresolved review threads before squash merge.
blockers: []
next_action: Closure coordinator synchronizes downstream workers to develop at or after 6e489f7e10199120424cbcd01b3e125711630243 using contract freeze commit 549ba3afddba39ce455fce5eebbd4d67bea813a6.
```
