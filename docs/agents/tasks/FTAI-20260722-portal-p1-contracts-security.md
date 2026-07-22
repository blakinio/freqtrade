---
task_id: FTAI-20260722-portal-p1-contracts-security
status: active
branch: feat/portal-p1-contracts-security
base_branch: develop
created: 2026-07-22
updated: 2026-07-22
related_pr: null
owned_paths:
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

Run the narrowest portal contract tests first, then compile/syntax validation, Ruff lint, Ruff format check, relevant AI Platform tests and repository pre-commit where required by scope. After push, verify AI Platform CI, Freqtrade CI, zizmor, documentation build and CI Gate; skipped optional jobs are not failures.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-22T10:30:00+02:00
head: ebd34c169da375f22d114cf9847d39b75fb2179d
branch: feat/portal-p1-contracts-security
pr: null
status: active
context_routes:
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/SECURITY_ARCHITECTURE.md
  - docs/ai_platform/portal/SYSTEM_ARCHITECTURE.md
  - docs/ai_platform/portal/AI_ML_AND_LEARNING_ARCHITECTURE.md
  - docs/ai_platform/portal/DATA_AND_OBSERVABILITY_ARCHITECTURE.md
  - docs/ai_platform/portal/AGENT_EXECUTION_PLAN.md
owned_paths:
  - ai_platform/portal/contracts/
  - ai_platform/portal/security/
  - tests/ai_platform/portal/
  - docs/ai_platform/portal/CONTRACTS_AND_SECURITY_FOUNDATION.md
  - docs/agents/tasks/FTAI-20260722-portal-p1-contracts-security.md
proven:
  - PR #113 was squash-merged to develop as ebd34c169da375f22d114cf9847d39b75fb2179d after AI Platform CI, Freqtrade CI and zizmor succeeded; its durable checkpoint also records documentation build and CI Gate success.
  - Current P1 branch was created directly from merged develop head ebd34c169da375f22d114cf9847d39b75fb2179d.
  - Open PR #112 owns TradingView futures research/preflight paths and does not overlap P1 portal contract/security paths.
  - Open draft PR #109 owns only docs/ai_platform/design_references/wickhunter-profile/ and does not overlap P1.
  - Repository dependencies already include Pydantic v2, so no new heavy framework is required.
  - Portal architecture requires tenant boundaries, private Freqtrade, deterministic risk gating, immutable version identities, opaque secret references, versioned events, audit and correlation propagation.
derived:
  - P1 can be implemented entirely under project-specific ai_platform/portal and targeted tests without modifying upstream freqtrade core.
  - Freezing shared contracts before P2/P3/P4/P5/P10a prevents parallel workstreams from independently redefining common semantics.
unknown:
  - Exact final Vault/KMS provider remains intentionally deferred behind SecretRef.
  - Final production identity provider remains intentionally vendor-neutral.
conflicts: []
first_failure:
  marker: none
  evidence: Live-state preflight completed without a blocking merge, ownership or CI conflict.
changed_paths:
  - docs/agents/tasks/FTAI-20260722-portal-p1-contracts-security.md
validation:
  - command: live-state preflight
    result: PASS
    evidence: PR #113 merged safely; develop reverified; branch created from merged head; open PR ownership is disjoint.
blockers: []
next_action: Implement immutable Pydantic portal contracts and fail-closed security helpers in the declared owned paths, then add targeted negative tests before broader validation.
```
