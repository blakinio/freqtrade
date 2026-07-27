---
task_id: FTAI-20260727-okx-liquidation-staging-readiness-probe-v1
status: implementing
branch: feat/okx-staging-readiness-probe-v1
base_branch: develop
created: 2026-07-27
updated: 2026-07-27
related_pr: "pending"
owned_paths:
  - .github/workflows/ai-platform-okx-liquidation-staging-readiness.yml
  - docs/ai_platform/LIQUIDATION_OKX_STAGING_READINESS.md
  - docs/agents/tasks/FTAI-20260727-okx-liquidation-staging-readiness-probe-v1.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE_EXECUTION.md
  - docs/agents/tasks/FTAI-20260727-liquidation-okx-shadow-acceptance-infrastructure-v1.md
search_first:
  - current develop and open OKX staging-readiness ownership
  - existing self-hosted workflow and environment safety patterns
optional_reads: []
---

# OKX liquidation staging readiness probe v1

## Goal

Add an inert, exact-one-file readiness probe that verifies the protected
`okx-liquidation-staging` environment, its required variables, durable storage and the
labelled self-hosted Linux runner before the canonical 24-hour acceptance request is
created.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-27T09:13:25+02:00
head: 35d9fe674a5137ba90fdd095fde62937e98e0349
branch: feat/okx-staging-readiness-probe-v1
pr: "pending"
status: implementing
context_routes:
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE_EXECUTION.md
  - docs/ai_platform/LIQUIDATION_OKX_STAGING_READINESS.md
  - .github/workflows/ai-platform-okx-liquidation-staging-readiness.yml
owned_paths:
  - .github/workflows/ai-platform-okx-liquidation-staging-readiness.yml
  - docs/ai_platform/LIQUIDATION_OKX_STAGING_READINESS.md
  - docs/agents/tasks/FTAI-20260727-okx-liquidation-staging-readiness-probe-v1.md
proven:
  - PR 417 merged the inert OKX 24-hour acceptance infrastructure as develop commit 237196b2b5b3bfbdd52609e139f55f585711d4d5.
  - The acceptance workflow requires environment okx-liquidation-staging, runner labels self-hosted/Linux/okx-liquidation-staging and variables OKX_ACCEPTANCE_HOST_ID, OKX_ACCEPTANCE_DURABLE_ROOT and OKX_ACCEPTANCE_DURABLE_URI.
  - The available GitHub connector cannot directly list protected-environment variables or self-hosted runner status.
  - The readiness workflow never installs the collector dependency, performs an OKX network probe, starts collection or writes to the durable acceptance directory.
derived:
  - A started readiness job proves an online runner matches all required labels.
  - A successful readiness job proves the three environment variables are non-empty, the durable root is acceptable and no recognized trading credential is present.
  - The bounded readiness artifact may publish only the declared non-sensitive host identity, credential-free durable URI, runner metadata and boolean checks.
unknown:
  - Exact-head repository CI outcome for this readiness workflow package.
  - Whether the protected environment and labelled runner will pass the future readiness request.
conflicts: []
first_failure:
  marker: readiness-package-not-yet-validated
  evidence: The new workflow and task checkpoint have not completed repository CI on an exact pull-request head.
rejected_hypotheses:
  - Guess the host identity or durable URI in the canonical 24-hour request.
  - Start the 24-hour collector merely to test runner availability.
  - Publish the durable filesystem root or any credential inventory.
  - Execute branch-controlled collector code on a self-hosted runner during readiness verification.
changed_paths:
  - .github/workflows/ai-platform-okx-liquidation-staging-readiness.yml
  - docs/ai_platform/LIQUIDATION_OKX_STAGING_READINESS.md
  - docs/agents/tasks/FTAI-20260727-okx-liquidation-staging-readiness-probe-v1.md
validation:
  - command: python tools/agents/checkpoint.py docs/agents/tasks/FTAI-20260727-okx-liquidation-staging-readiness-probe-v1.md --require-checkpoint
    result: NOT_RUN
    evidence: Exact validation is delegated to repository CI.
  - command: zizmor workflow security analysis
    result: NOT_RUN
    evidence: Exact validation is delegated to repository CI.
blockers: []
next_action: Open the readiness-infrastructure PR, resolve exact-head CI or review failures, merge only when green, then create the separate exact-one-file readiness request PR and inspect its bounded artifact.
```
