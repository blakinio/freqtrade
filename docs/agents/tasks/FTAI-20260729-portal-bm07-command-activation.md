---
task_id: FTAI-20260729-portal-bm07-command-activation
status: ready
branch: feat/portal-bm07-command-activation
base_branch: develop
created: 2026-07-29
updated: 2026-07-29
related_pr: 672
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
updated_at: 2026-07-29T10:47:00+02:00
head: 0663046ef773e802c6a78fe71ee21a169089c609
merged_commit: ef0550744104f4c82ef3f106181f14442f9b82af
branch: feat/portal-bm07-command-activation
pr: 672
status: ready
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/portal/BOT_MANAGEMENT_AGENT_PLAN.md
  - docs/ai_platform/portal/BOT_MANAGEMENT_PRODUCT_ARCHITECTURE.md
  - docs/ai_platform/portal/PI08_PRIVATE_DRY_RUN_SUBMISSION.md
  - docs/ai_platform/portal/BM07_COMMAND_ACTIVATION.md
owned_paths:
  - ai_platform/portal/bot_operations/activation_*.py
  - ai_platform/portal/bot_operations/__init__.py
  - tests/ai_platform/portal/bot_operations/test_bm07_*.py
  - docs/ai_platform/portal/BM07_COMMAND_ACTIVATION.md
  - docs/agents/tasks/FTAI-20260729-portal-bm07-command-activation.md
proven:
  - Exact-head AI Platform CI 30435644106 passed.
  - Exact-head Freqtrade CI 30435640985 passed, including pre-commit, documentation and Python 3.11 through 3.14.
  - Exact-head workflow security run 30435637949 passed.
  - PR 672 squash merged as ef0550744104f4c82ef3f106181f14442f9b82af.
  - BM-07 reserves command evidence before private I/O and exact replay does not repeat mutation.
  - Exposure-increasing DCA, grid and replacement paths delegate to PI-08.
derived:
  - BM-09 may now use the merged BM-07 contract as its final command-activation dependency.
unknown:
  - Real Synology, Vault and Freqtrade target acceptance remains owner-managed deployment evidence.
conflicts: []
first_failure:
  marker: resolved_ruff_format
  evidence: exact Ruff 0.15.21 output was applied before final exact-head CI passed
rejected_hypotheses:
  - Do not treat runtime acknowledgement as authoritative execution proof.
  - Do not expose private Freqtrade command routes to browser clients.
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
  - command: AI Platform CI 30435644106
    result: PASS
    evidence: exact head 0663046ef773e802c6a78fe71ee21a169089c609 completed successfully
  - command: Freqtrade CI 30435640985
    result: PASS
    evidence: exact head completed successfully across required jobs
  - command: GitHub Actions security analysis 30435637949
    result: PASS
    evidence: exact head completed successfully
blockers: []
next_action: Use merged commit ef0550744104f4c82ef3f106181f14442f9b82af as the BM-09 dependency and preserve P11 and P14 as separate owner-governed gates.
```
