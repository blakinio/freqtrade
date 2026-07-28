---
task_id: FTAI-20260728-portal-bmw03-safe-feature-convergence
status: completed
branch: feat/portal-bmw03-safe-feature-convergence-v2
base_branch: develop
created: 2026-07-28
updated: 2026-07-28
owned_paths:
  - ai_platform/portal/exchange_connections/public_schema.py
  - ai_platform/portal/exchange_connections/router.py
  - ai_platform/portal/signal_control/public_schema.py
  - ai_platform/portal/signal_control/overview_service.py
  - ai_platform/portal/signal_control/repository.py
  - ai_platform/portal/signal_control/router.py
  - ai_platform/portal/grid_control/overview.py
  - ai_platform/portal/grid_control/router.py
  - ai_platform/portal/control_plane/bot_management.py
  - ai_platform/portal/control_plane/api.py
  - ai_platform/portal/web/lib/exchange-connections.ts
  - ai_platform/portal/web/lib/signal-control.ts
  - ai_platform/portal/web/lib/grid-control.ts
  - ai_platform/portal/web/app/platform/exchanges/page.tsx
  - ai_platform/portal/web/app/bots/signals/page.tsx
  - ai_platform/portal/web/app/bots/grid/page.tsx
  - ai_platform/portal/web/e2e/specs/bots/feature-convergence.spec.ts
  - ai_platform/portal/web/e2e/specs/platform/product-surfaces.spec.ts
  - tests/ai_platform/portal/exchange_connections/test_public_view.py
  - tests/ai_platform/portal/signal_control/test_public_overview.py
  - tests/ai_platform/portal/grid_control/test_overview.py
  - tests/ai_platform/portal/control_plane/test_api.py
  - docs/agents/tasks/FTAI-20260728-portal-bmw03-safe-feature-convergence.md
---

# BMW-03 safe signals, grid and exchange convergence

## Goal

Converge the three feature web surfaces on BM-04, BM-05 and BM-06 without exposing credential or authentication references and without accepting browser-supplied authoritative grid evidence.

## Delivered

- public exchange DTO excluding credential references, account labels and secret-store material;
- exchange page backed by BM-06 public metadata rather than reconstructed bot specs;
- signal overview excluding authentication references and webhook slugs;
- explicit unavailable authentication-provider state until PI-07;
- grid overview rejecting browser capability evidence and disabling preview/persistence until a trusted server provider exists;
- removal of legacy unsigned signal and browser-generated grid forms from the primary surfaces;
- critical secret-boundary and fail-closed E2E coverage.

## Safety boundary

BMW-03 performs no credential resolution, signature acceptance, grid runtime activation, exchange request, Freqtrade submission, order placement or live-capital action. PI-07 and PI-08 remain explicit prerequisites for provider activation and execution.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-28T20:24:00+02:00
branch: feat/portal-bmw03-safe-feature-convergence-v2
pr: 641
status: completed
base_head: 6270cb012ddf7366c07050d1faa97c05afbfd321
validated_head: f93387faf946f55f20006e258a56971bc4be0220
merge_commit: 9614217182a71fe5fa495b6552e50dabe9854a96
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/portal/BOT_MANAGEMENT_PRODUCT_ARCHITECTURE.md
  - docs/ai_platform/portal/BOT_MANAGEMENT_AGENT_PLAN.md
owned_paths:
  - ai_platform/portal/exchange_connections/public_schema.py
  - ai_platform/portal/exchange_connections/router.py
  - ai_platform/portal/signal_control/public_schema.py
  - ai_platform/portal/signal_control/overview_service.py
  - ai_platform/portal/signal_control/repository.py
  - ai_platform/portal/signal_control/router.py
  - ai_platform/portal/grid_control/overview.py
  - ai_platform/portal/grid_control/router.py
  - ai_platform/portal/control_plane/bot_management.py
  - ai_platform/portal/control_plane/api.py
  - ai_platform/portal/web/lib/exchange-connections.ts
  - ai_platform/portal/web/lib/signal-control.ts
  - ai_platform/portal/web/lib/grid-control.ts
  - ai_platform/portal/web/app/platform/exchanges/page.tsx
  - ai_platform/portal/web/app/bots/signals/page.tsx
  - ai_platform/portal/web/app/bots/grid/page.tsx
  - ai_platform/portal/web/e2e/specs/bots/feature-convergence.spec.ts
  - ai_platform/portal/web/e2e/specs/platform/product-surfaces.spec.ts
  - tests/ai_platform/portal/exchange_connections/test_public_view.py
  - tests/ai_platform/portal/signal_control/test_public_overview.py
  - tests/ai_platform/portal/grid_control/test_overview.py
  - tests/ai_platform/portal/control_plane/test_api.py
  - docs/agents/tasks/FTAI-20260728-portal-bmw03-safe-feature-convergence.md
proven:
  - BMW-01 merged through PR 625 as 81a45bbae0e7b63655ca5a684fb110c5a03fb4d5.
  - BMW-02 merged through PR 632 as 6270cb012ddf7366c07050d1faa97c05afbfd321.
  - BMW-03 merged through PR 641 as 9614217182a71fe5fa495b6552e50dabe9854a96.
  - Public exchange responses exclude credential_ref and account_label.
  - Public signal views exclude authentication references and webhook slugs.
  - Grid overview rejects browser-supplied authority and remains fail-closed without a trusted evidence provider.
  - Legacy unsigned signal and browser-generated grid mutations are absent from the primary web surfaces.
  - The merged diff contains no temporary diagnostic or integration workflow.
derived:
  - Safe feature convergence requires truthful unavailable states instead of fixture-like provider or execution success.
  - BM-08 should replace the web-composed dashboard snapshot with an authoritative server-side read model and explicit source availability/freshness.
unknown: []
conflicts: []
first_failure:
  marker: BROWSER_FEATURE_AUTHORITY_LEAK
  evidence: Exchange responses exposed credential_ref, signals used an unsigned legacy path and grid accepted browser-composed configuration evidence.
rejected_hypotheses:
  - Render opaque credential references or account labels in the browser.
  - Generate a webhook secret or verifier without PI-07.
  - Accept template/exchange capability evidence from the browser.
  - Claim grid preview, persistence or execution is enabled without a trusted provider.
changed_paths:
  - ai_platform/portal/control_plane/api.py
  - ai_platform/portal/control_plane/bot_management.py
  - ai_platform/portal/exchange_connections/public_schema.py
  - ai_platform/portal/exchange_connections/router.py
  - ai_platform/portal/grid_control/overview.py
  - ai_platform/portal/grid_control/router.py
  - ai_platform/portal/signal_control/overview_service.py
  - ai_platform/portal/signal_control/public_schema.py
  - ai_platform/portal/signal_control/repository.py
  - ai_platform/portal/signal_control/router.py
  - ai_platform/portal/web/lib/exchange-connections.ts
  - ai_platform/portal/web/lib/signal-control.ts
  - ai_platform/portal/web/lib/grid-control.ts
  - ai_platform/portal/web/app/platform/exchanges/page.tsx
  - ai_platform/portal/web/app/bots/signals/page.tsx
  - ai_platform/portal/web/app/bots/grid/page.tsx
  - ai_platform/portal/web/e2e/specs/bots/feature-convergence.spec.ts
  - ai_platform/portal/web/e2e/specs/platform/product-surfaces.spec.ts
  - tests/ai_platform/portal/control_plane/test_api.py
  - tests/ai_platform/portal/exchange_connections/test_public_view.py
  - tests/ai_platform/portal/grid_control/test_overview.py
  - tests/ai_platform/portal/signal_control/test_public_overview.py
  - docs/agents/tasks/FTAI-20260728-portal-bmw03-safe-feature-convergence.md
validation:
  - command: AI Platform CI run 30385988192
    result: PASS
  - command: Portal Web CI run 30385988261
    result: PASS
  - command: Portal Universal E2E run 30385988241
    result: PASS
  - command: Freqtrade CI run 30385988170
    result: PASS
  - command: GitHub Actions Security Analysis run 30385988318
    result: PASS
blockers: []
next_action: Start BM-08 from merge commit 9614217182a71fe5fa495b6552e50dabe9854a96 with a server-side dashboard read model; do not activate BM-07 execution before PI-08.
```
