---
task_id: FTAI-20260725-portal-liquidations-synology
status: completed
branch: feat/portal-liquidations-synology-20260725
base_branch: develop
created: 2026-07-25
updated: 2026-07-26
related_pr: "#313"
owned_paths:
  - .github/workflows/portal-synology-lan-preview.yml
  - deploy/synology/portal/
  - docs/agents/tasks/FTAI-20260725-portal-liquidations-synology.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260725-portal-synology-lan-staging.md
  - docs/agents/tasks/FTAI-20260725-portal-liquidations-read-model.md
  - docs/agents/tasks/FTAI-20260725-portal-liquidations-ui.md
  - docs/ai_platform/portal/LIQUIDATIONS_AND_AI_BOT_ARCHITECTURE.md
search_first:
  - current Synology preview workflow, running image, Liquid20 collector and newest acceptance evidence
optional_reads: []
---

# Portal Liquidations Synology integration

## Goal

Mount the authoritative Liquid20 Synology evidence directory read-only into the existing private-LAN portal preview, validate the BFF and Likwidacje page against real data, and preserve exact-SHA candidate health, rollback and port 3031.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-26T07:04:00Z
head: 1bf106fb5919706cca4db4f8245e00d2a1932df9
branch: develop
pr: 313
status: completed
context_routes:
  - docs/ai_platform/portal/LIQUIDATIONS_AND_AI_BOT_ARCHITECTURE.md
  - docs/agents/tasks/FTAI-20260725-portal-synology-lan-staging.md
  - docs/agents/tasks/FTAI-20260725-portal-liquidations-read-model.md
  - docs/agents/tasks/FTAI-20260725-portal-liquidations-ui.md
owned_paths:
  - .github/workflows/portal-synology-lan-preview.yml
  - deploy/synology/portal/deploy-preview.sh
  - deploy/synology/portal/README.md
  - docs/agents/tasks/FTAI-20260725-portal-liquidations-synology.md
proven:
  - PR 307 read-model merged to develop as aa2f193b970588e478b5d57f58d2ddfd7f4aab67.
  - PR 311 BFF and UI merged to develop as 228b5ad3eb12c6adab300ab86461d3fa67acaa47.
  - PR 313 Synology integration merged to develop as 1bf106fb5919706cca4db4f8245e00d2a1932df9.
  - The authoritative Liquid20 root is mounted from /volume1/docker/freqtrade-liquidations/data to /liquid20-data read-only.
  - The deployment validates regular non-symlinked paths, group-readable files and one consistent numeric read GID through the Synology Docker daemon.
  - The portal process remains non-root and receives only the verified supplementary read group required by the root:root 750/640 evidence tree.
  - Host permissions and Liquid20 evidence contents remain unchanged.
  - The portal container has no Docker socket mount, exposes no credentials and carries no trading authority.
  - The feature candidate e48c421aea4adb46854578264d80622803498a87 passed real-data deployment run 30191045808.
  - The authoritative develop commit 1bf106fb5919706cca4db4f8245e00d2a1932df9 passed deployment run 30191687921.
  - Build, isolated candidate, health, summary, bounded list, page and private-LAN probes all passed on 192.168.1.2:3031.
  - Automatic Synology deployment is restricted to develop after the feature proof.
derived:
  - The portal integration is terminal and independent of the Liquid20 acceptance decision.
  - Every future task must reverify the current running image, collector and newest run because they are mutable runtime facts.
unknown:
  - Final acceptance outcome of active run liquid20-20260725T212201Z-1; this does not block or reopen the completed portal integration.
conflicts: []
first_failure:
  marker: LIQUID20_GROUP_TRAVERSE
  evidence: Real-data candidate routes initially returned HTTP 500 with EACCES permission denied scandir /liquid20-data; permission diagnostics identified the required group-only access boundary.
rejected_hypotheses:
  - Run the portal container as root.
  - Change or recursively chmod the immutable Liquid20 evidence tree.
  - Copy evidence into a writable portal directory.
  - Mount the Docker socket or expose collector files directly.
  - Treat the HTTP 500 as a read-model schema or route failure.
changed_paths:
  - .github/workflows/portal-synology-lan-preview.yml
  - deploy/synology/portal/deploy-preview.sh
  - deploy/synology/portal/README.md
  - docs/agents/tasks/FTAI-20260725-portal-liquidations-synology.md
validation:
  - command: isolated real-data candidate without supplementary group
    result: FAIL_EXPECTED
    evidence: Image and read-only mount were valid, page returned 200, and all read-model endpoints returned 500 with EACCES scandir.
  - command: permission metadata diagnostic run 30178732843
    result: PASS
    evidence: Root, run directories and event files consistently use uid 0, gid 0 with directory mode 750 and file mode 640.
  - command: supplementary-group candidate run 30178801452
    result: PASS
    evidence: Non-root process included the verified group and health, summary, list and page all returned HTTP 200 against real data.
  - command: exact feature deployment run 30191045808
    result: PASS
    evidence: Build and deploy, LAN Liquid20 surface and final status all completed successfully for e48c421aea4adb46854578264d80622803498a87.
  - command: PR 313 final CI
    result: PASS
    evidence: Freqtrade CI, documentation, all Linux/Python core tests and zizmor completed successfully for 33c4d3b139ea16d14b8eb57568a71f822dce506c.
  - command: authoritative develop deployment run 30191687921
    result: PASS
    evidence: Build and deploy, real-data LAN Liquid20 surface and final status all completed successfully for 1bf106fb5919706cca4db4f8245e00d2a1932df9.
blockers: []
next_action: none
```
