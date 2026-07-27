---
task_id: FTAI-20260727-liquidations-live-stream-repair
status: validating
branch: fix/liquidations-live-synology-nanocpus-20260727
base_branch: develop
updated: 2026-07-27
related_pr: 533
required_reads:
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/LIQUIDATIONS_LIVE_STREAM_ARCHITECTURE.md
search_first:
  - .github/workflows/liquidations-live-synology.yml
  - deploy/synology/liquid20/deploy-live.sh
  - tests/ai_platform_integration/test_synology_liquid20_live_deployment.py
optional_reads:
  - docs/ai_platform/portal/LIQUIDATIONS_AND_AI_BOT_ARCHITECTURE.md
---

# FTAI-20260727-liquidations-live-stream-repair

The continuous read-only liquidation stream and truthful portal status model were merged through PR #489. PR #510 repaired the first Synology identity and host-path blockers; PR #533 repairs the proven target-kernel NanoCPUs incompatibility before another controlled collector cutover.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-27T21:08:46Z
head: e8ccb31f2203a0547df90f8ad0b123a0622fdf24
branch: fix/liquidations-live-synology-nanocpus-20260727
pr: 533
status: validating
context_routes:
  - docs/agents/tasks/FTAI-20260727-liquidations-live-stream-repair.md
  - .github/workflows/liquidations-live-synology.yml
  - deploy/synology/liquid20/deploy-live.sh
  - deploy/synology/liquid20/LIVE_STREAM.md
  - tests/ai_platform_integration/test_synology_liquid20_live_deployment.py
  - docs/ai_platform/portal/LIQUIDATIONS_LIVE_STREAM_ARCHITECTURE.md
owned_paths:
  - deploy/synology/liquid20/deploy-live.sh
  - deploy/synology/liquid20/LIVE_STREAM.md
  - tests/ai_platform_integration/test_synology_liquid20_live_deployment.py
  - docs/agents/tasks/FTAI-20260727-liquidations-live-stream-repair.md
proven:
  - PR #489 merged as 51591d89c0fba9917abb4b087a91b49c45911606 and introduced the separate continuous live/shadow stream, immutable historical fallback and truthful LIVE/STALE/OFFLINE/HISTORICAL portal semantics.
  - PR #510 merged as 19600ec2c6588986af37c2b79cdbe3bbd8e6b08c after resolving the non-root UID, existing data-root GID, runner/host candidate paths and bounded live-directory bootstrap.
  - Develop deployment run 30303141155 built exact image 19600ec2c6588986af37c2b79cdbe3bbd8e6b08c and resolved uid=1026 gid=0 before candidate start.
  - Run 30303141155 then failed because Synology Docker rejected --cpus 1.0 with NanoCPUs unavailable when CPU CFS is unsupported or not mounted.
  - Artifact 8667428514 retained the bounded deployment log; no operational JSON report was produced and production replacement had not started.
  - PR #533 removes the hard NanoCPUs quota while retaining 512 MiB memory, 128 PID, non-root, read-only, capability and rollback controls.
  - PR #533 adds focused regression coverage and documents the Synology CPU CFS compatibility boundary.
  - Freqtrade CI run 30304386760 and zizmor run 30304386761 passed on formatted implementation head feb4416f6f3cf95befa00d1ba96e69eb7eb132b9.
  - Current develop head 351567d57760305b992fb1e441205dc32890dc2a was merged into PR #533 without task-owned conflicts, producing synchronized implementation head e8ccb31f2203a0547df90f8ad0b123a0622fdf24.
  - The only review thread created during synchronization concerned a deleted temporary helper workflow; it was outdated and is resolved.
derived:
  - The previous identity and host-path failure is no longer the first active blocker; the next proven blocker is isolated to unsupported Docker NanoCPUs on the target kernel.
  - Production was not replaced in run 30303141155 because failure occurred while starting the isolated candidate, so rollback was not exercised.
  - Collector operational proof remains pending until PR #533 is green on its documentation-advanced head, merged and deployed through the trusted develop-only workflow.
  - The portal cannot truthfully present LIVE until the collector writes a fresh live-state pointer and advancing heartbeats.
unknown:
  - Whether exact-head Freqtrade CI and zizmor pass after this documentation-only checkpoint update.
  - Whether the repaired Synology deployment produces two advancing candidate and production heartbeats.
  - Whether a real exchange liquidation occurs during the bounded observation window; a quiet window is not a deployment failure.
  - Whether rollback evidence succeeds after the first production collector cutover.
conflicts: []
first_failure:
  marker: LIQUID20_DEPLOY_SYNOLOGY_NANOCPUS_UNSUPPORTED
  evidence: Develop deployment run 30303141155 built the exact image and resolved uid=1026 gid=0, then Docker rejected the isolated candidate because --cpus requested NanoCPUs on a Synology kernel without usable CPU CFS support.
rejected_hypotheses:
  - The accepted historical Liquid20 evidence was defective; its digest boundary remains intact and production mutation had not started.
  - The repaired UID, GID or runner/host path mapping caused the latest failure; all three resolved before Docker evaluated the candidate CPU quota.
  - Running the collector as root was required; the failure is a Docker host capability mismatch unrelated to container UID.
  - A real liquidation is required to prove deployment health; advancing heartbeat and dynamic subscriptions are sufficient during a quiet bounded window.
changed_paths:
  - deploy/synology/liquid20/deploy-live.sh
  - deploy/synology/liquid20/LIVE_STREAM.md
  - tests/ai_platform_integration/test_synology_liquid20_live_deployment.py
  - docs/agents/tasks/FTAI-20260727-liquidations-live-stream-repair.md
validation:
  - command: GitHub Liquidations Live Synology run 30303141155 on 19600ec2c6588986af37c2b79cdbe3bbd8e6b08c
    result: FAIL
    evidence: Exact image build and uid=1026 gid=0 resolution passed; isolated candidate start failed with Docker NanoCPUs and CPU CFS unsupported.
  - command: GitHub artifact 8667428514 from run 30303141155
    result: PASS
    evidence: Bounded log captured the first failure; operational JSON report was absent because candidate start did not complete.
  - command: bash -n deploy/synology/liquid20/deploy-live.sh and static resource-control assertions
    result: PASS
    evidence: The controlled deploy script omits --cpus while retaining --memory 512m and --pids-limit 128.
  - command: GitHub Freqtrade CI run 30304386760 on feb4416f6f3cf95befa00d1ba96e69eb7eb132b9
    result: PASS
    evidence: Pre-commit, documentation, Linux matrix, distribution build and CI gate completed successfully.
  - command: GitHub zizmor run 30304386761 on feb4416f6f3cf95befa00d1ba96e69eb7eb132b9
    result: PASS
    evidence: GitHub Actions security analysis completed successfully.
  - command: Compare develop 351567d57760305b992fb1e441205dc32890dc2a with synchronized PR #533 head e8ccb31f2203a0547df90f8ad0b123a0622fdf24
    result: PASS
    evidence: PR #533 is mergeable and changes only the four task-owned paths relative to current develop.
  - command: PR #533 inline review-thread query after synchronization
    result: PASS
    evidence: The sole outdated helper-workflow thread is resolved; no active task-code thread remains.
  - command: python tools/agents/checkpoint.py docs/agents/tasks/FTAI-20260727-liquidations-live-stream-repair.md --require-checkpoint
    result: PASS
    evidence: Compact checkpoint contract validated locally before the documentation update.
  - command: Exact-head GitHub CI and zizmor after this documentation-only checkpoint commit
    result: NOT_RUN
    evidence: The documentation update will advance the PR branch beyond the recorded synchronized implementation head.
blockers:
  - PR #533 exact-head CI and security analysis must pass on the documentation-advanced branch head before merge.
  - Controlled Synology candidate and production heartbeat evidence remains pending until the repair reaches develop.
next_action: Verify exact-head PR #533 CI, zizmor, mergeability and review threads; merge only if green, then inspect the automatic develop-only Synology deployment artifact for candidate and production heartbeat evidence.
```
