---
task_id: FTAI-20260725-portal-liquidations-synology
status: implementing
branch: feat/portal-liquidations-synology-20260725
base_branch: develop
created: 2026-07-25
updated: 2026-07-25
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
search_first:
  - current Synology preview workflow and Liquid20 issue 148
optional_reads: []
---

# Portal Liquidations Synology integration

## Goal

Mount the authoritative Liquid20 Synology evidence directory read-only into the existing private-LAN portal preview, validate the BFF and Likwidacje page against real data, and preserve exact-SHA candidate health, rollback and port 3031.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-25T23:15:00Z
head: pending-feature-validation
branch: feat/portal-liquidations-synology-20260725
pr: 313
status: implementing
context_routes:
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
  - The private Synology portal preview remains bound to 192.168.1.2:3031 with exact-SHA images, isolated candidate validation and rollback.
  - The authoritative Liquid20 root is /volume1/docker/freqtrade-liquidations/data and is mountable read-only through the Synology Docker daemon.
  - Liquid20 directories are root:root mode 750 and event files are root:root mode 640; the image's non-root Node user cannot traverse them without a supplementary group.
  - Isolated run 30178801452 proved that adding only supplementary GID 0 keeps the process non-root and returns HTTP 200 for health, summary, bounded list and page against real Liquid20 data.
  - The portal container does not require or receive the Docker socket, exchange credentials or trading authority.
derived:
  - The deployment must derive and validate the numeric read GID through a short root-only metadata preflight container, then add only that GID to the non-root portal process.
  - Host permissions and Liquid20 evidence contents must remain unchanged.
unknown:
  - Final acceptance outcome of active run liquid20-20260725T212201Z-1.
conflicts: []
first_failure:
  marker: LIQUID20_GROUP_TRAVERSE
  evidence: Real-data candidate routes returned HTTP 500 with EACCES permission denied scandir /liquid20-data; permission diagnostics showed root:root 750 directories and root:root 640 event files.
rejected_hypotheses:
  - Run the portal container as root.
  - Change or recursively chmod the immutable Liquid20 evidence tree.
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
    evidence: Non-root process included GID 0 and health, summary, list and page all returned HTTP 200 against real data.
blockers: []
next_action: Deploy the clean exact-SHA feature candidate with dynamically verified group-only access, remove the temporary feature-branch trigger after proof, then merge and verify the develop deployment.
```
