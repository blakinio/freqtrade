---
task_id: FTAI-20260724-synology-liquid20-deployment-v1
status: blocked
branch: develop
base_branch: develop
created: 2026-07-24
updated: 2026-07-24
related_pr: "#258"
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
updated_at: 2026-07-24T16:10:00Z
head: 24c726d6d69b31fc80ca8b315f0651d034600b05
branch: develop
pr: "#258"
status: blocked
proven:
  - PR #258 merged to develop as 24c726d6d69b31fc80ca8b315f0651d034600b05.
  - The multi-source collector, frozen policy, evaluator, and 24-hour acceptance runbook are merged on develop.
  - The Synology package provides a local Compose project with a bind-mounted persistent evidence directory.
  - The deployment exposes no ports, mounts no Docker socket, and requires no exchange or Freqtrade trading credentials.
  - Acceptance mode is fixed to exactly 86400 seconds and every start uses a new run directory unless an explicit unused run ID is supplied.
  - Automatic restart is disabled so an interrupted attempt cannot be represented as one uninterrupted accepted run.
  - The image embeds the exact declared collector commit and the entrypoint rejects a runtime commit mismatch.
  - The container root is read-only, all Linux capabilities are dropped, and no-new-privileges is enabled.
  - Dedicated Docker validation run 30098441178 job 89498195818 built the image and verified imports as UID/GID 65534:65534 on a read-only filesystem.
  - Final candidate ce5d81fe4bc4800d08d24a90e51ed27cd1500bb3 passed Freqtrade CI run 30098509415 and zizmor run 30098509595.
unknown:
  - Whether the user's Synology CPU architecture and DSM Container Manager successfully build and start the image.
  - Whether the user's Polish egress reaches both WebSocket feeds and both exchange clock endpoints without restriction.
  - Whether the NAS remains uninterrupted and passes every frozen acceptance gate for 24 hours.
first_failure:
  marker: no-synology-smoke-run
  evidence: The deployable project is merged, but no artifact or log from the user's Synology exists yet.
rejected_hypotheses:
  - Reuse the Oteryn runner container or mount the Docker socket.
  - Expose an inbound port or reverse proxy for a collector that only needs outbound connections.
  - Enable an automatic restart policy for the immutable 24-hour acceptance attempt.
  - Add exchange credentials to improve public market-data collection.
validation:
  - command: Docker image diagnostic run 30098441178 job 89498195818
    result: PASS
  - command: Freqtrade CI run 30098509415
    result: PASS
  - command: zizmor run 30098509595
    result: PASS
blockers:
  - No direct administrative access to the user's Synology is available from this environment.
  - No successful smoke package from the user's Synology has been preserved.
next_action: Deploy deploy/synology/liquid20 on the user's Synology, run the default 60-second smoke, preserve its logs and artifacts, and only then switch the same validated image and commit to acceptance mode.
```
