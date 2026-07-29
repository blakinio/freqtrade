---
task_id: FTAI-20260729-portal-bm07-command-activation
status: implementing
branch: feat/portal-bm07-command-activation
base_branch: develop
created: 2026-07-29
updated: 2026-07-29
related_pr: null
depends_on:
  - FTAI-20260727-portal-bm03-bot-command-persistence
  - FTAI-20260728-portal-pi07-vault-credential-broker
  - FTAI-20260728-portal-pi08-private-dry-run-submission
owned_paths:
  - ai_platform/portal/bot_operations/activation_*.py
  - ai_platform/portal/bot_operations/__init__.py
  - tests/ai_platform/portal/bot_operations/test_bm07_*.py
  - docs/ai_platform/portal/BM07_COMMAND_ACTIVATION.md
  - docs/agents/tasks/FTAI-20260729-portal-bm07-command-activation.md
---

# BM-07 command activation

## Goal

Activate authorized position, order, DCA and grid commands against private Freqtrade dry-run runtimes while preserving BM-03 durability, PI-07 credential isolation, PI-08 risk approval for exposure increases and PI-01 authoritative reconciliation.

## Acceptance criteria

1. BM-03 capability, tenant, actor, environment, immutable revision, runtime freshness and kill-switch decisions remain authoritative.
2. A deterministic pending-reconciliation attempt is persisted before any private runtime mutation.
3. Exact replay cannot repeat a runtime mutation; conflicting idempotency remains rejected by BM-03.
4. Close, partial close, close-all, forced take-profit, cancel and cancel-all map only to bounded private Freqtrade dry-run operations.
5. Position/order evidence is exact-revision and exact-tenant/bot/runtime scoped.
6. DCA, grid and exposure-increasing replacement delegate to risk-approved PI-08 rather than bypassing risk.
7. PI-07 credentials remain bounded, runtime-scoped, withdrawal-disabled and cleared after use.
8. Acknowledgements never prove execution; ambiguity remains pending until authoritative reconciliation.
9. Price-changing replacement is rejected where no native atomic runtime operation exists.
10. No browser, public endpoint, live capital, production credential or withdrawal authority is added.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-29T09:42:00+02:00
validated_code_head: null
merged_commit: null
branch: feat/portal-bm07-command-activation
pr: null
status: implementing
base_head: 530f61caf9d5d4644068a93baa0b7a09298f24c6
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/portal/BOT_MANAGEMENT_AGENT_PLAN.md
  - docs/ai_platform/portal/BOT_MANAGEMENT_PRODUCT_ARCHITECTURE.md
  - docs/ai_platform/portal/PI08_PRIVATE_DRY_RUN_SUBMISSION.md
  - docs/ai_platform/portal/BM07_COMMAND_ACTIVATION.md
proven:
  - PI-08 repository implementation is merged and all exact-head CI gates passed.
  - BM-03 supports durable accepted and pending-reconciliation command history with exact replay.
  - Freqtrade exposes bounded private force-exit and open-order cancellation operations.
  - BM-07 reserves a deterministic command attempt before private I/O and replays pending state without repeating I/O.
  - Exposure-increasing DCA, grid and replacement paths delegate to PI-08.
derived:
  - Repository-side BM-07 can complete without weakening default fail-closed behavior or authorizing target deployment.
unknown:
  - Real Synology/Vault/Freqtrade target acceptance remains owner-managed deployment evidence.
conflicts: []
first_failure: null
changed_paths:
  - ai_platform/portal/bot_operations/activation_errors.py
  - ai_platform/portal/bot_operations/activation_schema.py
  - ai_platform/portal/bot_operations/activation_service.py
  - ai_platform/portal/bot_operations/activation_transport.py
  - ai_platform/portal/bot_operations/__init__.py
  - tests/ai_platform/portal/bot_operations/test_bm07_command_activation.py
  - tests/ai_platform/portal/bot_operations/test_bm07_activation_transport.py
  - docs/ai_platform/portal/BM07_COMMAND_ACTIVATION.md
  - docs/agents/tasks/FTAI-20260729-portal-bm07-command-activation.md
validation:
  - command: focused BM-07 tests
    result: PENDING
  - command: AI Platform CI
    result: PENDING
  - command: Freqtrade CI
    result: PENDING
  - command: GitHub Actions security analysis
    result: PENDING
blockers: []
next_action: Open the BM-07 pull request, inspect exact-head CI, fix all deterministic failures, then squash merge before starting BM-09.
```
