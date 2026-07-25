---
task_id: FTAI-20260725-portal-synology-lan-staging
status: active
branch: feat/portal-synology-lan-staging
base_branch: develop
created: 2026-07-25
updated: 2026-07-25
---

# Synology portal LAN staging

Deploy the existing AI Trading Portal web application to the user's private Synology LAN through the dedicated `freqtrade-staging` self-hosted runner.

This task delivers a fixture-backed product preview only. It does not expose Freqtrade, add exchange credentials, enable live capital, configure Cloudflare, or claim production-like staging acceptance.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-25T20:10:00+02:00
head: 1dca945834b7f2c5e3bb7974649501af1ae35604
branch: feat/portal-synology-lan-staging
pr: null
status: validating
context_routes:
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/README.md
  - docs/ai_platform/portal/PRODUCTION_LIKE_STAGING.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
owned_paths:
  - .github/workflows/portal-synology-lan-preview.yml
  - deploy/synology/portal/
  - ai_platform/portal/web/.dockerignore
  - docs/agents/tasks/FTAI-20260725-portal-synology-lan-staging.md
proven:
  - Dedicated repository runner freqtrade-synology-staging is online with custom label freqtrade-staging.
  - Runner smoke workflow run 30168583394 passed Docker, Compose, Docker socket, disposable container and staging-state mount checks.
  - User approved private-LAN port 3000 and requested no Tunnel or SSH deployment path.
  - Portal web already supports explicit fixture mode and standalone Next.js output.
derived:
  - An exact-SHA GHCR image built on GitHub-hosted infrastructure can be validated and deployed by the lightweight Synology runner without building on the NAS.
unknown:
  - Whether the exact-SHA portal image builds successfully from the current web tree.
  - Whether Synology can bind 192.168.1.2:3000 and the final container becomes healthy.
conflicts: []
first_failure:
  marker: NONE
  evidence: Deployment workflow has been dispatched by the feature-branch push and has not yet published its final commit status.
rejected_hypotheses:
  - Expose the Freqtrade REST or WebSocket API directly to the browser or LAN.
  - Treat fixture-mode LAN preview as production-like Cloudflare staging evidence.
  - Build the portal image on the Synology CPU when GitHub-hosted build infrastructure is available.
changed_paths:
  - .github/workflows/portal-synology-lan-preview.yml
  - deploy/synology/portal/Dockerfile
  - deploy/synology/portal/README.md
  - ai_platform/portal/web/.dockerignore
  - docs/agents/tasks/FTAI-20260725-portal-synology-lan-staging.md
validation:
  - command: Freqtrade Synology Runner Smoke run 30168583394
    result: PASS
    evidence: Runner accepted the job and validated Docker access, a disposable container and the persistent state bind.
blockers: []
next_action: Read the portal-synology-lan-preview commit status for the latest branch head; fix the first deterministic failure if present, otherwise verify the LAN endpoint and open a PR to develop.
```
