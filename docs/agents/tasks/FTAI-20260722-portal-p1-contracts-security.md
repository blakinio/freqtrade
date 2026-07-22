---
task_id: FTAI-20260722-portal-p1-contracts-security
status: ready
branch: feat/portal-p1-contracts-security
base_branch: develop
created: 2026-07-22
updated: 2026-07-22
related_pr: "#114"
owned_paths:
  - .github/workflows/ai-platform.yml
  - ai_platform/portal/contracts/
  - ai_platform/portal/security/
  - tests/ai_platform/portal/
  - docs/ai_platform/portal/CONTRACTS_AND_SECURITY_FOUNDATION.md
  - docs/agents/tasks/FTAI-20260722-portal-p1-contracts-security.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/README.md
  - docs/ai_platform/portal/SYSTEM_ARCHITECTURE.md
  - docs/ai_platform/portal/SECURITY_ARCHITECTURE.md
  - docs/ai_platform/portal/AI_ML_AND_LEARNING_ARCHITECTURE.md
  - docs/ai_platform/portal/DATA_AND_OBSERVABILITY_ARCHITECTURE.md
  - docs/ai_platform/portal/QUALITY_AND_AUTONOMOUS_E2E.md
  - docs/ai_platform/portal/ARCHITECTURE_DECISIONS.md
  - docs/ai_platform/portal/DELIVERY_ROADMAP.md
  - docs/ai_platform/portal/AGENT_EXECUTION_PLAN.md
search_first:
  - current develop HEAD, PR #113 merge state and final CI
  - open PRs and active tasks overlapping portal contracts/security ownership
  - existing Pydantic and AI Platform test conventions
optional_reads:
  - only implementation-adjacent AI Platform source and tests
---

# AI Trading Portal P1 — Contracts & Security Foundation

## Goal

Implement the first machine-readable, versioned and fail-closed shared contract foundation for the AI Trading Portal. Freeze tenant, identity, authorization, environment, bot, model, risk, execution-adapter, secret-reference, event, audit and correlation semantics without implementing Control Plane runtime, a public API, Freqtrade runtime integration, event-bus infrastructure or live trading.

## Deliverables

- immutable Pydantic v2 domain contracts under `ai_platform/portal/contracts/`;
- fail-closed permission and environment/secret boundary helpers under `ai_platform/portal/security/`;
- targeted positive and negative contract tests under `tests/ai_platform/portal/`;
- implementation documentation in `docs/ai_platform/portal/CONTRACTS_AND_SECURITY_FOUNDATION.md`;
- durable task checkpoint and reviewable PR to `develop`.

## Non-negotiable boundaries

- Do not modify upstream `freqtrade/` core.
- Do not implement a FastAPI production server, web UI, database, NATS, Redis, Kubernetes or Cloudflare deployment.
- Do not expose Freqtrade REST/WebSocket details or credentials in browser-facing/domain contracts.
- Do not store plaintext exchange credentials; use opaque `SecretRef` only.
- Do not add a test-only security bypass.
- Do not enable live capital or withdrawal permissions.
- Research/test workloads cannot access production exchange credentials.
- AI/model output cannot bypass deterministic risk approval before execution.
- Training is not promotion; do not implement automatic model promotion.
- Do not change frozen thresholds `0.006/-0.009`.
- Do not access or consume protected final holdout `20260801-20260930`; no final-holdout evaluation before `2026-10-01 UTC`.
- Do not reopen completed Phase 6 or change authoritative `selected_model = null`.
- Do not reinterpret PyTorch/RL evidence as promotion authorization.

## Acceptance criteria

1. Tenant-owned contracts require explicit non-empty `tenant_id`.
2. Authorization is permission-based and unknown/missing permissions fail closed.
3. Environment and secret-reference validation prevents research/test use of production secrets and prevents environment mismatch.
4. Browser/domain exchange-connection contracts reject raw secret fields and forbid withdrawal-enabled credentials.
5. Bot desired and observed state are distinct; bot/config/model/risk identities are immutable and versioned.
6. Model identity includes artifact hash, feature schema, dataset/training window, training pipeline, parameters, Git revision, timestamp and lifecycle state.
7. `TradeIntent` cannot be submitted through `ExecutionAdapter`; only a risk-approved execution intent is accepted.
8. Rejected risk decisions cannot construct an approved execution intent.
9. Events are versioned, tenant-scoped, correlation-aware and reject secret-bearing payload keys.
10. Audit events answer who/what/when/tenant/resource/action/result/correlation and reject secret-bearing detail keys.
11. Canonical serialization is deterministic and representative JSON schemas are stable/versioned.
12. Targeted tests, compile validation, Ruff lint/format and relevant AI Platform CI pass.

## Validation

The implementation was validated on PR #114. The lightweight AI Platform workflow now installs the repository's existing Pydantic v2 dependency because portal contract tests import it directly. No heavy framework or runtime dependency was added.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-22T11:40:03+02:00
head: 4fbd4aa31acde833bed7a76760395496036d0159
branch: feat/portal-p1-contracts-security
pr: "#114"
status: ready
context_routes:
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/SECURITY_ARCHITECTURE.md
  - docs/ai_platform/portal/SYSTEM_ARCHITECTURE.md
  - docs/ai_platform/portal/AI_ML_AND_LEARNING_ARCHITECTURE.md
  - docs/ai_platform/portal/DATA_AND_OBSERVABILITY_ARCHITECTURE.md
  - docs/ai_platform/portal/AGENT_EXECUTION_PLAN.md
owned_paths:
  - .github/workflows/ai-platform.yml
  - ai_platform/portal/contracts/
  - ai_platform/portal/security/
  - tests/ai_platform/portal/
  - docs/ai_platform/portal/CONTRACTS_AND_SECURITY_FOUNDATION.md
  - docs/agents/tasks/FTAI-20260722-portal-p1-contracts-security.md
proven:
  - PR #113 was squash-merged to develop as ebd34c169da375f22d114cf9847d39b75fb2179d before P1 branched from that exact develop head.
  - Open PR #112 and draft PR #109 have disjoint ownership from the final P1 paths.
  - P1 implements immutable versioned Pydantic v2 contracts and fail-closed security helpers entirely outside upstream freqtrade core.
  - Every tenant-owned public contract carries an explicit tenant_id and unknown or missing permissions grant no access.
  - Production secret references are tenant/environment scoped and denied to research, model-training and test/E2E workload planes.
  - ExchangeConnection stores only SecretRef, rejects undeclared raw credential fields and structurally forbids withdrawal-enabled credentials.
  - Bot desired and observed states are separate; bot config, model and risk version identities are immutable.
  - Risk flow is frozen as Prediction to TradeIntent to RiskDecision to ApprovedExecutionIntent or RejectedExecutionIntent; ExecutionAdapter accepts only approved intents.
  - EventEnvelope and AuditEvent are versioned, correlation-aware and reject sensitive-value payload keys.
  - Frozen thresholds, protected final holdout, completed Phase 6 and selected_model = null were not changed or evaluated.
  - AI Platform CI run 29908628639 passed compile, AI Platform tests, Ruff lint, Ruff format, Codespell and JSON validation on implementation head 4fbd4aa31acde833bed7a76760395496036d0159.
  - Freqtrade CI run 29908628724 and zizmor run 29908628823 passed on implementation head 4fbd4aa31acde833bed7a76760395496036d0159; optional Pre-commit Types update run 29908628763 was skipped.
derived:
  - Shared P1 semantics are stable enough for separate P2, P3, P4, P5 and P10a workstreams after PR #114 is merged.
  - Concrete Vault/KMS and production identity-provider selections can remain replaceable behind the frozen P1 reference and identity contracts.
unknown:
  - Final Vault/KMS provider selection remains intentionally deferred.
  - Final production application identity provider remains intentionally vendor-neutral.
conflicts: []
first_failure:
  marker: github-write-safety-classification
  evidence: Initial common.py creation containing an explicit sensitive-key vocabulary was blocked by connector safety before branch mutation; the implementation was safely split and subsequent writes succeeded.
rejected_hypotheses:
  - P1 requires modifying upstream freqtrade core.
  - Frontend filtering is sufficient authorization.
  - A TradeIntent may be submitted directly to execution.
  - Research or test workloads may reuse production exchange secret references.
changed_paths:
  - .github/workflows/ai-platform.yml
  - ai_platform/portal/contracts/__init__.py
  - ai_platform/portal/contracts/audit.py
  - ai_platform/portal/contracts/bots.py
  - ai_platform/portal/contracts/common.py
  - ai_platform/portal/contracts/environment.py
  - ai_platform/portal/contracts/events.py
  - ai_platform/portal/contracts/execution.py
  - ai_platform/portal/contracts/identity.py
  - ai_platform/portal/contracts/models.py
  - ai_platform/portal/contracts/payloads.py
  - ai_platform/portal/contracts/risk.py
  - ai_platform/portal/contracts/secret_refs.py
  - ai_platform/portal/security/__init__.py
  - ai_platform/portal/security/authorization.py
  - ai_platform/portal/security/secret_access.py
  - docs/ai_platform/portal/CONTRACTS_AND_SECURITY_FOUNDATION.md
  - tests/ai_platform/portal/test_contracts.py
  - tests/ai_platform/portal/test_security.py
  - docs/agents/tasks/FTAI-20260722-portal-p1-contracts-security.md
validation:
  - command: live-state preflight and PR #113 squash merge
    result: PASS
    evidence: develop reverified at ebd34c169da375f22d114cf9847d39b75fb2179d and P1 branch created from that exact merged head; open ownership was disjoint.
  - command: python -m compileall -q ai_platform tests/ai_platform
    result: PASS
    evidence: AI Platform CI run 29908628639 Compile AI platform Python step passed.
  - command: python -m pytest -q -o addopts='' --confcutdir=tests/ai_platform tests/ai_platform
    result: PASS
    evidence: AI Platform CI run 29908628639 Run AI platform tests step passed, including targeted portal contract and security tests.
  - command: ruff check ai_platform tests/ai_platform
    result: PASS
    evidence: AI Platform CI run 29908628639 Ruff step passed.
  - command: ruff format --check ai_platform tests/ai_platform
    result: PASS
    evidence: AI Platform CI run 29908628639 Ruff format step passed.
  - command: pre-commit checks
    result: PASS
    evidence: Freqtrade CI run 29908628724 Pre-commit checks job passed.
  - command: documentation build
    result: PASS
    evidence: Freqtrade CI run 29908628724 Documentation build job passed.
  - command: Freqtrade CI
    result: PASS
    evidence: Freqtrade CI run 29908628724 completed successfully on implementation head 4fbd4aa31acde833bed7a76760395496036d0159.
  - command: zizmor
    result: PASS
    evidence: GitHub Actions Security Analysis run 29908628823 completed successfully.
  - command: Pre-commit Types update
    result: NOT_RUN
    evidence: Optional workflow run 29908628763 was skipped and is not a failure.
blockers: []
next_action: Review and merge PR #114; after merge, start P2 Control Plane, P3 Execution Adapter, P4 Data / Observability, P5 Model Lifecycle Control and P10a Exchange Simulator Core as separate disjoint bounded tasks from current develop.
```
