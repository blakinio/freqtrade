---
task_id: FTAI-20260727-liquidations-live-stream-repair
status: completed
branch: develop
base_branch: develop
updated: 2026-07-28
related_pr: 553
required_reads:
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/LIQUIDATIONS_LIVE_STREAM_ARCHITECTURE.md
search_first:
  - .github/workflows/liquidations-live-synology.yml
  - deploy/synology/liquid20/deploy-live.sh
  - deploy/synology/liquid20/LIVE_STREAM.md
  - tests/ai_platform_integration/test_synology_liquid20_live_deployment.py
optional_reads:
  - docs/ai_platform/portal/LIQUIDATIONS_AND_AI_BOT_ARCHITECTURE.md
---

# FTAI-20260727-liquidations-live-stream-repair

The continuous read-only liquidation stream, truthful portal status model and controlled Synology collector deployment are complete. PR #553 delivered the final native deployment repair and trusted develop deployment run `30336184269` produced operational proof for candidate and production.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-28T07:25:00Z
head: b6f4589ff4da88a9cbd91342c657de6b57def142
branch: develop
pr: 553
status: completed
context_routes:
  - docs/agents/tasks/FTAI-20260727-liquidations-live-stream-repair.md
  - .github/workflows/liquidations-live-synology.yml
  - deploy/synology/liquid20/deploy-live.sh
  - deploy/synology/liquid20/LIVE_STREAM.md
  - tests/ai_platform_integration/test_synology_liquid20_live_deployment.py
  - docs/ai_platform/portal/LIQUIDATIONS_LIVE_STREAM_ARCHITECTURE.md
owned_paths:
  - .github/workflows/liquidations-live-synology.yml
  - deploy/synology/liquid20/deploy-live.sh
  - deploy/synology/liquid20/compose.yaml
  - deploy/synology/liquid20/LIVE_STREAM.md
  - tests/ai_platform_integration/test_synology_liquid20_live_deployment.py
  - docs/agents/tasks/FTAI-20260727-liquidations-live-stream-repair.md
proven:
  - PR #489 introduced the separate continuous live/shadow stream, immutable historical fallback and truthful LIVE/STALE/OFFLINE/HISTORICAL portal semantics.
  - PR #510 repaired the non-root identity, existing data-root group, runner/host candidate paths and bounded live-directory bootstrap.
  - PR #532 added strict Synology CPU quota capability fallback while preserving mandatory supported resource boundaries.
  - PR #553 merged as b6f4589ff4da88a9cbd91342c657de6b57def142 and natively observes state inside candidate and production containers, handles unsupported CPU and PID cgroups, and raises the validated public universe bound to 1000.
  - Trusted develop deployment run 30336184269 completed successfully on the exact merged SHA and uploaded artifact 8679367850.
  - Candidate heartbeat advanced from 1785221733426 to 1785221739316; Bybit and Binance were configured and connected with 655 and 526 subscriptions respectively.
  - Production heartbeat advanced from 1785221816002 to 1785221838334; both source files grew and real exchange events were recorded.
  - Production runtime is uid 1026, gid 0, restart unless-stopped, 512 MiB memory, no unsupported CPU or PID cgroup limit, and trading_authorized=false.
  - Accepted historical evidence digest remained e13709197391082710047088733fc695ac9b99347848f7cc7ce4c8fafb6a8829 before and after deployment.
  - Duplicate PR #552 was closed without merge after PR #553 and its successful deployment superseded it.
derived:
  - The portal can truthfully expose LIVE while the deployed collector continues publishing fresh state and advancing heartbeats.
  - A quiet exchange window is not required for acceptance because heartbeat, connectivity and subscription readiness are independently proven; this run also observed real events.
unknown:
  - Long-term exchange availability and future upstream protocol changes remain operational monitoring concerns, not blockers for this completed deployment.
conflicts: []
first_failure:
  marker: LIQUID20_DEPLOYMENT_CHAIN_RESOLVED
  evidence: Identity/path, unsupported CPU quota, unsupported PID limit, repeated helper polling and insufficient universe-bound failures were resolved through PRs #510, #532 and #553.
rejected_hypotheses:
  - Run the collector as root.
  - Mutate accepted historical evidence or recursively change its permissions.
  - Require unsupported Synology CPU or PID cgroup controls.
  - Treat portal polling as proof of fresh exchange data.
changed_paths:
  - .github/workflows/liquidations-live-synology.yml
  - deploy/synology/liquid20/deploy-live.sh
  - deploy/synology/liquid20/compose.yaml
  - deploy/synology/liquid20/LIVE_STREAM.md
  - tests/ai_platform_integration/test_synology_liquid20_live_deployment.py
  - docs/agents/tasks/FTAI-20260727-liquidations-live-stream-repair.md
validation:
  - command: GitHub status liquidations-live-synology on b6f4589ff4da88a9cbd91342c657de6b57def142
    result: PASS
    evidence: Trusted workflow run 30336184269 completed with success.
  - command: Operational artifact 8679367850 report validation
    result: PASS
    evidence: Candidate and production heartbeats advanced, both public sources were connected with non-empty subscriptions, file growth and real events were observed, and historical evidence was unchanged.
  - command: Runtime safety validation
    result: PASS
    evidence: Non-root uid 1026, exact image SHA, unless-stopped restart, 512 MiB memory, no Docker socket or trading authorization, and compatibility-safe CPU/PID settings were proven.
blockers: []
next_action: Continue normal monitoring of collector heartbeat freshness, source connectivity and portal LIVE/STALE/OFFLINE transitions.
```
