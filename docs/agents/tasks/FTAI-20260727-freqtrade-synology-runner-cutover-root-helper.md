---
task_id: FTAI-20260727-freqtrade-synology-runner-cutover-root-helper
status: validating
branch: fix/freqtrade-synology-runner-cutover-root-helper-20260727
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

# Root-owned Freqtrade Synology runner cutover retry

## Goal

Retry the dedicated Freqtrade runner cutover with a detached helper that explicitly runs as root, matching the live Compose runner execution context and the permissions required for the Synology host path and Docker socket.

## Proven state

- PR 503 merged the first bounded cutover workflow.
- Exact-head CI and security analysis passed before that merge.
- The live merge status reported `synology/freqtrade-runner-cutover: failure`.
- No component verification statuses were published, so failure occurred before post-reconnection verification.
- The dedicated image declares `USER runner` while the live Compose runner declares `user: "0:0"`.
- The failed workflow launched helper-image commands without `--user 0:0` while writing below `/volume1/docker/freqtrade` and accessing `/var/run/docker.sock`.

## Acceptance

1. Use the same exact image already proven by live preflight.
2. Validate the canonical Freqtrade Compose project, service and named volumes before mutation.
3. Write the durable Compose file and helper from the currently root-owned runner process.
4. Launch the detached replacement helper with explicit `--user 0:0`.
5. Preserve the existing `runner_config` and `runner_work` volumes as external volumes.
6. Preserve the canonical container name, project/service labels and dedicated state mount.
7. Verify the replacement after the runner reconnects and publish component plus overall statuses.
8. Do not remove volumes, prune Docker resources or reference OteryN.

## Checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-27T21:05:00+02:00
head: ef8426d4965e15aef088f960c34207ae20d7ed72
branch: fix/freqtrade-synology-runner-cutover-root-helper-20260727
pr: null
status: validating
first_failure:
  marker: ROOT_HELPER_LAUNCH_CONTEXT_MISMATCH
  evidence: The first live cutover published only the launch-level failure status; its helper image defaults to USER runner while host mutation and Docker control require the root context used by the live Compose service.
changed_paths:
  - .github/workflows/freqtrade-synology-runner-dedicated-cutover-retry.yml
  - tests/ai_platform/portal/deployment/test_freqtrade_synology_runner_cutover_retry.py
  - docs/agents/tasks/FTAI-20260727-freqtrade-synology-runner-cutover-root-helper.md
validation:
  - command: exact-head repository CI and security analysis
    result: NOT_RUN
  - command: trusted-develop root-owned detached live cutover
    result: NOT_RUN
blockers:
  - Exact-head CI and security analysis must pass before merge.
next_action: Open the bounded retry PR, validate its exact head, merge it and observe the live component statuses.
```
