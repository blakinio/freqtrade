---
task_id: FTAI-20260727-liquidations-live-stream-repair
status: validating
branch: fix/liquidations-live-synology-identity-paths-20260727
base_branch: develop
updated: 2026-07-27
related_pr: 510
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

The continuous read-only liquidation stream and truthful portal status model were merged through PR #489. The remaining work is the controlled Synology collector cutover and operational proof; PR #510 repairs the proven deployment identity and runner/host path blockers.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-27T20:11:30Z
head: 01e5bd2eb331b9273f269a7617e95fbbd51611a1
branch: fix/liquidations-live-synology-identity-paths-20260727
pr: 510
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
  - The first controlled collector deployment stopped before build because LIQUID20_PUID was unset; the dedicated runner path and Docker-host bind path were different, and data/live did not yet exist.
  - PR #510 resolves a non-root UID, derives the existing host data-root GID, separates runner and host candidate paths, bounds live-directory bootstrap and preserves accepted-evidence digest checks.
  - Exact implementation head 01e5bd2eb331b9273f269a7617e95fbbd51611a1 passed Freqtrade CI run 30299336099 and zizmor run 30299336054.
  - PR #510 has no inline review threads.
  - Current develop head is 1f89f6f566525894b785a8488698cf605398e593; PR #510 is seven commits ahead and two commits behind it.
  - This checkpoint update is documentation-only and will advance the branch beyond the recorded implementation head.
derived:
  - The previously green exact-head merge gate is stale because develop advanced after 01e5bd2eb331b9273f269a7617e95fbbd51611a1.
  - Collector operational proof remains pending until the repair is synchronized, reviewed, merged and deployed through the trusted develop-only workflow.
  - The portal cannot truthfully present LIVE until the collector writes a fresh live-state pointer and advancing heartbeats.
unknown:
  - Whether PR #510 remains conflict-free after synchronization with current develop.
  - Whether the repaired Synology deployment produces two advancing candidate and production heartbeats.
  - Whether a real exchange liquidation occurs during the bounded observation window; a quiet window is not a deployment failure.
  - Whether rollback evidence succeeds after the first production collector cutover.
conflicts: []
first_failure:
  marker: LIQUID20_DEPLOY_IDENTITY_AND_HOST_PATH_MISMATCH
  evidence: The controlled collector run failed before image deployment because LIQUID20_PUID was missing, the runner-visible state root was not the Docker-host bind root, and the live data directory had not been safely bootstrapped.
rejected_hypotheses:
  - The accepted historical Liquid20 evidence was defective; it remains valid and immutable.
  - Portal polling every ten seconds implied fresh market data; it only refreshed the historical read result.
  - Running the collector as root was an acceptable workaround; the deployment contract requires a non-root runtime.
  - Runner-visible filesystem paths could be used directly as Docker-host bind paths.
changed_paths:
  - deploy/synology/liquid20/deploy-live.sh
  - deploy/synology/liquid20/LIVE_STREAM.md
  - tests/ai_platform_integration/test_synology_liquid20_live_deployment.py
  - docs/agents/tasks/FTAI-20260727-liquidations-live-stream-repair.md
validation:
  - command: GitHub Freqtrade CI run 30299336099 on 01e5bd2eb331b9273f269a7617e95fbbd51611a1
    result: PASS
    evidence: Full Linux matrix, distribution build and CI Gate completed successfully.
  - command: GitHub zizmor run 30299336054 on 01e5bd2eb331b9273f269a7617e95fbbd51611a1
    result: PASS
    evidence: Security analysis completed successfully.
  - command: PR #510 inline review-thread query
    result: PASS
    evidence: No review threads were returned.
  - command: Compare develop with fix/liquidations-live-synology-identity-paths-20260727
    result: FAIL
    evidence: Branch is diverged, seven commits ahead and two commits behind current develop; GitHub reports the PR non-mergeable.
  - command: python tools/agents/checkpoint.py docs/agents/tasks/FTAI-20260727-liquidations-live-stream-repair.md --require-checkpoint
    result: PASS
    evidence: Compact checkpoint contract validated locally before handoff.
blockers:
  - PR #510 is behind current develop by two commits and GitHub currently reports mergeable=false.
  - Controlled Synology collector deployment and operational JSON evidence have not been rerun after the repair.
next_action: Merge current develop head 1f89f6f566525894b785a8488698cf605398e593 into PR #510, resolve only task-owned conflicts, rerun exact-head CI and review-thread checks, and merge only if green before triggering the controlled Synology collector deployment.
```
