---
task_id: FTAI-20260727-freqtrade-synology-runner-dedicated-cutover
status: validating
branch: fix/freqtrade-synology-runner-dedicated-cutover-20260727-v2
base_branch: develop
created: 2026-07-27
updated: 2026-07-27
owned_paths:
  - .github/workflows/freqtrade-synology-runner-dedicated-cutover.yml
  - tests/ai_platform/portal/deployment/test_freqtrade_synology_runner_isolation.py
  - docs/agents/tasks/FTAI-20260727-freqtrade-synology-runner-dedicated-cutover.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260727-freqtrade-synology-runner-isolation.md
  - docs/agents/tasks/FTAI-20260727-freqtrade-synology-runner-cutover-preflight.md
---

# Dedicated Freqtrade Synology runner cutover

## Goal

Replace the live shared-image Freqtrade runner with the proven exact dedicated Freqtrade image while preserving its registration and work volumes, canonical container name, Compose identity and dedicated state mount.

## Acceptance

1. Require all four live cutover-preflight statuses from merge `0e2a6428a7ca29e7c2fdc4ac34be85bb5f5ac0c0` to be successful.
2. Use only exact image `ghcr.io/blakinio/freqtrade-deploy-runner:sha-0e2a6428a7ca29e7c2fdc4ac34be85bb5f5ac0c0` and verify its local image ID.
3. Launch replacement through an independent detached helper so the active runner job can finish before its container is recreated.
4. Preserve the exact existing Compose-owned `runner_config` and `runner_work` volumes as external volumes.
5. Preserve canonical name `freqtrade-synology-staging-runner` and exact project/service labels.
6. Mount `/volume1/docker/freqtrade/state` at `/var/lib/freqtrade-staging-state`.
7. Persist the durable Compose file and a non-secret result marker below `/volume1/docker/freqtrade`.
8. Verify the replacement from a job that runs only after the new runner reconnects.
9. Publish bounded identity, image, volume, state and overall commit statuses.
10. Publish an observable failure if the new runner never reconnects.
11. Do not remove volumes, prune Docker resources or modify independently owned projects.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-27T20:35:00+02:00
head: 52446c12b8ee2d37edc641573662224f01b77f77
branch: fix/freqtrade-synology-runner-dedicated-cutover-20260727-v2
pr: null
status: validating
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260727-freqtrade-synology-runner-isolation.md
  - docs/agents/tasks/FTAI-20260727-freqtrade-synology-runner-cutover-preflight.md
  - PR 490 merged canonical-name repair
  - PR 493 merged observable name verification
  - PR 499 merged live cutover preflight
  - PR 500 superseded after develop advanced through PR 501
proven:
  - Live canonical runner identity and Compose project/service labels are valid.
  - Existing runner_config and runner_work volumes are Compose-owned and valid.
  - Exact dedicated image sha-0e2a6428a7ca29e7c2fdc4ac34be85bb5f5ac0c0 is available and passed tool smoke tests on Synology.
  - Host directory /volume1/docker/freqtrade/state exists.
  - All four live preflight commit statuses are successful.
  - Superseded PR 500 exact head 39b8ed2550663bedb8af688c8886fd2aad7195cf passed Freqtrade CI, AI Platform CI, runner image build and security analysis.
derived:
  - The active runner cannot safely execute its own synchronous Compose recreation.
  - A detached helper plus delayed post-reconnection verification is the narrowest observable cutover mechanism.
  - Reapplying the three final blobs to current develop preserves unrelated PR 501 changes without force-updating the stale branch.
unknown:
  - Final replacement outcome until the reviewed workflow reaches trusted develop.
conflicts: []
first_failure:
  marker: LIVE_RUNNER_STILL_USES_SHARED_IMAGE
  evidence: The preflight proved readiness but intentionally did not mutate the live runner image.
rejected_hypotheses:
  - Force-update the stale PR 500 branch after develop advanced.
  - Replace the container synchronously inside its active Actions step.
  - Delete or recreate registration volumes.
  - Use mutable develop image as cutover evidence.
  - Depend on a long-lived repository token inside the detached helper.
changed_paths:
  - .github/workflows/freqtrade-synology-runner-dedicated-cutover.yml
  - tests/ai_platform/portal/deployment/test_freqtrade_synology_runner_isolation.py
  - docs/agents/tasks/FTAI-20260727-freqtrade-synology-runner-dedicated-cutover.md
validation:
  - command: exact-head repository CI and security analysis
    result: NOT_RUN
    evidence: Fresh PR not opened yet.
  - command: trusted-develop detached live cutover and post-reconnection status verification
    result: NOT_RUN
    evidence: Runs only after reviewed merge.
blockers:
  - Exact-head CI and security analysis must pass on the fresh develop base before merge.
  - No live mutation is allowed before the reviewed workflow reaches trusted develop.
next_action: Open the fresh bounded cutover PR, validate its exact head, merge it, then observe the overall cutover status and all four component statuses.
```
