---
task_id: FTAI-20260727-liquidation-okx-shadow-acceptance-staging-preflight-v1
status: fixing
branch: fix/okx-preflight-route-by-custom-runner-label
base_branch: develop
created: 2026-07-27
updated: 2026-07-27
related_prs:
  - "#442"
  - "#446"
  - "#451"
  - "#458"
  - "#461"
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
updated_at: 2026-07-27T13:34:00+02:00
head: PENDING
base_develop: 01004e9b64fb571f283fd7f763805df963cd388d
branch: fix/okx-preflight-route-by-custom-runner-label
pr: "#461"
status: fixing
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
  - PR 446 corrected the frozen OKX runner identity to freqtrade-synology-staging and the custom label to freqtrade-staging after exact-head CI.
  - PR 451 enabled cancellation of stale per-PR preflight runs, so reopening or synchronizing the request schedules only the newest HEAD.
  - PR 458 merged the repository-proven routing correction for the parallel PI-06 Synology preflight: route by the unique custom label freqtrade-staging while retaining exact runner-name and Linux checks inside the probe.
  - PI-06 run 30262205600 was assigned after that routing correction and executed checkout, exact-one-file validation, credential refusal, bounded preflight and artifact upload; therefore custom-label-only routing reaches the established Synology runner.
  - PR 442 remains the only canonical OKX one-file trigger and currently changes only okx-shadow-acceptance-staging-preflight-20260727-v1.json at head fff8f31b4ea59c159ca618a0016bc31d1396205e.
  - PR 442 run 30261984163 remains queued with no steps while the OKX workflow requests the intersection self-hosted/Linux/freqtrade-staging.
  - The workflow already rejects any assigned runner whose exact name is not freqtrade-synology-staging or whose runner.os is not Linux.
  - No liquidation collection, raw market-data capture, replay, model work, strategy work or order execution has started.
derived:
  - The current first failure is multi-label runner routing, not request content, runner identity, concurrency or evidence that the runner is offline.
  - Routing by the unique proven custom label does not weaken target validation because exact runner name and Linux remain fail-closed runtime checks.
  - The protected environment, state variable, durable path, public endpoint probes and credential refusal remain unchanged and must still fail closed at runtime.
unknown:
  - Whether synology-staging exposes OTERYN_STAGING_STATE_DIR as /var/lib/oteryn-staging-state.
  - Whether the prospective durable root is writable and has at least 1 GiB free.
  - Whether public OKX endpoints are reachable from the Synology runner.
  - Whether the durable host path has a separately enforceable immutable snapshot or retention mechanism.
conflicts: []
first_failure:
  marker: MULTI_LABEL_RUNNER_ROUTE_NOT_MATCHED
  evidence: The proven runner is reachable through custom label freqtrade-staging, while OKX run 30261984163 remains queued with no steps under the self-hosted/Linux/freqtrade-staging intersection; PI-06 custom-label-only run 30262205600 was assigned and executed.
rejected_hypotheses:
  - Treat queued status as proof that the runner is offline.
  - Recreate or rename the working Synology runner.
  - Remove the in-probe exact runner-name or Linux checks.
  - Create another identical trigger PR.
  - Fall back to a GitHub-hosted runner or remove the protected environment.
  - Merge the one-file trigger request into develop.
  - Start the canonical 24-hour collection before the non-collecting preflight passes.
changed_paths:
  - .github/workflows/ai-platform-okx-liquidation-shadow-acceptance-staging-preflight.yml
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE_STAGING_PREFLIGHT.md
  - tests/ai_platform_integration/test_liquidation_okx_shadow_acceptance_staging_preflight.py
  - docs/agents/tasks/FTAI-20260727-liquidation-okx-shadow-acceptance-staging-preflight-v1.md
validation:
  - command: focused static workflow contract test
    result: PENDING
    evidence: Exact-head repository CI must validate custom-label-only routing and retained fail-closed checks.
  - command: exact-head repository CI and security analysis
    result: PENDING
    evidence: Required workflows must pass on the final routing-correction head.
  - command: reopened PR 442 Synology staging preflight
    result: NOT_RUN
    evidence: Merge this routing correction, then close and reopen PR 442 to schedule a fresh current-head run.
blockers:
  - Merge the custom-label routing correction after green exact-head CI.
next_action: Validate and merge the routing correction, close and reopen the existing one-file PR 442, inspect the terminal bounded preflight artifact, close PR 442 without merge, and create acceptance-workflow mapping only after every readiness and safety field passes.
```
