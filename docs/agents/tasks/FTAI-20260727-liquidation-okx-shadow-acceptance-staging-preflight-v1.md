---
task_id: FTAI-20260727-liquidation-okx-shadow-acceptance-staging-preflight-v1
status: validating
branch: fix/okx-preflight-latest-head-concurrency-20260727
base_branch: develop
created: 2026-07-27
updated: 2026-07-27
related_pr: "#451"
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
updated_at: 2026-07-27T12:08:00+02:00
head: PENDING
base_develop: 435e58037dd6ca992e4e3f834fc9a07a534c6630
branch: fix/okx-preflight-latest-head-concurrency-20260727
pr: "#451"
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
  - PR 446 passed exact-head AI Platform CI 30254019803, Freqtrade CI 30254019844 including CI Gate, and zizmor 30254019873 before guarded squash merge f9d160af06a9857767e9cece1d0c4c8e39fb7353.
  - PR 442 remains the only canonical one-file trigger and was synchronized at head 456e3d9ba945bfa993557f8b18204cc020d940c4 to runner freqtrade-synology-staging and label freqtrade-staging.
  - Old PR 442 preflight run 30251172959 remains queued on the obsolete runner mapping.
  - Fresh PR 442 preflight run 30256330079 remains pending with no job because the per-PR concurrency group is occupied by the obsolete queued run.
  - Closing PR 442 did not cancel either stale workflow run.
  - Successful Synology workflow run 30205769267 executed on runner name freqtrade-synology-staging, and the durable portal checkpoint records custom label freqtrade-staging with successful state-mount evidence.
  - No liquidation collection, raw market-data capture, replay, model work, strategy work or order execution has started.
derived:
  - The remaining first failure is stale-run concurrency, not runner identity or request content.
  - Setting cancel-in-progress true on the existing per-PR group is fail-safe because the workflow is non-collecting and only the newest exact-one-file HEAD should proceed.
  - The protected environment, state variable, durable path, public endpoint probes and credential refusal remain unchanged and must still fail closed at runtime.
  - PR 442 must be reopened only after PR 451 merges and must still be closed without merge after terminal evidence.
unknown:
  - Exact-head repository CI and review outcome for PR 451.
  - Whether synology-staging currently exposes OTERYN_STAGING_STATE_DIR as /var/lib/oteryn-staging-state.
  - Whether the prospective durable root is writable and has at least 1 GiB free.
  - Whether public OKX endpoints are reachable from the proven Synology runner.
  - Whether the durable host path has a separately enforceable immutable snapshot or retention mechanism.
conflicts: []
first_failure:
  marker: stale-preflight-concurrency-block
  evidence: Run 30251172959 is still queued while corrected run 30256330079 is pending with no job under the same per-PR concurrency group and cancel-in-progress false.
rejected_hypotheses:
  - Create another identical trigger PR.
  - Fall back to a GitHub-hosted runner or remove the custom-label requirement.
  - Remove the protected synology-staging environment.
  - Merge the one-file trigger request into develop.
  - Start the canonical 24-hour collection before the non-collecting preflight passes.
changed_paths:
  - .github/workflows/ai-platform-okx-liquidation-shadow-acceptance-staging-preflight.yml
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE_STAGING_PREFLIGHT.md
  - tests/ai_platform_integration/test_liquidation_okx_shadow_acceptance_staging_preflight.py
  - docs/agents/tasks/FTAI-20260727-liquidation-okx-shadow-acceptance-staging-preflight-v1.md
validation:
  - command: PR 446 exact-head repository CI
    result: PASS
    evidence: AI Platform CI 30254019803, Freqtrade CI 30254019844 including CI Gate, and zizmor 30254019873 passed on head 7c1e93a99bf01b46ce41dffc59395483a431fcc8.
  - command: PR 451 exact-head repository CI
    result: IN_PROGRESS
    evidence: Required workflows must complete on the checkpoint-bound latest-head concurrency correction.
  - command: reopened PR 442 Synology staging preflight
    result: NOT_RUN
    evidence: Merge PR 451 first, then reopen PR 442 to create the latest-head run and cancel stale runs.
blockers: []
next_action: Validate and merge PR 451, reopen the existing one-file PR 442, inspect the terminal bounded preflight artifact, and close PR 442 without merge.
```
