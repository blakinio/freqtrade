---
task_id: FTAI-20260722-portal-p7-risk-terminal
status: active
branch: feat/portal-p7-risk-core
base_branch: develop
created: 2026-07-22
updated: 2026-07-22
related_pr: null
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

## P7.1 acceptance criteria

1. Cross-tenant policy, kill-switch, intent and decision access is denied or undisclosed.
2. Duplicate policy identity cannot overwrite prior immutable limits.
3. Manual intent requires `trade.manual_execute`; policy/kill-switch mutation requires `risk.manage`.
4. Risk evaluation produces stable machine-readable reason codes and non-empty evaluated-limit evidence.
5. Active kill switch always rejects approval regardless of other passing limits.
6. Order notional, projected exposure, projected open positions, daily loss, drawdown and runtime health gates fail closed.
7. Approved output can only be constructed from an approved canonical `RiskDecision`; rejected output remains non-executable.
8. Intent + decision + audit + outbox evidence commit atomically; outbox failure rolls back domain writes.
9. P7.1 does not call or modify P3 `submit_approved_intent`.
10. Targeted tests and required repository CI pass before merge.

## Validation

- focused risk-core tests first;
- AI Platform CI;
- Freqtrade CI/pre-commit;
- zizmor/security analysis.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-22T22:10:00+02:00
head: 88199e235972f25fd7becb3cc6a72357bc497bb9
branch: feat/portal-p7-risk-core
pr: null
status: active
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
  - Canonical architecture requires deterministic risk approval before execution and identifies exposure/loss/drawdown/health gates plus emergency kill switch.
derived:
  - P7.1 can implement the full deterministic approval authority without changing shared P1 contracts or pretending order submission is available.
  - P7.2 must treat current production execution submission as fail-closed until a separately coordinated P3 execution slice implements it.
unknown: []
conflicts: []
first_failure:
  marker: none
  evidence: No P7.1 executable validation has run yet.
changed_paths:
  - docs/agents/tasks/FTAI-20260722-portal-p7-risk-terminal.md
validation: []
blockers: []
next_action: Implement immutable risk-policy persistence, kill-switch state and deterministic TradeIntent evaluation under ai_platform/portal/risk/ without modifying shared contracts or execution paths.
```
