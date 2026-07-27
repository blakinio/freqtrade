---
task_id: FTAI-20260727-liquidations-live-synology-cpu-quota-compat
status: implementation-complete-ci-pending
branch: fix/liquidations-live-synology-cpu-quota-compat-20260727
base_branch: develop
created: 2026-07-27
updated: 2026-07-27
related_pr: pending
owned_paths:
  - deploy/synology/liquid20/deploy-live.sh
  - deploy/synology/liquid20/compose.yaml
  - deploy/synology/liquid20/LIVE_STREAM.md
  - tests/ai_platform_integration/test_synology_liquid20_live_deployment.py
  - docs/agents/tasks/FTAI-20260727-liquidations-live-synology-cpu-quota-compat.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260727-liquidations-live-stream-repair.md
  - docs/agents/tasks/FTAI-20260727-liquidations-live-synology-identity-paths.md
---

# Liquidations live Synology CPU quota compatibility

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-27T20:45:00Z
head: af2cf8cbd878af54d612353f341b965ae2ab5c77
branch: fix/liquidations-live-synology-cpu-quota-compat-20260727
pr: pending
status: implementation-complete-ci-pending
context_routes:
  - docs/agents/tasks/FTAI-20260727-liquidations-live-stream-repair.md
  - deploy/synology/liquid20/LIVE_STREAM.md
owned_paths:
  - deploy/synology/liquid20/deploy-live.sh
  - deploy/synology/liquid20/compose.yaml
  - deploy/synology/liquid20/LIVE_STREAM.md
  - tests/ai_platform_integration/test_synology_liquid20_live_deployment.py
  - docs/agents/tasks/FTAI-20260727-liquidations-live-synology-cpu-quota-compat.md
proven:
  - Controlled run 30303141155 built exact image 19600ec2c6588986af37c2b79cdbe3bbd8e6b08c and resolved uid 1026, gid 0 before candidate start.
  - Docker rejected the candidate before creation because NanoCPUs are unsupported by the Synology kernel/CFS cgroup configuration.
  - Production was not replaced and accepted evidence was not mutated.
  - The repair probes CPU quota capability with the exact image before candidate start.
  - A 1.0 CPU quota is applied only after a successful probe.
  - Only the exact known CFS/cgroup unsupported response enables a fallback without CPU quota; every other probe failure remains fatal.
  - The 512 MiB memory limit and PID limit remain mandatory in all cases.
  - The operational report records CPU quota support/application and actual NanoCPUs.
derived:
  - Compose must omit an unconditional CPU quota on this target while retaining memory and PID limits.
unknown:
  - Real candidate and production result until the reviewed repair reaches develop.
conflicts: []
first_failure:
  marker: SYNOLOGY_CPU_CFS_UNAVAILABLE
  evidence: docker reported NanoCPUs can not be set because CPU CFS or the required cgroup is unavailable.
rejected_hypotheses:
  - Remove all resource limits.
  - Retry the same unconditional --cpus deployment.
  - Change accepted evidence permissions or run the collector as root.
  - Ignore unexpected Docker probe failures.
changed_paths:
  - deploy/synology/liquid20/deploy-live.sh
  - deploy/synology/liquid20/compose.yaml
  - deploy/synology/liquid20/LIVE_STREAM.md
  - tests/ai_platform_integration/test_synology_liquid20_live_deployment.py
  - docs/agents/tasks/FTAI-20260727-liquidations-live-synology-cpu-quota-compat.md
validation:
  - command: bash -n deploy/synology/liquid20/deploy-live.sh
    result: PASS
    evidence: Updated shell script parses successfully.
  - command: exact-head repository CI and security analysis
    result: PENDING
    evidence: Required before merge.
blockers:
  - Exact-head CI and review are pending.
  - Real deployment runs only after reviewed merge to develop.
next_action: Open the PR, pass exact-head CI and review, merge, then inspect the new controlled Synology operational artifact.
```
