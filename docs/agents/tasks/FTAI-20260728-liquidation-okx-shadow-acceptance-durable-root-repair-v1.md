---
task_id: FTAI-20260728-liquidation-okx-shadow-acceptance-durable-root-repair-v1
status: implementation-complete-ci-pending
branch: fix/okx-shadow-acceptance-durable-root-preparation-20260728
base_branch: develop
created: 2026-07-28
updated: 2026-07-28
owned_paths:
  - .github/workflows/ai-platform-okx-liquidation-shadow-acceptance.yml
  - tests/ai_platform_integration/test_liquidation_okx_shadow_acceptance_workflow_mapping.py
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE_EXECUTION.md
  - docs/agents/tasks/FTAI-20260728-liquidation-okx-shadow-acceptance-durable-root-repair-v1.md
required_reads:
  - AGENTS.md
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE_EXECUTION.md
  - docs/agents/tasks/FTAI-20260728-liquidation-okx-shadow-acceptance-freqtrade-staging-mapping-v1.md
---

# OKX shadow acceptance durable-root repair

```yaml
checkpoint_version: 1
updated_at: 2026-07-28T13:05:00+02:00
status: implementation-complete-ci-pending
branch: fix/okx-shadow-acceptance-durable-root-preparation-20260728
base_develop: c0fba2ddf90d145211ca42fdea61ffbfe73d7185
proven:
  - Mapping PR 577 merged as c0fba2ddf90d145211ca42fdea61ffbfe73d7185 after exact-head CI and guarded review.
  - Trigger PR 606 added exactly the frozen request at f637f73cbde3d6fb07d40d5faf36a44ffdf4d5ad.
  - Workflow 30352834444 ran on freqtrade-synology-staging; job 90254107799 accepted the runner and passed exact-one-file scope.
  - The first failure was Validate staging identity and durable storage before credential checks, dependency installation, WebSocket collection, artifact publication or evaluation.
  - Trigger PR 606 was closed without merge.
  - No collection package or raw OKX artifact was created and orders remained zero.
first_failure:
  marker: OKX_ACCEPTANCE_DURABLE_ROOT_NOT_READY
  evidence: The exact runner and request mapping were present, while the silent pre-collection durable-root validation exited before all downstream steps.
changes:
  - Bind an explicit canonical state directory in the workflow.
  - Validate runner, OS, state directory, durable-root parent and ephemeral-path exclusion with named errors.
  - Create only the missing canonical durable root under the verified state directory using umask 027.
  - Require the created root to be writable.
  - Perform an atomic fsync, rename and read-back probe and remove it before network activity.
  - Add static regression coverage and update execution documentation.
safety:
  - This repair contains no canonical trigger request.
  - It performs no OKX network collection, replay, model work, strategy work, order submission or live-capital action.
  - It cannot create storage outside /var/lib/freqtrade-staging-state/okx-liquidation-acceptance.
validation:
  - Exact-head AI Platform CI pending.
  - Exact-head Freqtrade CI including CI Gate pending.
  - Exact-head zizmor pending.
blockers:
  - Guarded merge requires full exact-head green CI and no unresolved review threads.
next_action: Complete exact-head CI and guarded merge, then create one fresh exact-one-file trigger from current develop and monitor the 24-hour terminal evidence without merging the trigger.
```
