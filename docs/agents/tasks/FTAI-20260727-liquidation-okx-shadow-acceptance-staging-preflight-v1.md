---
task_id: FTAI-20260727-liquidation-okx-shadow-acceptance-staging-preflight-v1
status: validating
branch: fix/okx-staging-runner-mapping-20260727
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
  - PR 442 workflow state
  - proven Synology runner executions
optional_reads: []
---

# OKX shadow acceptance staging preflight v1

## Goal

Verify the established Synology self-hosted runner, protected environment, durable state path and public OKX endpoint access without starting liquidation collection or creating the canonical 24-hour request.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-27T11:21:00+02:00
head: PENDING
base_develop: b48b556706cc95adf93d7fd9b317868a787a54eb
branch: fix/okx-staging-runner-mapping-20260727
pr: null
status: validating
context_routes:
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE.md
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE_EXECUTION.md
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE_STAGING_PREFLIGHT.md
  - docs/agents/tasks/FTAI-20260725-portal-synology-lan-staging.md
owned_paths:
  - .github/workflows/ai-platform-okx-liquidation-shadow-acceptance-staging-preflight.yml
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE_STAGING_PREFLIGHT.md
  - tests/ai_platform_integration/test_liquidation_okx_shadow_acceptance_staging_preflight.py
  - docs/agents/tasks/FTAI-20260727-liquidation-okx-shadow-acceptance-staging-preflight-v1.md
proven:
  - PR 436 passed exact-head AI Platform CI 30249780591, Freqtrade CI 30249780754 including CI Gate, and zizmor 30249780728 before merge 2ba6ea967144e9629048b1b02dec67684e56dbc0.
  - PR 442 adds exactly the canonical request file at head f23781f105861b970c52e56f1628cb12c7f907e0, passed its GitHub-hosted checks and remains unmerged.
  - PR 442 preflight run 30251172959 remains queued at job 89929271587 with no executed step.
  - Successful Synology workflow run 30205769267 executed on runner name freqtrade-synology-staging.
  - The durable portal checkpoint records the same online runner name with custom label freqtrade-staging and successful runner smoke, Docker, persistent-state-mount and deployment evidence.
  - No terminal execution evidence establishes a runner named oteryn-synology-staging or custom label oteryn-staging.
  - The canonical 24-hour request does not exist and no liquidation collection, raw market-data capture, replay, model work, strategy work or order execution has started.
derived:
  - The first operational failure is a repository-side runner identity and label mismatch, not proof that the proven Synology runner is offline.
  - Mapping the preflight to self-hosted, Linux and freqtrade-staging while asserting runner name freqtrade-synology-staging preserves the owner-managed Synology boundary.
  - The protected environment variable and durable filesystem path remain prospective and must still fail closed if absent or incorrect after the job schedules.
  - PR 442 must remain the single authoritative exact-one-file trigger and must not be merged.
unknown:
  - Whether synology-staging currently exposes OTERYN_STAGING_STATE_DIR as /var/lib/oteryn-staging-state.
  - Whether the prospective durable root is writable and has at least 1 GiB free.
  - Whether public OKX endpoints are reachable from the proven Synology runner.
  - Whether the durable host path has a separately enforceable immutable snapshot or retention mechanism.
conflicts: []
first_failure:
  marker: self-hosted-runner-identity-mismatch
  evidence: The queued workflow requires oteryn-staging and oteryn-synology-staging, while terminal run 30205769267 and the durable portal checkpoint prove freqtrade-staging and freqtrade-synology-staging.
rejected_hypotheses:
  - Restore or create an unproven oteryn-synology-staging runner before checking the proven existing runner mapping.
  - Create another identical trigger PR.
  - Fall back to a GitHub-hosted runner or remove the custom-label requirement.
  - Merge the one-file trigger request into develop.
  - Start the canonical 24-hour collection before the non-collecting preflight passes.
changed_paths:
  - .github/workflows/ai-platform-okx-liquidation-shadow-acceptance-staging-preflight.yml
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE_STAGING_PREFLIGHT.md
  - tests/ai_platform_integration/test_liquidation_okx_shadow_acceptance_staging_preflight.py
  - docs/agents/tasks/FTAI-20260727-liquidation-okx-shadow-acceptance-staging-preflight-v1.md
validation:
  - command: historical Synology execution evidence
    result: PASS
    evidence: Run 30205769267 log identifies runner freqtrade-synology-staging; FTAI-20260725-portal-synology-lan-staging records custom label freqtrade-staging and successful runner/state-mount checks.
  - command: correction PR exact-head repository CI
    result: NOT_RUN
    evidence: The correction PR has not been opened yet.
  - command: corrected PR 442 Synology staging preflight
    result: NOT_RUN
    evidence: Merge the reviewed mapping correction, then update the existing request contract on PR 442 to synchronize a fresh run.
blockers: []
next_action: Open and validate the four-file runner-mapping correction; merge it after exact-head CI, update the existing one-file PR 442 request to the proven runner identity, and inspect the resulting terminal bounded preflight evidence.
```
