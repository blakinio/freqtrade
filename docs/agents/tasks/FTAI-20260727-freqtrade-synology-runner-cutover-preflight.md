---
task_id: FTAI-20260727-freqtrade-synology-runner-cutover-preflight
status: validating
branch: fix/freqtrade-synology-runner-cutover-preflight-20260727-v2
base_branch: develop
created: 2026-07-27
updated: 2026-07-27
owned_paths:
  - .github/workflows/freqtrade-synology-runner-cutover-preflight.yml
  - deploy/synology/freqtrade-runner/compose.yml
  - tests/ai_platform/portal/deployment/test_freqtrade_synology_runner_isolation.py
  - docs/agents/tasks/FTAI-20260727-freqtrade-synology-runner-cutover-preflight.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260727-freqtrade-synology-runner-isolation.md
---

# Freqtrade Synology runner cutover preflight

## Goal

Prove the dedicated exact Freqtrade runner image, current Compose identity and preserved registration volumes on Synology before any live runner replacement.

## Acceptance

1. Preserve the canonical container name `freqtrade-synology-staging-runner` in the dedicated Compose package.
2. Run only from trusted `develop` on the dedicated `freqtrade-staging` runner.
3. Pull and smoke-test the exact image tag for the merged commit.
4. Verify the current running container has exact project/service labels.
5. Verify `/runner` and `/work` are the Compose-owned `runner_config` and `runner_work` volumes.
6. Check the dedicated host state directory without creating or modifying it.
7. Publish bounded commit statuses for container, volumes, image and state path.
8. Do not stop, restart, remove or recreate a container or volume.
9. Do not modify any independently owned runner project.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-27T19:35:00+02:00
head: f98ca47da8817dd691b8e59047e2916d5993a323
branch: fix/freqtrade-synology-runner-cutover-preflight-20260727-v2
pr: null
status: validating
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260727-freqtrade-synology-runner-isolation.md
  - PR 490 merged runner-name repair
  - PR 493 merged observable runtime status
  - PR 496 superseded after develop advanced
proven:
  - The live Freqtrade runner now has canonical container name freqtrade-synology-staging-runner.
  - Commit status synology/freqtrade-runner-name returned success after exact project/service verification.
  - The live runner still uses the previous shared image and requires a dedicated Freqtrade image/state cutover.
  - The repository contains the dedicated Freqtrade image and Compose package merged by PR 485.
  - The first preflight branch passed exact-head AI Platform CI, image build, security analysis and Freqtrade CI before being superseded by newer develop merges.
derived:
  - A read-only live preflight is required before replacing the container that is executing the workflow.
  - The Compose package must explicitly retain the canonical container name during recreation.
unknown:
  - Exact-image availability on Synology after develop publication.
  - Exact current runner_config and runner_work volume ownership labels.
  - Existence of /volume1/docker/freqtrade/state on the Synology host.
conflicts: []
first_failure:
  marker: LIVE_CUTOVER_PREREQUISITES_UNPROVEN
  evidence: The name repair is proven, but image, volume and state-path prerequisites have not yet been inspected together.
rejected_hypotheses:
  - Force-merge a stale branch after develop advanced.
  - Recreate the live runner before verifying the exact target image.
  - Delete or replace registration volumes.
  - Use a non-exact mutable image as preflight evidence.
changed_paths:
  - .github/workflows/freqtrade-synology-runner-cutover-preflight.yml
  - deploy/synology/freqtrade-runner/compose.yml
  - tests/ai_platform/portal/deployment/test_freqtrade_synology_runner_isolation.py
  - docs/agents/tasks/FTAI-20260727-freqtrade-synology-runner-cutover-preflight.md
validation:
  - command: exact-head repository CI, dedicated image build and security analysis
    result: NOT_RUN
    evidence: Fresh PR not opened yet.
  - command: trusted-develop live cutover preflight
    result: NOT_RUN
    evidence: Runs automatically only after reviewed merge.
blockers:
  - Exact-head CI and security analysis must pass on the fresh develop base before merge.
  - All four live preflight contexts must be evaluated before a cutover workflow is introduced.
next_action: Open and validate the fresh preflight PR, merge it, then read all four Synology status contexts before planning the self-replacing cutover.
```
