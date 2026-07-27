---
task_id: FTAI-20260727-freqtrade-synology-runner-state-path-cutover
status: implementation-complete-ci-pending
branch: fix/freqtrade-synology-runner-state-path-cutover-20260727
base_branch: develop
created: 2026-07-27
updated: 2026-07-27
related_pr: "#516"
owned_paths:
  - .github/workflows/freqtrade-synology-runner-state-path-cutover.yml
  - tests/ai_platform/portal/deployment/test_freqtrade_synology_runner_state_path_cutover.py
  - docs/agents/tasks/FTAI-20260727-freqtrade-synology-runner-state-path-cutover.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260727-freqtrade-synology-runner-cutover-root-helper.md
---

# Freqtrade Synology runner state-path cutover

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-27T19:44:00Z
head: c57410e917f5a809e554ad4f0f328d5c0177f4e8
branch: fix/freqtrade-synology-runner-state-path-cutover-20260727
pr: "#516"
status: implementation-complete-ci-pending
context_routes:
  - docs/agents/tasks/FTAI-20260727-freqtrade-synology-runner-cutover-root-helper.md
  - docs/agents/tasks/FTAI-20260727-liquidations-live-stream-repair.md
owned_paths:
  - .github/workflows/freqtrade-synology-runner-state-path-cutover.yml
  - tests/ai_platform/portal/deployment/test_freqtrade_synology_runner_state_path_cutover.py
  - docs/agents/tasks/FTAI-20260727-freqtrade-synology-runner-state-path-cutover.md
proven:
  - Retry merge 3127b1826d6e0827be6e1636ee5745d75583d9a3 published synology/freqtrade-runner-cutover failure.
  - The live runner exposes host /volume1/docker/freqtrade/state at /var/lib/freqtrade-staging-state.
  - Retry #509 attempted to create helper and Compose files below unmounted /volume1/docker/freqtrade from inside the runner.
  - The repair writes through the runner-visible state mount and passes the corresponding host path only to the Docker daemon.
  - Registration volumes, canonical project/service/name, exact image and state mount remain unchanged.
  - A bounded rollback Compose definition restores the prior image if target verification fails.
derived:
  - The path translation is required before controlled Liquid20 collector deployment can produce trustworthy Synology evidence.
unknown:
  - Real cutover result until the reviewed workflow reaches develop.
conflicts: []
first_failure:
  marker: RUNNER_HOST_PATH_NOT_MOUNTED
  evidence: The runner mounts only the state subdirectory, while the retry attempted direct writes to the parent host root.
rejected_hypotheses:
  - Change registration volumes or create a new runner identity.
  - Mount the entire /volume1/docker/freqtrade host root into the steady-state runner.
  - Delete runner volumes or bypass exact-image verification.
changed_paths:
  - .github/workflows/freqtrade-synology-runner-state-path-cutover.yml
  - tests/ai_platform/portal/deployment/test_freqtrade_synology_runner_state_path_cutover.py
  - docs/agents/tasks/FTAI-20260727-freqtrade-synology-runner-state-path-cutover.md
validation:
  - command: repository CI and security analysis
    result: PENDING
    evidence: Required on the exact PR head.
blockers:
  - Exact-head CI and review are pending.
  - Real state-path cutover runs only after reviewed merge to develop.
next_action: Complete exact-head CI and review on PR #516, then merge so the trusted develop workflow can verify the dedicated runner before Liquid20 deployment.
```
