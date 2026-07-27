---
task_id: FTAI-20260727-freqtrade-synology-runner-cutover-root-helper
status: validating
branch: fix/freqtrade-synology-cutover-host-bind-writer-20260727
base_branch: develop
created: 2026-07-27
updated: 2026-07-27
owned_paths:
  - .github/workflows/freqtrade-synology-runner-dedicated-cutover-retry.yml
  - tests/ai_platform/portal/deployment/test_freqtrade_synology_runner_cutover_retry.py
  - docs/agents/tasks/FTAI-20260727-freqtrade-synology-runner-cutover-root-helper.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260727-freqtrade-synology-runner-dedicated-cutover.md
---

# Host-bind Freqtrade Synology runner cutover retry

## Goal

Complete the dedicated Freqtrade runner cutover by staging the helper and durable Compose definition through a root utility container with the Synology host directory bind-mounted at its real host path.

## Proven state

- PR 503 merged the first bounded cutover workflow and returned only the launch-level failure status.
- PR 509 added explicit root execution and passed exact-head CI and security analysis, but its live retry again returned only `synology/freqtrade-runner-cutover: failure`.
- The active runner Compose contract mounts `/volume1/docker/freqtrade/state` only at `/var/lib/freqtrade-staging-state`; it does not mount `/volume1/docker/freqtrade` inside the runner container.
- PR 509 attempted `test -d /volume1/docker/freqtrade/state` and direct writes below `/volume1/docker/freqtrade` from the runner container before launching its detached helper.
- Therefore PR 509 failed before helper launch because it treated a Docker-host path as a path mounted in the runner container.
- The Docker socket remains available, so a separate root utility container can bind the host directory at `/volume1/docker/freqtrade`, stage the helper there, and launch the detached replacement safely.

## Acceptance

1. Use the same immutable image already proven by live preflight.
2. Validate the canonical Freqtrade Compose project, service and named registration volumes before mutation.
3. Do not directly read or write `/volume1/docker/freqtrade` from the runner container.
4. Stage the helper using a root utility container with `/volume1/docker/freqtrade:/volume1/docker/freqtrade`.
5. Launch the detached replacement helper as root with the Docker socket and the same host bind.
6. Preserve `runner_config`, `runner_work`, the canonical container name and the dedicated state mount.
7. Verify the replacement after reconnection and publish identity, image, volumes, state and overall statuses.
8. Do not remove volumes or prune Docker resources.

## Checkpoint

```yaml
checkpoint_version: 2
updated_at: 2026-07-27T21:35:00+02:00
head: 6f74acb3cd2199a853f8f2d721d238cbfa3dd875
branch: fix/freqtrade-synology-cutover-host-bind-writer-20260727
pr: null
status: validating
first_failure:
  marker: HOST_PATH_NOT_MOUNTED_IN_RUNNER
  evidence: PR 509 wrote to /volume1/docker/freqtrade from the runner container, but the runner contract mounts only the state subdirectory at /var/lib/freqtrade-staging-state.
rejected_hypotheses:
  - The immutable target image was unavailable; live preflight had already pulled and inspected it successfully.
  - The registration volumes were missing; live preflight verified both Compose-owned volumes.
  - Root execution alone was sufficient; PR 509 proved root does not make an unmounted Docker-host path visible inside the runner container.
changed_paths:
  - .github/workflows/freqtrade-synology-runner-dedicated-cutover-retry.yml
  - tests/ai_platform/portal/deployment/test_freqtrade_synology_runner_cutover_retry.py
  - docs/agents/tasks/FTAI-20260727-freqtrade-synology-runner-cutover-root-helper.md
validation:
  - command: exact-head repository CI and security analysis
    result: NOT_RUN
  - command: trusted-develop host-bind detached live cutover
    result: NOT_RUN
blockers:
  - Exact-head CI and security analysis must pass before merge.
next_action: Open the host-bind correction PR, validate its exact head, merge it and observe all five live Synology cutover statuses.
```
