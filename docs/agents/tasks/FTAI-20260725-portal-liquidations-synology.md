---
task_id: FTAI-20260725-portal-liquidations-synology
status: reviewing
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
updated_at: 2026-07-26T06:30:00Z
head: 8ec78c8e77cb7bfdba123efe10f5ac75cbbb344e
branch: feat/portal-liquidations-synology-20260725
pr: 313
status: reviewing
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
  - The authoritative Liquid20 root is /volume1/docker/freqtrade-liquidations/data and is mounted at /liquid20-data read-only.
  - Liquid20 directories are root:root mode 750 and event files are root:root mode 640.
  - The deployment derives and validates the shared numeric read GID through a root-only metadata preflight container, then adds only that supplementary group to the non-root Node process.
  - Host permissions and Liquid20 evidence contents remain unchanged.
  - Exact feature commit e48c421aea4adb46854578264d80622803498a87 deployed successfully in workflow run 30191045808.
  - The exact deployment passed image build, isolated candidate health, real-data health, summary, bounded list and page probes, LAN probes on 192.168.1.2:3031 and final health-contract validation.
  - The running portal remains non-root, has no Docker socket mount, exposes no credentials and carries no trading authority.
  - The temporary feature-branch deployment trigger was removed after successful proof; authoritative future deployments run from develop only.
derived:
  - The final merge can preserve the existing running exact feature image until the develop deployment replaces it with the merge SHA.
unknown:
  - Final acceptance outcome of active run liquid20-20260725T212201Z-1; this is independent of portal integration completion.
conflicts: []
first_failure:
  marker: LIQUID20_GROUP_TRAVERSE
  evidence: Real-data candidate routes initially returned HTTP 500 with EACCES permission denied scandir /liquid20-data; permission diagnostics identified the required group-only access boundary.
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
    evidence: Non-root process included the verified group and health, summary, list and page all returned HTTP 200 against real data.
  - command: exact feature deployment run 30191045808
    result: PASS
    evidence: Build and deploy, LAN Liquid20 surface and final status all completed successfully for e48c421aea4adb46854578264d80622803498a87.
blockers: []
next_action: Complete final PR checks, verify review threads remain empty, squash-merge PR 313 and verify the authoritative develop deployment.
```
