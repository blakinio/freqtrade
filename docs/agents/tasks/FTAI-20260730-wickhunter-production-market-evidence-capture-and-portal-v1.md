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
  - ai_platform/portal/web/e2e/specs/market-evidence*.spec.ts
  - ai_platform/portal/web/fixtures/market-evidence/**
  - deploy/synology/wickhunter-market-evidence/**
  - deploy/synology/portal/deploy-market-evidence-preview.sh
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
updated_at: 2026-07-30T10:24:00+02:00
head: d68da6d1ae27d3dc7113ce162931e22721c6250d
branch: agent/wickhunter-production-market-evidence-capture-v1
pr: 753
status: validating
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_WICKHUNTER_LIQUIDATION_BOT_PROGRAM.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/WICKHUNTER_PRODUCTION_MARKET_EVIDENCE.md
  - docs/ai_platform/portal/MARKET_EVIDENCE_READ_MODEL.md
owned_paths:
  - ai_platform/wickhunter/**
  - ai_platform/portal/web/app/api/market/evidence/**
  - ai_platform/portal/web/app/market/evidence/**
  - ai_platform/portal/web/components/market-evidence-*
  - ai_platform/portal/web/lib/market-evidence/**
  - ai_platform/portal/web/e2e/specs/market-evidence*.spec.ts
  - ai_platform/portal/web/fixtures/market-evidence/**
  - deploy/synology/wickhunter-market-evidence/**
  - deploy/synology/portal/deploy-market-evidence-preview.sh
  - docs/ai_platform/WICKHUNTER_PRODUCTION_MARKET_EVIDENCE.md
  - docs/ai_platform/portal/MARKET_EVIDENCE_READ_MODEL.md
  - docs/agents/tasks/FTAI-20260730-wickhunter-production-market-evidence-capture-and-portal-v1.md
proven:
  - The feature branch was synchronized normally with develop through merge PR 757 without force-push and remains zero commits behind develop.
  - The collector captures source-separated public Binance USD-M and Bybit Linear market quality and completed 5m candles with a versioned 24h pre-roll.
  - The publication service writes historical instrument and source-health snapshots and atomically publishes a hash-verified immutable package without overwriting a closed package.
  - The persistent daemon and hardened Synology Compose definition use non-root execution, a read-only root filesystem, dropped capabilities, no-new-privileges, bounded resources, durable state, no host network, no public port and no exchange credentials.
  - The WH-01 adapter verifies both evidence layers, binds only real accepted liquidation imports, enforces as-of metric availability and existing materialization preflight, and remains blocked when a liquidation archive is not bound.
  - The Portal includes tenant-safe read-only summary, source, instrument and run APIs plus the full Market Evidence page, exact blocker rendering, capability-separated source cards, filters, pagination, run details and no trading path.
  - Browser coverage includes identity, source status, instrument filtering, run details, blocker display, cross-tenant denial, bounded responses and loading, empty, stale, unavailable and error component states.
  - Documentation covers architecture, immutable format, pre-roll, availability, restart and recovery, WH-01 integration, API, UI, status codes, Synology deployment and authority boundaries.
derived:
  - The repository implementation is complete enough for exact-head backend, Portal, browser, deployment, documentation and checkpoint validation.
  - A matching accepted liquidation archive must still be bound after a real completed capture before WH-01 materialization can become ready.
unknown:
  - Exact failures, if any, from the first dedicated market-evidence CI run on the complete implementation head.
conflicts: []
first_failure:
  marker: exact_head_ci_not_yet_executed
  evidence: The dedicated workflow was added on the feature branch and requires a child validation PR so GitHub evaluates it from a base branch that already contains the workflow definition.
rejected_hypotheses:
  - Treat OKX liquidation availability as equivalent to complete WH-01 candle evidence.
  - Expose durable host paths, raw exchange payloads, credentials or mutation controls through the Portal.
  - Modify WH-01 or its materialization operator to accept missing or synthetic evidence.
  - Backdate current instrument state or use a later candle, ticker or liquidation event for an earlier decision.
changed_paths:
  - .github/workflows/ai-platform-wickhunter-market-evidence-ci.yml
  - .github/workflows/ai-platform-wickhunter-production-market-evidence.yml
  - ai_platform/wickhunter/production_market_evidence.py
  - ai_platform/wickhunter/production_market_evidence_service.py
  - ai_platform/wickhunter/production_market_evidence_daemon.py
  - ai_platform/wickhunter/production_market_evidence_wh01.py
  - ai_platform/wickhunter/policies/wickhunter-production-market-evidence-wh01-policy-v1.json
  - ai_platform/portal/web/app/api/market/evidence/**
  - ai_platform/portal/web/app/market/evidence/page.tsx
  - ai_platform/portal/web/components/market-evidence-dashboard.tsx
  - ai_platform/portal/web/components/market-evidence-dashboard.module.css
  - ai_platform/portal/web/components/app-shell.tsx
  - ai_platform/portal/web/lib/market-evidence/**
  - ai_platform/portal/web/e2e/specs/market-evidence.spec.ts
  - ai_platform/portal/web/e2e/specs/market-evidence-states.spec.ts
  - ai_platform/portal/web/fixtures/market-evidence/**
  - deploy/synology/wickhunter-market-evidence/**
  - deploy/synology/portal/deploy-market-evidence-preview.sh
  - docs/ai_platform/WICKHUNTER_PRODUCTION_MARKET_EVIDENCE.md
  - docs/ai_platform/portal/MARKET_EVIDENCE_READ_MODEL.md
  - docs/ai_platform/portal/README.md
  - tests/ai_platform_integration/test_wickhunter_production_market_evidence_service.py
  - tests/ai_platform_integration/test_wickhunter_production_market_evidence_wh01.py
validation:
  - command: repository and ownership audit
    result: PASS
    evidence: develop was merged into the feature branch through PR 757 and no task-relevant open ownership conflict was found.
  - command: implementation review
    result: PASS
    evidence: backend, WH-01 adapter, Portal API, UI, E2E, deployment and documentation paths are present on head d68da6d1ae27d3dc7113ce162931e22721c6250d.
blockers: []
next_action: Run the dedicated exact-head validation PR, repair every failing backend, Portal, browser, deployment, documentation or checkpoint check, then fast-forward the feature branch to the proven head.
```
