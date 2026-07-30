---
task_id: FTAI-20260730-closure-signal-wizard-backend
status: ready
branch: agent/closure-signal-wizard-backend
base_branch: develop
created: 2026-07-30
updated: 2026-07-30
related_pr: null
dependencies:
  - FTAI-20260730-closure-contracts merged as 6e489f7e10199120424cbcd01b3e125711630243
  - Signal Wizard blocker PR 818 and terminal PR 820 merged
owned_paths:
  - docs/agents/tasks/FTAI-20260730-closure-signal-wizard-backend.md
  - ai_platform/portal/control_plane/api.py
  - ai_platform/portal/control_plane/database.py
  - ai_platform/portal/signal_wizard/__init__.py
  - ai_platform/portal/signal_wizard/models.py
  - ai_platform/portal/signal_wizard/repository.py
  - ai_platform/portal/signal_wizard/router.py
  - ai_platform/portal/signal_wizard/service.py
  - ai_platform/portal/signal_wizard/migrations/0001_signal_wizard.sql
  - tests/ai_platform/portal/signal_wizard/__init__.py
  - tests/ai_platform/portal/signal_wizard/test_signal_wizard.py
  - tests/ai_platform_integration/test_signal_wizard_backend_e2e.py
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/prompts/ai-program-closure/WORKER-COMMON-RULES.md
  - docs/agents/tasks/FTAI-20260730-ai-program-closure-orchestration.md
  - docs/ai_platform/PROGRAM_CLOSURE_MATRIX.md
  - docs/agents/tasks/FTAI-20260730-closure-ui-signal-wizard.md
  - ai_platform/portal/contracts/strategy_closure.py
  - ai_strategy_engine/src/strategy_engine/dsl/validator.py
---

# Closure Signal Wizard backend/API

## Goal

Implement the missing canonical, tenant-scoped Signal Wizard preview and durable submit application services and register same-origin Portal control-plane endpoints. This task owns backend/API convergence only; the existing frontend child remains `WAIT_FOR_BACKEND` until this task merges normally with green exact-head CI.

## Canonical endpoints

- `POST /v1/signal-wizard/preview` consumes `SignalWizardPreviewCommand` and returns `SignalWizardPreviewResult`.
- `POST /v1/signal-wizard/submit` consumes `SignalWizardSubmitCommand` and returns `SignalWizardSubmitResult`.
- Both endpoints use the authenticated Portal `RequestContext`; command tenant, actor, target, environment and authority must match or fail closed.
- `Idempotency-Key` must be bounded and equal the command idempotency key.

## Required semantics

### Preview

- Reuse the canonical Feature Registry manifest/service; do not create a local feature allowlist.
- Reject every referenced feature that is missing, not `approved_for_ai`, not research-only compatible or invalid for its declared parameters/timeframe.
- Preserve exact feature IDs, enablement, timeframes, parameters, parameter constraints, target context and provenance.
- Normalize and validate `condition_ast` through the canonical typed DSL AST/validator. Do not use `eval`, `exec`, source generation or a source-code compiler.
- Do not invent universe, risk or execution fields that the frozen command does not provide and do not claim compatibility with the two fixed Strategy Lab catalog strategies.
- Return a deterministic v2 research-draft envelope in `strategy_definition`; derive its immutable draft version from the canonical preview request digest.
- Compute `preview_hash` from canonical JSON of the returned strategy-definition envelope.
- Persist the preview durably before returning it so submit can resolve the hash without transient process state.

### Submit

- Resolve `preview_hash` only inside the authenticated tenant.
- Require the submitted expected strategy version to equal the immutable version stored with the preview.
- Persist one durable research experiment-admission record referencing the immutable preview; this is not a backtest result, deployment, promotion or execution request.
- Derive the durable experiment ID deterministically from tenant, idempotency key and canonical request digest; never return a transient/random candidate ID.
- Same tenant plus same idempotency key and same request returns the same result. Reuse with different content fails with conflict. Cross-tenant keys and hashes remain isolated.

## Deterministic reason codes

At minimum cover and test stable codes for context mismatch, idempotency conflict, unknown feature, feature not approved for AI, invalid feature parameters, invalid constraints, invalid DSL, preview not found, preview hash/version mismatch, preview valid and submit accepted. Router errors must expose bounded reason-code payloads without secret values or internal paths.

## Persistence and compatibility

- Add SQLAlchemy models, repository logic and a versioned SQL migration under the owned package.
- Store canonical JSON/digests required to prove exact feature identity, typed DSL, actor/target/environment/provenance and idempotency.
- Register the package models in `create_schema` and inject/register the service/router in canonical `control_plane.api.create_app`.
- Consume frozen PR #781 contracts unchanged. Do not modify shared contracts, common exports, frontend paths, Strategy Lab fixed catalog definitions or Feature Registry source files.

## Safety boundaries

- Research-only authority.
- No execution, order submission, deployment, approval, promotion or live-capital authority.
- No browser-to-Freqtrade, exchange or Vault path.
- No credentials, tokens, private endpoints, secret-bearing metadata, protected-holdout use or threshold changes.
- No mock-only BFF, transient candidate IDs or false mapping to incompatible fixed strategies.

## Acceptance

- Focused service tests prove approved-feature validation, exact identity/parameter/typed-DSL preservation, deterministic hashes/reason codes and fail-closed errors.
- API tests prove same-origin route registration, authenticated context matching, bounded payloads and no secret leakage.
- Repository/integration tests prove durable preview/submit, tenant isolation, idempotency replay/conflict, version compatibility and restart-safe lookup.
- Existing contract and Strategy Lab compatibility remains green.
- Exact owned paths remain disjoint from open PRs.
- Required exact-head CI passes, unresolved review threads are zero and the focused PR merges normally.
- The terminal checkpoint leaves exactly one next action: Agent 0 marks the frontend Signal Wizard `READY` from the merged backend evidence.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-30T22:27:00+02:00
head: 38f7ad50cfe1b03fdf7a6e9ee4a9b73ebbebe7de
branch: agent/closure-signal-wizard-backend
pr: null
status: ready
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/prompts/ai-program-closure/WORKER-COMMON-RULES.md
  - docs/agents/tasks/FTAI-20260730-ai-program-closure-orchestration.md
  - docs/ai_platform/PROGRAM_CLOSURE_MATRIX.md
  - docs/agents/tasks/FTAI-20260730-closure-ui-signal-wizard.md
  - ai_platform/portal/contracts/strategy_closure.py
  - ai_strategy_engine/src/strategy_engine/dsl/validator.py
owned_paths:
  - docs/agents/tasks/FTAI-20260730-closure-signal-wizard-backend.md
  - ai_platform/portal/control_plane/api.py
  - ai_platform/portal/control_plane/database.py
  - ai_platform/portal/signal_wizard/__init__.py
  - ai_platform/portal/signal_wizard/models.py
  - ai_platform/portal/signal_wizard/repository.py
  - ai_platform/portal/signal_wizard/router.py
  - ai_platform/portal/signal_wizard/service.py
  - ai_platform/portal/signal_wizard/migrations/0001_signal_wizard.sql
  - tests/ai_platform/portal/signal_wizard/__init__.py
  - tests/ai_platform/portal/signal_wizard/test_signal_wizard.py
  - tests/ai_platform_integration/test_signal_wizard_backend_e2e.py
proven:
  - develop 38f7ad50cfe1b03fdf7a6e9ee4a9b73ebbebe7de contains frozen Signal Wizard v2 commands/results from PR 781.
  - PR 818 and terminal PR 820 prove no canonical Signal Wizard service or registered preview/submit routes exist.
  - control_plane.api currently registers only Feature Registry and Strategy Lab extension routers.
  - The new signal_wizard package paths do not exist on develop.
  - Open PR 823 changes only the Research Data task, PR 816 one WickHunter request and PR 758 deployment preflight paths.
derived:
  - A dedicated durable Signal Wizard admission store is required because fixed Strategy Lab definitions cannot preserve arbitrary approved feature identity.
  - The frozen result contract supports a non-executable v2 research-draft envelope without inventing missing runtime fields.
unknown:
  - Exact implementation head, PR number and workflow run IDs until the backend worker starts.
conflicts: []
first_failure:
  marker: NONE
  evidence: Contract, dependency and owned-path preflight passes; the bounded backend child is ready to start from current develop.
rejected_hypotheses:
  - Create transient preview or candidate state in the browser or BFF.
  - Map arbitrary approved selections to tv_supertrend_v1 or tv_squeeze_momentum_v1.
  - Redefine frozen Signal Wizard contracts or invent missing execution fields.
  - Grant execution, deployment, promotion or live-capital authority.
changed_paths: []
validation:
  - command: develop identity comparison
    result: PASS
    evidence: develop is identical to 38f7ad50cfe1b03fdf7a6e9ee4a9b73ebbebe7de.
  - command: open PR changed-path inventory
    result: PASS
    evidence: PRs 823, 816 and 758 have no overlap with the declared backend ownership.
  - command: canonical service and route inventory
    result: PASS
    evidence: No signal_wizard package or registered preview/submit service exists; the gap is bounded and non-duplicative.
blockers: []
next_action: Start the backend worker from current develop using docs/agents/prompts/ai-program-closure/SIGNAL-WIZARD-BACKEND-AGENT-PROMPT.md.
```
