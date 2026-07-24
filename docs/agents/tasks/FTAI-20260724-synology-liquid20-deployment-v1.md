---
task_id: FTAI-20260724-synology-liquid20-deployment-v1
status: validating
branch: feat/synology-liquid20-deployment-v1
base_branch: develop
created: 2026-07-24
updated: 2026-07-24
owned_paths:
  - deploy/synology/liquid20/Dockerfile
  - deploy/synology/liquid20/compose.yaml
  - deploy/synology/liquid20/entrypoint.sh
  - deploy/synology/liquid20/.env.example
  - deploy/synology/liquid20/README.md
  - tests/ai_platform_integration/test_synology_liquid20_deployment.py
  - docs/agents/tasks/FTAI-20260724-synology-liquid20-deployment-v1.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/LIQUIDATION_MULTI_SOURCE.md
---

# Synology Liquid20 Deployment v1

## Goal

Provide a hardened Synology Container Manager project for the frozen `liquid20-v1` smoke and 24-hour acceptance run without credentials, inbound ports, trading, automatic continuation after interruption, or artifact reuse.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-24T15:00:00Z
branch: feat/synology-liquid20-deployment-v1
status: validating
proven:
  - The multi-source collector, frozen policy, evaluator, and runbook are merged on develop.
  - Synology Container Manager can use a local Compose project with a bind-mounted persistent data directory.
  - The deployment exposes no ports and does not require exchange credentials.
  - Acceptance mode is fixed to 86400 seconds and uses a unique run directory.
  - Automatic restart is disabled so an interrupted attempt cannot be represented as one uninterrupted accepted run.
  - The image embeds the exact declared collector commit and the entrypoint verifies the runtime value matches it.
  - The container root is read-only, capabilities are dropped, and no-new-privileges is enabled.
unknown:
  - Whether the user's Synology CPU architecture and DSM Container Manager successfully build the image.
  - Whether the user's Polish egress reaches both WebSocket feeds and clock endpoints without restriction.
  - Whether the NAS remains uninterrupted and passes every frozen acceptance gate for 24 hours.
blockers:
  - No direct administrative access to the user's Synology is available from this environment.
next_action: Complete repository CI, merge the deployment package, then create the project on the user's Synology and run smoke mode before acceptance mode.
```
