---
task_id: FTAI-20260727-freqtrade-synology-compose-orphan-recovery
status: validating
branch: fix/freqtrade-synology-compose-orphan-recovery-20260727
base_branch: develop
created: 2026-07-27
updated: 2026-07-27
owned_paths:
  - .github/workflows/repair-freqtrade-synology-runner-orphan.yml
  - tests/ai_platform/portal/deployment/test_freqtrade_synology_runner_orphan_repair.py
  - docs/agents/tasks/FTAI-20260727-freqtrade-synology-compose-orphan-recovery.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260727-freqtrade-synology-runner-isolation.md
---

# Freqtrade Synology Compose orphan recovery

## Goal

Repair the running Freqtrade runner container name that Synology Container Manager cannot manage, without stopping or restarting the runner and without changing containers, projects or volumes owned by OteryN.

## Acceptance

1. Detect only a name matching `<12-hex>_freqtrade-synology-staging-runner`.
2. Verify exact Compose labels `freqtrade-deploy-runner` and `runner` before mutation.
3. Refuse multiple candidates or a canonical-name collision.
4. Rename the verified running container to `freqtrade-synology-staging-runner` using `docker rename` only.
5. Verify the runner remains running with the same Compose labels.
6. Do not stop, restart, remove or recreate a container or volume.
7. Execute only from trusted `develop` on the dedicated `freqtrade-staging` runner.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-27T18:15:00+02:00
head: 53f1a81f95f7a2eee5fad2105d9379d7235ef1c5
branch: fix/freqtrade-synology-compose-orphan-recovery-20260727
pr: null
status: validating
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260727-freqtrade-synology-runner-isolation.md
  - OteryN PR 162 verified name-repair pattern
owned_paths:
  - .github/workflows/repair-freqtrade-synology-runner-orphan.yml
  - tests/ai_platform/portal/deployment/test_freqtrade_synology_runner_orphan_repair.py
  - docs/agents/tasks/FTAI-20260727-freqtrade-synology-compose-orphan-recovery.md
proven:
  - Synology displays the running container as c1c396947593_freqtrade-synology-staging-runner.
  - Synology reports that the undefined container does not exist and cannot stop it through the stale UI record.
  - The container belongs to Compose project freqtrade-deploy-runner and currently runs the old shared deploy-runner image.
  - OteryN PR 162 repaired the same short-ID-prefixed Compose condition by exact-label verification followed by docker rename without restart or volume mutation.
derived:
  - The Freqtrade container is a Compose replacement orphan under a temporary prefixed name.
  - A label-verified rename is the narrowest repair and preserves the active runner process and named volumes.
unknown:
  - Live Compose service label until the trusted runner workflow inspects it.
  - Whether the canonical container name is currently free until live inspection.
conflicts: []
first_failure:
  marker: SYNLOGY_CONTAINER_UNDEFINED_PREFIXED_NAME
  evidence: DSM cannot operate on c1c396947593_freqtrade-synology-staging-runner and reports that the undefined container does not exist.
rejected_hypotheses:
  - Stop or restart the entire Container Manager service.
  - Delete or recreate the runner container.
  - Remove or replace named runner volumes.
  - Modify the OteryN runner project.
changed_paths:
  - .github/workflows/repair-freqtrade-synology-runner-orphan.yml
  - tests/ai_platform/portal/deployment/test_freqtrade_synology_runner_orphan_repair.py
  - docs/agents/tasks/FTAI-20260727-freqtrade-synology-compose-orphan-recovery.md
validation:
  - command: exact-head repository CI and security analysis
    result: NOT_RUN
    evidence: PR not opened yet.
  - command: trusted develop one-shot live name repair
    result: NOT_RUN
    evidence: Runs only after reviewed workflow merges.
blockers:
  - Exact-head CI and security analysis must pass before merge.
next_action: Open the bounded repair PR, validate its exact head, merge it, and observe the trusted-develop one-shot rename result before changing the runner image.
```
