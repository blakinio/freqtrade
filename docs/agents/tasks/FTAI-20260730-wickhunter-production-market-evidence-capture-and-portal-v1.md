---
task_id: FTAI-20260730-wickhunter-production-market-evidence-capture-and-portal-v1
status: active
branch: agent/wickhunter-production-market-evidence-capture-v1
base_branch: develop
created: 2026-07-30
updated: 2026-07-30
depends_on:
  - FTAI-20260729-wickhunter-production-market-evidence-capture-v1
owned_paths:
  - ai_platform/wickhunter/**
  - ai_platform/portal/web/app/api/market/evidence/**
  - ai_platform/portal/web/app/market/evidence/**
  - ai_platform/portal/web/components/market-evidence-*
  - ai_platform/portal/web/lib/market-evidence/**
  - ai_platform/portal/web/e2e/market-evidence.spec.ts
  - ai_platform/portal/web/fixtures/market-evidence/**
  - deploy/synology/portal/**
  - docs/ai_platform/WICKHUNTER_PRODUCTION_MARKET_EVIDENCE.md
  - docs/ai_platform/portal/MARKET_EVIDENCE_READ_MODEL.md
  - docs/agents/tasks/FTAI-20260730-wickhunter-production-market-evidence-capture-and-portal-v1.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_WICKHUNTER_LIQUIDATION_BOT_PROGRAM.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/README.md
---

# WickHunter production market evidence capture and Portal v1

## Goal

Complete the production market-evidence collector for source-separated Binance USD-M and Bybit Linear data, publish immutable verified evidence and expose its source, instrument, run and WH-01 readiness state through a tenant-safe read-only Portal surface. OKX remains truthfully represented as liquidation-only unless candle and quality evidence exists.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-30T09:16:00+02:00
head: e45ad28e0e8738a421b6d6da3e77f999e4d329f7
branch: agent/wickhunter-production-market-evidence-capture-v1
pr: 753
status: active
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_WICKHUNTER_LIQUIDATION_BOT_PROGRAM.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/README.md
owned_paths:
  - ai_platform/wickhunter/**
  - ai_platform/portal/web/app/api/market/evidence/**
  - ai_platform/portal/web/app/market/evidence/**
  - ai_platform/portal/web/components/market-evidence-*
  - ai_platform/portal/web/lib/market-evidence/**
  - ai_platform/portal/web/e2e/market-evidence.spec.ts
  - ai_platform/portal/web/fixtures/market-evidence/**
  - docs/ai_platform/portal/MARKET_EVIDENCE_READ_MODEL.md
  - docs/agents/tasks/FTAI-20260730-wickhunter-production-market-evidence-capture-and-portal-v1.md
proven:
  - PR 753 contains a prospective public-only collector for Binance USD-M and Bybit Linear with 24h pre-roll, completed 5m candles, exact raw bytes, source-separated market-quality snapshots and immutable hash verification.
  - The branch was 20 commits behind develop and was synchronized normally through merge PR 757 without force-push; current branch head is e45ad28e0e8738a421b6d6da3e77f999e4d329f7.
  - The existing Portal Liquid20 read model is server-side, read-only, bounded and symlink-safe, with same-origin routes and a responsive Likwidacje page.
  - No other open Portal or Liquid20 PR currently claims the task-relevant paths.
derived:
  - The existing collector can remain the acquisition core while an additive v2 service freezes instrument history, policy, source-health and Portal index artifacts and owns final publication.
  - The Portal should use a separate /market/evidence surface and /api/market/evidence read model while linking from the existing Market Data navigation.
unknown:
  - Exact CI failures after the first complete backend and Portal implementation commit set.
conflicts: []
first_failure:
  marker: local_repository_clone_unavailable
  evidence: The execution sandbox cannot resolve github.com; repository reads, writes, review and CI use the authenticated GitHub connector.
rejected_hypotheses:
  - Treat OKX liquidation availability as equivalent to complete WH-01 candle evidence.
  - Expose durable host paths, raw exchange payloads, credentials or mutation controls through the Portal.
  - Modify WH-01 to accept incomplete or synthetic evidence.
changed_paths:
  - docs/agents/tasks/FTAI-20260730-wickhunter-production-market-evidence-capture-and-portal-v1.md
validation:
  - command: repository preflight and ownership audit
    result: PASS
    evidence: develop 7240762e134d8db42b83030491ae52ec0d02cad6 was merged into the feature branch through PR 757; PR 753 is open and mergeable.
blockers: []
next_action: Implement the additive collector publication service and its focused fail-closed tests, then continue immediately with the Portal read model and UI on the same branch.
```
