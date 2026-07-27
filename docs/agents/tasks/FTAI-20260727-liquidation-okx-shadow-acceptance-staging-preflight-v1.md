---
task_id: FTAI-20260727-liquidation-okx-shadow-acceptance-staging-preflight-v1
status: blocked
branch: docs/okx-staging-runner-queue-blocker-20260727
base_branch: develop
created: 2026-07-27
updated: 2026-07-27
related_pr: "#442"
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
  - PR 442 workflow state
optional_reads: []
---

# OKX shadow acceptance staging preflight v1

## Goal

Verify the established Synology self-hosted runner, protected environment, durable state path and public OKX endpoint access without starting liquidation collection or creating the canonical 24-hour request.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-27T11:20:00+02:00
head: PENDING
base_develop: 2ba6ea967144e9629048b1b02dec67684e56dbc0
branch: docs/okx-staging-runner-queue-blocker-20260727
pr: null
status: blocked
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
  - PR 436 passed exact-head AI Platform CI 30249780591, Freqtrade CI 30249780754 including CI Gate, and zizmor 30249780728 at head 3ad3e44b34c670629c134709e6b8091979aa4075.
  - PR 436 merged into develop as 2ba6ea967144e9629048b1b02dec67684e56dbc0 and installed the guarded non-collecting staging preflight.
  - PR 442 adds exactly the canonical request file at head f23781f105861b970c52e56f1628cb12c7f907e0 and must remain unmerged.
  - PR 442 passed AI Platform CI 30251172989, Freqtrade CI 30251172997 and zizmor 30251172996.
  - Self-hosted preflight run 30251172959 created job 89929271587 but the job remains queued and has executed no step.
  - The canonical 24-hour request does not exist and no liquidation collection, raw market-data capture, replay, model work, strategy work or order execution has started.
derived:
  - The request and repository workflow contract are valid enough to schedule the intended self-hosted job.
  - The first operational failure is runner availability or label matching before workflow execution, not preflight code, storage, endpoint or credential validation.
  - Keeping PR 442 open preserves one authoritative trigger; creating another trigger or a hosted-runner fallback would duplicate or weaken the evidence boundary.
unknown:
  - Whether oteryn-synology-staging is offline, disabled, busy or missing one of self-hosted, Linux or oteryn-staging labels.
  - The protected environment values and durable-filesystem result because no self-hosted step has executed.
  - Whether the durable host path has a separately enforceable immutable snapshot or retention mechanism.
conflicts: []
first_failure:
  marker: self-hosted-runner-not-scheduling
  evidence: Workflow run 30251172959 remains queued at job 89929271587 with no executed steps while all GitHub-hosted checks on the same request head passed.
rejected_hypotheses:
  - Create another identical trigger PR.
  - Fall back to a GitHub-hosted runner or weaken the custom-label requirement.
  - Merge the one-file trigger request into develop.
  - Start the canonical 24-hour collection before the non-collecting preflight passes.
changed_paths:
  - docs/agents/tasks/FTAI-20260727-liquidation-okx-shadow-acceptance-staging-preflight-v1.md
validation:
  - command: PR 436 exact-head repository CI
    result: PASS
    evidence: AI Platform CI 30249780591, Freqtrade CI 30249780754 and zizmor 30249780728 passed before merge 2ba6ea967144e9629048b1b02dec67684e56dbc0.
  - command: PR 442 standard exact-head repository CI
    result: PASS
    evidence: AI Platform CI 30251172989, Freqtrade CI 30251172997 and zizmor 30251172996 passed at f23781f105861b970c52e56f1628cb12c7f907e0.
  - command: PR 442 Synology staging preflight
    result: BLOCKED
    evidence: Run 30251172959 and job 89929271587 remain queued with no executed steps.
blockers:
  - Restore an available self-hosted Linux runner named oteryn-synology-staging with the oteryn-staging label so the existing authoritative PR 442 job can start.
next_action: Bring oteryn-synology-staging online with labels self-hosted, Linux and oteryn-staging and allow existing workflow run 30251172959 to complete; then publish its bounded report and close PR 442 without merge.
```
