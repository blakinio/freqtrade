---
task_id: FTAI-20260727-liquidations-live-symbol-universe-observation
status: implementation-complete-ci-pending
branch: fix/liquid20-live-symbol-universe-observation-20260727
base_branch: develop
created: 2026-07-27
updated: 2026-07-27
related_pr: 553
owned_paths:
  - deploy/synology/liquid20/deploy-live.sh
  - deploy/synology/liquid20/live-entrypoint.sh
  - deploy/synology/liquid20/compose.yaml
  - deploy/synology/liquid20/.env.example
  - deploy/synology/liquid20/LIVE_STREAM.md
  - tests/ai_platform_integration/test_synology_liquid20_live_deployment.py
  - docs/agents/tasks/FTAI-20260727-liquidations-live-symbol-universe-observation.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260727-liquidations-live-stream-repair.md
  - docs/agents/tasks/FTAI-20260727-liquidations-live-synology-cpu-quota-compat.md
---

# Liquidations live symbol universe and observation repair

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-27T22:20:00Z
branch: fix/liquid20-live-symbol-universe-observation-20260727
pr: 553
status: implementation-complete-ci-pending
proven:
  - Controlled deployment run 30306056410 built exact image fbf8551f606f6868cb86d65432fb9ab4b11311c3, passed CPU compatibility and identity resolution, then exhausted the 45-minute timeout before candidate readiness.
  - Isolated diagnostic run 30309745465 succeeded and artifact 8669894495 contains live-state-v1.json from the exact image.
  - The diagnostic state was active with advancing collector heartbeat, execution disabled and no trading credentials.
  - Both Bybit and Binance remained disconnected because dynamic discovery exceeded the configured maximum of 500; both subscription counts were zero.
  - The Synology kernel also reports that the PID cgroup limit is unsupported and discarded.
  - Repeated helper-container launches in state_observation made the deployment wait path unbounded relative to the workflow timeout.
repair:
  - Raise the deployment and entrypoint universe bound to the collector's existing validated ceiling of 1000.
  - Resolve the bound from the checked-in environment default and reject values outside 1..1000.
  - Read candidate and production state directly from /data through bounded docker exec calls.
  - Require connected=true and non-empty subscriptions for both Bybit and Binance before readiness succeeds.
  - Print the last state and bounded container logs when readiness fails.
  - Probe PID capability strictly and omit the limit only for the exact known unsupported Synology response.
  - Keep the 512 MiB memory limit mandatory and record actual CPU/PID capability and application state.
boundaries:
  - No exchange credentials, signals, orders, execution authority or live capital.
  - No Docker socket inside the collector.
  - Candidate-first exact-SHA deployment and rollback remain mandatory.
  - Accepted evidence under data/runs remains immutable and digest-verified.
validation:
  - command: bash -n deploy/synology/liquid20/deploy-live.sh
    result: PASS
  - command: sh -n deploy/synology/liquid20/live-entrypoint.sh
    result: PASS
  - command: focused deployment tests in extracted exact source bundle
    result: PASS
  - command: exact-head repository CI and security analysis
    result: PENDING
unknown:
  - Real candidate and production result until this reviewed repair reaches develop.
next_action: Remove the temporary source-export workflow, synchronize with current develop, pass exact-head CI and review, merge, then inspect the new controlled Synology artifact.
```
