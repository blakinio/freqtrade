---
task_id: FTAI-20260727-liquidation-okx-shadow-acceptance-staging-preflight-v1
status: validating
branch: feat/okx-shadow-acceptance-staging-preflight-v1
base_branch: develop
created: 2026-07-27
updated: 2026-07-27
related_pr: "#424"
owned_paths:
  - .github/workflows/ai-platform-okx-liquidation-shadow-acceptance-staging-preflight.yml
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE_STAGING_PREFLIGHT.md
  - tests/ai_platform_integration/test_liquidation_okx_shadow_acceptance_staging_preflight.py
  - docs/agents/tasks/FTAI-20260727-liquidation-okx-shadow-acceptance-staging-preflight-v1.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE.md
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE_EXECUTION.md
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE_STAGING_PREFLIGHT.md
search_first:
  - current develop and open OKX acceptance ownership
  - merged PR 417 infrastructure checkpoint
optional_reads: []
---

# OKX shadow acceptance staging preflight v1

## Goal

Verify the established Synology self-hosted runner, protected environment, durable state path and public OKX endpoint access without starting liquidation collection or creating the canonical 24-hour request.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-27T09:31:00+02:00
head: e017e8233f74ed9e47b0b4c035a95abea41c25b9
base_develop: ae63e2aaa403dc3d0a7e192edca6f8126f2d5dbb
branch: feat/okx-shadow-acceptance-staging-preflight-v1
pr: "#424"
status: validating
context_routes:
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE.md
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE_EXECUTION.md
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE_STAGING_PREFLIGHT.md
owned_paths:
  - .github/workflows/ai-platform-okx-liquidation-shadow-acceptance-staging-preflight.yml
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE_STAGING_PREFLIGHT.md
  - tests/ai_platform_integration/test_liquidation_okx_shadow_acceptance_staging_preflight.py
  - docs/agents/tasks/FTAI-20260727-liquidation-okx-shadow-acceptance-staging-preflight-v1.md
proven:
  - Develop ae63e2aaa403dc3d0a7e192edca6f8126f2d5dbb contains merged PR 417 runner, evaluator and guarded 24-hour workflow infrastructure plus unrelated Binance Spot smoke infrastructure.
  - PR 417 remains inert because no canonical 24-hour request exists.
  - The established self-hosted runner is named oteryn-synology-staging and carries the custom oteryn-staging label.
  - The established protected environment is synology-staging and exposes OTERYN_STAGING_STATE_DIR as /var/lib/oteryn-staging-state.
  - The merged acceptance workflow instead expects the unconfigured okx-liquidation-staging label and environment, so its trigger must not be created unchanged.
  - PR 424 adds a separate exact-one-file preflight that targets the established runner and environment, performs no collection and uploads only bounded non-sensitive readiness metadata.
derived:
  - A successful preflight can justify a later workflow-mapping PR but cannot authorize the 24-hour run by itself.
  - The future durable root candidate is /var/lib/oteryn-staging-state/okx-liquidation-acceptance with file URI file:///var/lib/oteryn-staging-state/okx-liquidation-acceptance.
  - The acceptance workflow must remain unchanged until the preflight verifies the actual runner, state path, filesystem probe and public endpoint reachability.
unknown:
  - Exact-head repository CI and review outcome for PR 424.
  - Terminal preflight result on oteryn-synology-staging.
  - Whether the durable host path has a separately enforceable immutable snapshot or retention mechanism.
conflicts: []
first_failure:
  marker: staging-name-mismatch
  evidence: Merged workflow targets okx-liquidation-staging while the established runner and environment use oteryn-staging and synology-staging.
rejected_hypotheses:
  - Create the canonical 24-hour request before staging readiness is verified.
  - Rename or mutate the existing self-hosted runner from repository code.
  - Run a short collection as a substitute for the non-collecting preflight.
  - Treat a passing storage write probe as proof of 24-hour source acceptance.
changed_paths:
  - .github/workflows/ai-platform-okx-liquidation-shadow-acceptance-staging-preflight.yml
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE_STAGING_PREFLIGHT.md
  - tests/ai_platform_integration/test_liquidation_okx_shadow_acceptance_staging_preflight.py
  - docs/agents/tasks/FTAI-20260727-liquidation-okx-shadow-acceptance-staging-preflight-v1.md
validation:
  - command: repository exact-head CI
    result: NOT_RUN
    evidence: PR 424 has not run on the reconciled current-develop head.
  - command: python tools/agents/checkpoint.py docs/agents/tasks/FTAI-20260727-liquidation-okx-shadow-acceptance-staging-preflight-v1.md --require-checkpoint
    result: NOT_RUN
    evidence: No local checkout is available; repository CI is authoritative.
blockers: []
next_action: Move PR 424 to the reconciled head, fix only confirmed exact-head CI or review failures, merge it when green, then create a separate exact-one-file preflight request PR and close it without merge after terminal readiness evidence is captured.
```
