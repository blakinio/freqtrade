---
task_id: FTAI-20260727-portal-synology-identity-runtime-diagnostic
status: diagnostic
branch: diag/portal-synology-identity-runtime-20260727
base_branch: develop
created: 2026-07-27
updated: 2026-07-27
owned_paths:
  - .github/workflows/diag-portal-synology-identity-runtime.yml
  - docs/agents/tasks/FTAI-20260727-portal-synology-identity-runtime-diagnostic.md
---

# Portal Synology identity runtime diagnostic

Temporary non-mergeable diagnostic for the running `freqtrade-portal-staging` container. It records only the image/revision, published port, presence or non-sensitive values of four known portal configuration fields, matching Next.js route names, and bounded HTTP status/error excerpts. It performs no container, network, volume, file or identity mutation and must be closed after the artifact is captured.
