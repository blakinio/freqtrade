---
task_id: FTAI-20260723-portal-remaining-product-capabilities
status: done
branch: feat/portal-remaining-product-capabilities-20260723
base_branch: develop
created: 2026-07-23
updated: 2026-07-24
related_pr: "#232"
owned_paths:
  - ai_platform/portal/control_plane/api.py
  - ai_platform/portal/control_plane/database.py
  - ai_platform/portal/product/
  - ai_platform/portal/web/
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
- Permission-gated administration read model using existing authorization contracts where available.
- Model Health status derived only from authoritative persisted evidence available in-repository; unavailable drift telemetry remains explicit.
- Bounded runtime/execution log evidence where authoritative events already exist; do not fabricate raw stdout/stderr.
- Unrealized performance only if it can be derived from authoritative operational position/valuation evidence without introducing market-price fabrication.
- Browser/API tests and delivery-status documentation.

## Explicitly out of scope

- Real Cloudflare/protected GitHub P11 infrastructure provisioning or claiming P11 acceptance.
- Live-capital enablement, withdrawals, production exchange credentials or direct browser-to-Freqtrade access.
- Implementing real order submission merely to make UI appear complete.
- Weakening deliberately fail-closed private execution adapter boundaries without a separately reviewed runtime-integration contract.
- Protected final-holdout access, Phase 6 changes, frozen-threshold changes or model auto-promotion.
- Fabricating drift, unrealized PNL, runtime logs, identity lifecycle or external delivery evidence when no authoritative source exists.

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
updated_at: 2026-07-24T00:37:00+02:00
head: e3d0fbf48632a449ce5b1e3aad1de46d95dad43b
branch: feat/portal-remaining-product-capabilities-20260723
pr: "#232"
status: ready
context_routes:
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
  - docs/ai_platform/portal/UI_INFORMATION_ARCHITECTURE.md
proven:
  - PR #227 completed the broad portal UI/navigation foundation and trusted P8/P9 read-only integrations.
  - PR #229 added bounded operational read models for orders, positions, trades, realized performance, risk events, audit events and execution activity.
  - This task added tenant-scoped advisory SignalEvent persistence shared by Signal Wizard and Signal Logs; SignalEvent cannot grant execution authority.
  - This task added immutable Strategy Catalog metadata and persisted Grid Bot configuration constrained to dry_run and grid-dry-run-v1.
  - This task added actor-scoped notification preferences and in-app notification views derived from canonical signal, risk-decision and own execution-audit evidence.
  - This task added trusted Profile and Security context plus ADMIN_MANAGE-gated built-in RBAC overview without exposing credential or exchange secrets.
  - Model Health now exposes canonical immutable model metadata while drift telemetry truthfully remains UNAVAILABLE until a canonical telemetry source exists.
  - Execution Activity now exposes an explicit raw-runtime-log availability contract; centralized stdout/stderr remains unavailable rather than fabricated.
  - Browser mutations use same-origin BFF routes; browser code has no direct Freqtrade, exchange or secret-store path.
  - Direct Freqtrade order submission and private order/position/trade query paths remain deliberately fail-closed.
  - AI Platform CI run 30050408641 passed compile, tests, Ruff, Ruff format, Codespell and schema validations on the implementation head.
  - zizmor run 30050408648 passed on the implementation head.
  - deterministic Universal E2E backend scenario passed on run 30050408646.
  - temporary diagnostic Chromium validation on run 30050408701 passed all 12 portal browser journeys after locator fixes.
derived:
  - Remaining partial product states are hard external/private-integration dependencies, not hidden UI shells: canonical drift telemetry, centralized raw runtime logs, authoritative unrealized valuation, reviewed private Freqtrade runtime queries, external notification delivery and external-IdP MFA/session/membership lifecycle.
  - Real P11 External E2E remains a separate blocked infrastructure gate and this task provides no evidence that it passed.
unknown: []
conflicts: []
first_failure:
  marker: lint-and-browser-acceptance-fixes
  evidence: Initial validation found Ruff route/notification complexity, an ESLint server-component catch/render issue and two ambiguous Playwright locators; implementation was refactored and the latest diagnostic browser suite passed 12 of 12.
changed_paths:
  - ai_platform/portal/control_plane/api.py
  - ai_platform/portal/control_plane/database.py
  - ai_platform/portal/product/
  - ai_platform/portal/web/
  - tests/ai_platform/portal/
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
  - docs/agents/tasks/FTAI-20260723-portal-remaining-product-capabilities.md
validation:
  - command: AI Platform CI 30050408641
    result: PASS
  - command: zizmor 30050408648
    result: PASS
  - command: Portal Universal E2E backend scenario 30050408646
    result: PASS
  - command: temporary Chromium diagnostic 30050408701
    result: PASS 12/12
blockers: []
next_action: Remove the temporary diagnostic workflow, require the standard repository CI suite to pass on the final cleanup head, then merge PR #232. Resume remaining hard external/private integrations only as separately authorized bounded tasks; do not claim P11 or enable live capital.
```
