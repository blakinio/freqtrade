---
task_id: FTAI-20260722-portal-p7-risk-terminal
status: active
branch: feat/portal-p7-risk-core
base_branch: develop
created: 2026-07-22
updated: 2026-07-22
related_pr: "#137"
owned_paths:
  - ai_platform/portal/risk/
  - tests/ai_platform/portal/risk/
  - docs/ai_platform/portal/RISK_ENGINE_FOUNDATION.md
  - docs/agents/tasks/FTAI-20260722-portal-p7-risk-terminal.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/DELIVERY_ROADMAP.md
  - docs/ai_platform/portal/AGENT_EXECUTION_PLAN.md
  - docs/ai_platform/portal/SYSTEM_ARCHITECTURE.md
  - docs/ai_platform/portal/SECURITY_ARCHITECTURE.md
  - ai_platform/portal/contracts/risk.py
  - ai_platform/portal/contracts/identity.py
  - ai_platform/portal/contracts/audit.py
  - ai_platform/portal/contracts/events.py
  - ai_platform/portal/execution/adapter.py
search_first:
  - current develop and open PRs or active tasks overlapping risk/terminal ownership
  - canonical P1 risk, permission, audit and event contracts
  - P2 transactional audit/outbox patterns
  - P3 ApprovedExecutionIntent boundary and current order-submission support
optional_reads:
  - terminal web/control-plane composition only after P7.1 risk core merges
---

# AI Trading Portal P7 — Risk Engine and Trading Terminal

## Goal

Introduce deterministic risk gating so manual/AI trade intent cannot become execution authority without an attributable `RiskDecision`, then expose that gate through an audited terminal surface without creating any browser-to-runtime bypass.

## Delivery slices

### P7.1 — deterministic risk core

Implemented in PR #137:

- immutable tenant-scoped risk policy definitions anchored to canonical `RiskPolicyVersion` identity;
- deterministic limit evaluation for order notional, projected gross exposure, projected open positions, daily loss, drawdown and runtime health;
- tenant/environment kill switch;
- canonical `TradeIntent` -> `RiskDecision` -> `ApprovedExecutionIntent`/`RejectedExecutionIntent` flow;
- transactional intent/decision persistence with canonical audit/outbox evidence;
- no execution submission implementation and no changes to `execution/**`.

### P7.2 — terminal API/UI integration

Starts only after P7.1 merges and revalidates live repository state. It may coordinate narrowly owned FastAPI composition and terminal web slices, but still must submit only `ApprovedExecutionIntent` to the existing execution boundary and must fail closed while P3 order submission remains unsupported.

## Non-negotiable boundaries

- No browser or risk module calls Freqtrade/exchanges directly.
- `TradeIntent` never authorizes execution by itself.
- Rejected intent cannot reach an execution submit boundary.
- Kill switch blocks new approval authority for its tenant/environment.
- Policy definitions are immutable; changed limits require a new risk-policy version.
- P7.1 does not modify P1 contracts, P2 control-plane paths, P3 execution paths or P6 web paths.
- No live capital is enabled.
- Frozen thresholds, completed research Phase 6, protected final holdout and PyTorch/RL evidence remain unchanged.

## P7.1 acceptance result

All P7.1 acceptance criteria are satisfied on the validated PR #137 implementation head.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-22T22:30:00+02:00
head: a290fdf60e59a2139e04598e8594c410e8f7d862
branch: feat/portal-p7-risk-core
pr: "#137"
status: ready_to_merge
context_routes:
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/DELIVERY_ROADMAP.md
  - docs/ai_platform/portal/AGENT_EXECUTION_PLAN.md
  - docs/ai_platform/portal/SYSTEM_ARCHITECTURE.md
owned_paths:
  - ai_platform/portal/risk/
  - tests/ai_platform/portal/risk/
  - docs/ai_platform/portal/RISK_ENGINE_FOUNDATION.md
  - docs/agents/tasks/FTAI-20260722-portal-p7-risk-terminal.md
proven:
  - P6 task is durably closed on develop after PR #136 merged as 88199e235972f25fd7becb3cc6a72357bc497bb9.
  - No open PR or existing task record matching P7 risk terminal ownership was found in preflight.
  - P1 already defines RiskPolicyVersion, TradeIntent, RiskDecision, ApprovedExecutionIntent and RejectedExecutionIntent.
  - P1 permissions already define trade.manual_execute and risk.manage; audit vocabulary includes trade.manual_intent, risk_policy.changed and kill-switch activate/release.
  - Event vocabulary already defines trade_intent.created, risk.approved and risk.rejected.
  - P3 exposes submit_approved_intent(ApprovedExecutionIntent) but current Freqtrade adapter intentionally raises ORDER_SUBMISSION_NOT_IMPLEMENTED.
  - P7.1 persists immutable tenant-scoped risk-policy definitions, tenant/environment kill-switch state, canonical TradeIntent and canonical RiskDecision records without modifying shared P1 contracts.
  - Deterministic evaluation order is kill switch, order notional, projected gross exposure, projected open positions, daily loss, drawdown and runtime health.
  - Stable rejection reason codes are KILL_SWITCH_ACTIVE, ORDER_NOTIONAL_LIMIT_EXCEEDED, GROSS_EXPOSURE_LIMIT_EXCEEDED, OPEN_POSITION_LIMIT_EXCEEDED, DAILY_LOSS_LIMIT_EXCEEDED, DRAWDOWN_LIMIT_EXCEEDED and RUNTIME_UNHEALTHY; fully passing evaluation uses RISK_APPROVED.
  - Manual intent evaluation requires trade.manual_execute; policy and kill-switch operations require risk.manage.
  - TradeIntent, RiskDecision, manual-trade audit evidence and trade_intent.created plus risk.approved/risk.rejected outbox events are committed in one transaction; outbox failure rolls back domain writes.
  - P7.1 contains no execution-adapter import or order-submission call and does not modify execution, control-plane, web or shared-contract paths.
  - Targeted tests cover immutable policy identity, tenant isolation/undisclosed decision access, permissions, approval, each deterministic limit, kill switch activation/release, transactional rollback and migration structure.
  - First executable AI Platform validation showed tests and Ruff passing with only Ruff format failing; an exact temporary formatter workflow applied canonical formatting and was deleted from the final diff.
  - Full pre-commit diagnostic later isolated exactly two mypy errors because RiskEvaluationResult was not declared as TypeAlias; annotating the union as TypeAlias resolved pre-commit and the temporary diagnostic/bootstrap workflow was deleted.
  - PR #137 implementation head a290fdf60e59a2139e04598e8594c410e8f7d862 passed AI Platform CI 29954843381, Freqtrade CI 29954843399 and zizmor 29954843446; Pre-commit Types update 29954843217 was skipped and is not a failure gate.
derived:
  - P7.1 establishes deterministic approval authority without pretending that production order submission exists.
  - P7.2 must construct RiskEvaluationSnapshot server-side from trusted state rather than accepting exposure/loss/drawdown/runtime-health facts from browser input.
  - P7.2 must resolve the bot's immutable pinned risk-policy version server-side before invoking P7.1.
  - P7.2 must remain fail-closed when an approved intent reaches the current P3 order-submission boundary because ORDER_SUBMISSION_NOT_IMPLEMENTED remains authoritative.
unknown: []
conflicts: []
first_failure:
  marker: ruff-format
  evidence: Initial PR #137 AI Platform CI passed compile, tests and Ruff but failed only Ruff format; canonical formatting resolved it.
subsequent_failure:
  marker: mypy-type-alias
  evidence: Full pre-commit diagnostic showed only two mypy errors for RiskEvaluationResult used as a type; explicit TypeAlias fixed both and all pre-commit hooks then passed.
rejected_hypotheses:
  - Modify P1 risk contracts to implement P7.1.
  - Call FreqtradeExecutionAdapter or submit an order from the risk core.
  - Accept browser-supplied risk snapshot facts as authoritative terminal inputs.
  - Keep temporary formatter or pre-commit diagnostic workflows in the final diff.
changed_paths:
  - ai_platform/portal/risk/__init__.py
  - ai_platform/portal/risk/database.py
  - ai_platform/portal/risk/migrations/0001_risk_core.sql
  - ai_platform/portal/risk/models.py
  - ai_platform/portal/risk/repository.py
  - ai_platform/portal/risk/schema.py
  - ai_platform/portal/risk/service.py
  - tests/ai_platform/portal/risk/test_risk_core_migration.py
  - tests/ai_platform/portal/risk/test_risk_core_service.py
  - docs/ai_platform/portal/RISK_ENGINE_FOUNDATION.md
  - docs/agents/tasks/FTAI-20260722-portal-p7-risk-terminal.md
validation:
  - command: AI Platform CI 29954843381
    result: PASS
    evidence: compile, AI Platform tests, Ruff, Ruff format, Codespell and JSON validation passed.
  - command: Freqtrade CI 29954843399
    result: PASS
    evidence: CI scope, pre-commit, documentation and full required core matrix passed after the TypeAlias fix.
  - command: GitHub Actions Security Analysis with zizmor 29954843446
    result: PASS
  - command: P7.1 implementation scope verification
    result: PASS
    evidence: final implementation diff is limited to the 11 declared P7.1 risk/test/docs/task files; temporary diagnostic workflows were deleted.
blockers: []
next_action: Verify required CI and review/base state on this checkpoint-only PR #137 head, then squash-merge P7.1 if green and revalidate develop before starting the P7.2 terminal integration slice.
```
