---
task_id: FTAI-20260728-liquidation-okx-shadow-acceptance-freqtrade-staging-mapping-v1
status: implementation-complete-ci-pending
branch: fix/okx-shadow-acceptance-freqtrade-staging-mapping-20260728
base_branch: develop
created: 2026-07-28
updated: 2026-07-28
owned_paths:
  - .github/workflows/ai-platform-okx-liquidation-shadow-acceptance.yml
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE_EXECUTION.md
  - tests/ai_platform_integration/test_liquidation_okx_shadow_acceptance_workflow_mapping.py
  - docs/agents/tasks/FTAI-20260728-liquidation-okx-shadow-acceptance-freqtrade-staging-mapping-v1.md
required_reads:
  - AGENTS.md
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE_EXECUTION.md
  - docs/agents/tasks/FTAI-20260727-liquidation-okx-shadow-acceptance-staging-preflight-v1.md
---

# OKX shadow acceptance Freqtrade staging mapping

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-28T10:05:00+02:00
status: implementation-complete-ci-pending
branch: fix/okx-shadow-acceptance-freqtrade-staging-mapping-20260728
base_develop: 59b62adad7b21d4e1c1114a118ce192eae6a7eea
proven:
  - Preflight workflow run 30308573877 completed successfully.
  - The exact runner name is freqtrade-synology-staging.
  - The routing label is freqtrade-staging.
  - The protected GitHub environment is synology-staging.
  - The canonical state directory is /var/lib/freqtrade-staging-state.
  - The durable acceptance root is /var/lib/freqtrade-staging-state/okx-liquidation-acceptance.
  - The credential-free durable URI is file:///var/lib/freqtrade-staging-state/okx-liquidation-acceptance.
  - Exact-one-file scope, credential refusal, atomic durable I/O and public OKX endpoint checks passed.
changes:
  - Route the 24-hour workflow to freqtrade-staging.
  - Bind the workflow to synology-staging and the verified canonical durable path.
  - Verify the actual runner name and Linux OS before collection.
  - Remove the obsolete mutable OKX_ACCEPTANCE_* variable dependency.
  - Add static regression coverage for the final mapping.
safety:
  - No canonical 24-hour request is present in this branch.
  - No WebSocket subscription or liquidation collection is executed by this branch.
  - No Liquid20 membership, replay, model training, strategy work, orders or live capital are authorized.
validation:
  - AI Platform CI passed on the initial implementation head.
  - Zizmor passed on the initial implementation head.
  - A temporary diagnostic proved the only initial pre-commit failure was ruff-format; mypy, schema extraction, codespell and all remaining hooks passed.
  - The exact ruff-format diff was applied and the diagnostic workflow was removed.
  - Fresh exact-head AI Platform CI, Freqtrade CI and zizmor are pending on the reconciled develop base.
next_action: Complete exact-head CI, guarded merge, then create a separate exact-one-file operational trigger and close it without merge after terminal evidence.
```
