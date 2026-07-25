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
updated_at: 2026-07-25T20:43:00+02:00
head: 6f377a9e61abb8320b5c19ddec8641a43bca6e26
branch: feat/portal-synology-lan-staging
pr: 284
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
  - Portal web supports explicit fixture mode and standalone Next.js output.
  - One-shot deployment run 30169834793 built the exact source, validated an isolated candidate and deployed a healthy final container.
  - Permanent workflow run 30169930641 passed exact-SHA build, candidate health, final health and the LAN HTTP probe at 192.168.1.2:3000.
  - The running preview is fixture-only and exposes no Freqtrade REST or WebSocket endpoint.
derived:
  - A local exact-SHA image built through the dedicated runner provides a reproducible LAN preview without GHCR credentials or an SSH launcher.
  - The Synology kernel requires memory and PID limits without Docker CPU CFS quota flags.
unknown:
  - Whether all required pull-request checks pass on the final checkpoint head.
conflicts: []
first_failure:
  marker: SYNOLGY_CPU_CFS_UNAVAILABLE
  evidence: Initial candidate creation returned Docker exit 125 because NanoCPUs cannot be set when the Synology kernel lacks CPU CFS scheduler support; removing only --cpus resolved the failure while preserving the other container restrictions.
rejected_hypotheses:
  - Expose the Freqtrade REST or WebSocket API directly to the browser or LAN.
  - Treat fixture-mode LAN preview as production-like Cloudflare staging evidence.
  - Retain --cpus after the host daemon proved CPU CFS quota unsupported.
  - Keep temporary one-shot, runner-probe or diagnostic files after successful deployment.
changed_paths:
  - .github/workflows/portal-synology-lan-preview.yml
  - deploy/synology/portal/Dockerfile
  - deploy/synology/portal/README.md
  - deploy/synology/portal/deploy-preview.sh
  - ai_platform/portal/web/.dockerignore
  - docs/agents/tasks/FTAI-20260725-portal-synology-lan-staging.md
validation:
  - command: Freqtrade Synology Runner Smoke run 30168583394
    result: PASS
    evidence: Runner accepted the job and validated Docker access, a disposable container and the persistent state bind.
  - command: One-shot Portal Synology LAN Deploy run 30169834793
    result: PASS
    evidence: Exact source built successfully; candidate and final containers became healthy on the dedicated Synology runner.
  - command: Portal Synology LAN Preview run 30169930641
    result: PASS
    evidence: Build, candidate health, final deployment and direct LAN HTTP probe all passed.
  - command: PR 284 checks on implementation head 6f377a9e61abb8320b5c19ddec8641a43bca6e26
    result: IN_PROGRESS
    evidence: AI Platform CI, Portal Web CI, Portal Universal E2E and zizmor passed; Freqtrade CI remained in progress when this checkpoint was written.
blockers: []
next_action: Wait for all required checks on PR 284 to pass on the checkpoint commit, then mark the PR ready and merge it to develop without changing the proven LAN fixture boundary.
```
