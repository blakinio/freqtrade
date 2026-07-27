---
task_id: FTAI-20260727-liquidation-okx-shadow-acceptance-staging-preflight-v1
status: validating
branch: feat/okx-shadow-acceptance-staging-preflight-v2
base_branch: develop
created: 2026-07-27
updated: 2026-07-27
related_pr: null
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
updated_at: 2026-07-27T09:56:00+02:00
head: 2b4b685de99a8fd5a25cee8722a4112bb4a94d9c
base_develop: f21a258643d70b4387e366e8b466dbc56735f44f
branch: feat/okx-shadow-acceptance-staging-preflight-v2
pr: not_opened
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
  - Develop f21a258643d70b4387e366e8b466dbc56735f44f contains merged PR 417 acceptance infrastructure plus later path-disjoint orchestration and Binance fixes.
  - PR 417 remains inert because no canonical 24-hour request exists.
  - The established self-hosted runner is named oteryn-synology-staging and carries the custom oteryn-staging label.
  - The established protected environment is synology-staging and exposes OTERYN_STAGING_STATE_DIR as /var/lib/oteryn-staging-state.
  - The merged acceptance workflow instead expects the unconfigured okx-liquidation-staging label and environment, so its trigger must not be created unchanged.
  - Former PR 424 validated the same four-file package at exact head b754e78e9a2109383e4b9c114f567a5ead491eba with AI Platform CI, Freqtrade CI and zizmor all passing.
  - Former PR 424 became non-mergeable only after develop advanced through unrelated PRs 423 and 429.
  - This branch recreates exactly the four declared paths from the green head on current develop without diagnostic workflow history.
derived:
  - A successful preflight can justify a later workflow-mapping PR but cannot authorize the 24-hour run by itself.
  - The future durable root candidate is /var/lib/oteryn-staging-state/okx-liquidation-acceptance with file URI file:///var/lib/oteryn-staging-state/okx-liquidation-acceptance.
  - The acceptance workflow must remain unchanged until the preflight verifies the actual runner, state path, filesystem probe and public endpoint reachability.
unknown:
  - Exact-head repository CI and review outcome for the reconciled replacement branch.
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
  - Merge former PR 424 after its base became stale and GitHub reported it non-mergeable.
changed_paths:
  - .github/workflows/ai-platform-okx-liquidation-shadow-acceptance-staging-preflight.yml
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE_STAGING_PREFLIGHT.md
  - tests/ai_platform_integration/test_liquidation_okx_shadow_acceptance_staging_preflight.py
  - docs/agents/tasks/FTAI-20260727-liquidation-okx-shadow-acceptance-staging-preflight-v1.md
validation:
  - command: former PR 424 exact-head repository CI
    result: PASS
    evidence: Head b754e78e9a2109383e4b9c114f567a5ead491eba passed AI Platform CI 30246717303, Freqtrade CI 30246717323 and zizmor 30246717320 before develop advanced.
  - command: replacement branch exact-head repository CI
    result: NOT_RUN
    evidence: Replacement PR has not been opened yet.
  - command: python tools/agents/checkpoint.py docs/agents/tasks/FTAI-20260727-liquidation-okx-shadow-acceptance-staging-preflight-v1.md --require-checkpoint
    result: NOT_RUN
    evidence: Repository CI is authoritative for the replacement head.
blockers: []
next_action: Open the reconciled four-file replacement PR against current develop, close superseded PR 424, fix only confirmed exact-head CI or review failures, and merge when all required checks pass.
```
