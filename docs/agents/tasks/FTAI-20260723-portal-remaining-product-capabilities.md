---
task_id: FTAI-20260723-portal-remaining-product-capabilities
status: active
branch: feat/portal-remaining-product-capabilities-20260723
base_branch: develop
created: 2026-07-23
updated: 2026-07-23
related_pr: null
owned_paths:
  - ai_platform/portal/control_plane/
  - ai_platform/portal/operations/
  - ai_platform/portal/web/
  - ai_platform/portal/contracts/
  - ai_platform/portal/notifications/
  - ai_platform/portal/signals/
  - ai_platform/portal/strategies/
  - ai_platform/portal/identity/
  - ai_platform/portal/admin/
  - ai_platform/portal/observability/
  - tests/ai_platform/portal/
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
  - docs/agents/tasks/FTAI-20260723-portal-remaining-product-capabilities.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
  - docs/ai_platform/portal/UI_INFORMATION_ARCHITECTURE.md
  - docs/ai_platform/portal/SYSTEM_ARCHITECTURE.md
---

# AI Trading Portal — Remaining Product Capabilities

## Goal

Close the remaining software-addressable portal product gaps after PRs #227 and #229 by replacing shells/read-model gaps with bounded authoritative services and UI integrations while preserving private Freqtrade, deterministic risk, dry-run and research safety boundaries.

## In scope

- Signal Wizard submission contract and tenant-scoped signal event history.
- Signal Logs read model and UI integration.
- Strategy Catalog read model and UI integration.
- Grid Bot configuration as a dry-run strategy template only; no live-capital authority.
- Notification preferences and durable in-app notification read model.
- Profile/security self-service read model for the authenticated portal identity; no credential secret exposure.
- Permission-gated administration read model for tenant membership/roles using existing authorization contracts where available.
- Model Health drift-status read model derived only from authoritative persisted evidence available in-repository.
- Bounded runtime/execution log evidence where authoritative events already exist; do not fabricate raw stdout/stderr.
- Unrealized performance only if it can be derived from authoritative operational position evidence without introducing market-price fabrication.
- Browser/API tests and delivery-status documentation.

## Explicitly out of scope

- Real Cloudflare/protected GitHub P11 infrastructure provisioning or claiming P11 acceptance.
- Live-capital enablement, withdrawals, production exchange credentials or direct browser-to-Freqtrade access.
- Implementing real order submission merely to make UI appear complete.
- Weakening deliberately fail-closed private execution adapter boundaries without a separately reviewed runtime-integration contract.
- Protected final-holdout access, Phase 6 changes, frozen-threshold changes or model auto-promotion.
- Fabricating drift, PNL, signal, runtime-log, security or admin records when no authoritative source exists.

## Acceptance criteria

1. Every formerly shell/read-model-gap product surface in `UI_DELIVERY_STATUS.md` has either an authoritative bounded implementation or a documented hard external/safety blocker.
2. Signal Wizard persists attributable tenant-scoped signal evidence and Signal Logs reads the same source.
3. Strategy Catalog exposes immutable strategy metadata and Grid Bots remain dry-run configuration templates unless separately promoted.
4. Notifications, profile/security and administration are permission/tenant scoped and expose no secrets.
5. Model health never invents drift evidence; unavailable telemetry is explicit.
6. Raw runtime stdout/stderr is not fabricated; any integrated execution activity is accurately named and sourced.
7. No direct public Freqtrade/exchange path and no live-capital authority are introduced.
8. Targeted Python/web/browser tests and required repository CI pass before merge.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-23T23:40:00+02:00
head: pending-first-task-commit
branch: feat/portal-remaining-product-capabilities-20260723
pr: null
status: active
context_routes:
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
  - docs/ai_platform/portal/UI_INFORMATION_ARCHITECTURE.md
proven:
  - PR #227 completed the broad portal UI/navigation foundation and trusted P8/P9 read-only integrations.
  - PR #229 added bounded operational read models for orders, positions, trades, realized performance, risk events, audit events and execution activity.
  - Remaining documented gaps include signals, strategy catalog/grid implementation, notifications, profile/security, administration, model drift telemetry and raw runtime/signal logs.
  - Freqtrade execution/query boundaries remain private and deliberately fail-closed where not separately implemented.
derived:
  - Remaining work must be split by authoritative data ownership rather than solved with fixture data in API mode.
unknown:
  - Exact current reusable identity/admin/strategy/signal contracts available on develop; inspect before implementation.
conflicts: []
first_failure:
  marker: none-yet
  evidence: Task declared after live preflight; no implementation validation has run yet.
changed_paths:
  - docs/agents/tasks/FTAI-20260723-portal-remaining-product-capabilities.md
validation: []
blockers: []
next_action: Inspect current develop contracts and route implementations for signals, strategies, identity, authorization, notifications and model-health evidence, then implement the smallest authoritative services without weakening execution or staging boundaries.
```
