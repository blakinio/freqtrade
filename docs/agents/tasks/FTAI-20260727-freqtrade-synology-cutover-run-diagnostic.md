---
task_id: FTAI-20260727-freqtrade-synology-cutover-run-diagnostic
status: diagnostic
branch: diag/freqtrade-synology-cutover-3127b182
base_branch: develop
created: 2026-07-27
updated: 2026-07-27
owned_paths:
  - .github/workflows/diag-freqtrade-synology-cutover-run.yml
  - docs/agents/tasks/FTAI-20260727-freqtrade-synology-cutover-run-diagnostic.md
---

# Failed Synology cutover push-run diagnostic

Temporary pull-request-only diagnostic. It runs on GitHub-hosted infrastructure, reads the exact Actions push run for merge commit `3127b1826d6e0827be6e1636ee5745d75583d9a3`, extracts bounded failure evidence and posts it to PR 509. It does not access or mutate Synology directly and must not be merged.
