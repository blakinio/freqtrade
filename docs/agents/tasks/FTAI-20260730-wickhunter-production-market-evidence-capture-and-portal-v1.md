---
task_id: FTAI-20260730-wickhunter-production-market-evidence-capture-and-portal-v1
status: completed
branch: agent/wickhunter-production-market-evidence-capture-v1
base_branch: develop
created: 2026-07-30
updated: 2026-07-30
related_pr: 753
validation_pr: 763
repair_pr: 766
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
updated_at: 2026-07-30T11:52:00+02:00
head: dd8595fe7a2d3559340d46d9c2b43e05aabbd0e0
validated_code_head: dd8595fe7a2d3559340d46d9c2b43e05aabbd0e0
feature_head: 40571ec7f9ec5eb590226cffc20de0fef72cb2a9
feature_merge: 0208666d98849386e2f2d9acf534b13891e4afa2
merged_commit: ac545041046e618c477e0ab5d999e11d261a742e
develop_head: ac545041046e618c477e0ab5d999e11d261a742e
branch: agent/wickhunter-production-market-evidence-capture-v1
repair_branch: fix/wickhunter-ruff-baseline-20260730
pr: 753
auxiliary_pr: 763
repair_pr: 766
status: ready
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_WICKHUNTER_LIQUIDATION_BOT_PROGRAM.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/WICKHUNTER_PRODUCTION_MARKET_EVIDENCE.md
  - docs/ai_platform/portal/MARKET_EVIDENCE_READ_MODEL.md
  - docs/ai_platform/portal/README.md
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
  - Current develop, PR heads, AGENTS.md, task ownership, reviews, review threads and exact workflow results were re-fetched before final integration.
  - PR 763 merged the intended validation corrections into the feature head 40571ec7f9ec5eb590226cffc20de0fef72cb2a9 without introducing substitute public contracts.
  - PR 753 merged the bounded collector, immutable publication, WH-01 adapter, tenant-safe Portal read model and UI, documentation and hardened deployment definitions as 0208666d98849386e2f2d9acf534b13891e4afa2.
  - Source-separated Binance USD-M and Bybit Linear evidence uses completed 5m candles, a versioned 24h pre-roll and explicit event, close and availability timestamps while OKX remains liquidation-only.
  - Publication rejects overwrite, symlinks, path traversal, non-regular or oversized files, malformed geometry, tampering, missing artifacts and inconsistent identities and publishes atomically.
  - WH-01 verifies both immutable layers, uses adjacent-candle pairing, enforces as-of availability and remains truthfully blocked until an accepted liquidation archive and split geometry are bound.
  - Portal APIs and the /market/evidence UI are read-only, tenant-safe, bounded and expose no credentials, raw exchange payloads, host paths, mutation controls or trading actions.
  - Synology definitions run non-root with read-only filesystems where supported, dropped capabilities, no-new-privileges, no host networking, no unintended ports, read-only evidence mounts and durable state only where required.
  - Repair head dd8595fe7a2d3559340d46d9c2b43e05aabbd0e0 passed AI Platform CI 30530887717, Portal Web CI 30530887753, Portal Universal E2E 30530887777, WickHunter Market Evidence CI 30530887721, Freqtrade CI 30530887788 and zizmor 30530887747.
  - The final Freqtrade matrix passed Python 3.11, 3.12 coverage, 3.13, 3.14, generated-file checks, backtesting and hyperopt smoke tests, Ruff, Ruff format, MyPy, distribution build, pre-commit and CI Gate.
  - PR 766 had no unresolved blocking review thread and merged the exact validated repair head to develop as ac545041046e618c477e0ab5d999e11d261a742e.
  - execution_enabled, orders_submitted, trading_credentials_present, model_execution_authorized, replay_authorized, performance_research_authorized and live_capital_authorized remain false.
derived:
  - Repository-side implementation, validation, review, merge and deployment-definition acceptance are complete.
  - A real immutable production package cannot truthfully exist before the frozen decision interval ends at 2026-07-31T18:00:00Z.
  - WH-01 readiness remains a typed external-data blocker rather than a repository defect or fabricated readiness claim.
unknown:
  - Whether the approved freqtrade-synology-staging runner and durable state root will be available for the future capture window.
  - The identity, hashes and record counts of the future accepted production package and liquidation archive.
conflicts: []
first_failure:
  marker: post_merge_exact_head_validation_regressions
  evidence: Original PR 753 validation exposed ten Ruff findings, five MyPy object-to-int errors, one symlink-message regression, one Playwright strict-locator collision and one stale Liquid20 restart assertion; PR 766 repaired root causes without weakening security checks.
rejected_hypotheses:
  - Retry deterministic CI failures without a code or test correction.
  - Weaken symlink, traversal, tamper, availability, tenant, pagination or deployment-security assertions to obtain green CI.
  - Treat OKX liquidation-only capability as complete candle and quality evidence.
  - Treat a future or absent production capture as a completed immutable package.
  - Enable replay, model execution, performance research, order execution, trading credentials or live-capital authority.
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
  - tests/ai_platform_integration/test_wickhunter_production_market_evidence.py
  - tests/ai_platform_integration/test_wickhunter_production_market_evidence_service.py
  - tests/ai_platform_integration/test_wickhunter_production_market_evidence_wh01.py
  - tests/ai_platform_integration/test_synology_liquid20_live_deployment.py
validation:
  - command: python compileall plus focused WickHunter pytest, Ruff, Ruff format and checkpoint validation
    result: PASS
    evidence: WickHunter Market Evidence CI run 30530887721 passed all backend collector, immutable-package, WH-01, path, symlink, tamper, leakage, restart and publication checks on dd8595fe7a2d3559340d46d9c2b43e05aabbd0e0.
  - command: npm ci; npm run typecheck; npm run lint; npm run build; focused Playwright market-evidence tests
    result: PASS
    evidence: Portal Web CI 30530887753, Portal Universal E2E 30530887777 and the Portal job in 30530887721 passed on the exact validated head.
  - command: py_compile deployment helpers; bash -n; docker compose config --quiet; hardened Compose assertions
    result: PASS
    evidence: Hardened deployment definitions job in WickHunter Market Evidence CI 30530887721 passed on the exact validated head.
  - command: pre-commit run --all-files
    result: PASS
    evidence: Full pre-commit passed during repair and the Pre-commit checks job in Freqtrade CI 30530887788 passed on the exact validated head.
  - command: Freqtrade Python 3.11-3.14 matrix, coverage, generated files, smoke tests, Ruff, format, MyPy and distributions
    result: PASS
    evidence: Freqtrade CI 30530887788 and CI Gate passed on dd8595fe7a2d3559340d46d9c2b43e05aabbd0e0.
  - command: GitHub Actions security analysis with zizmor
    result: PASS
    evidence: Run 30530887747 passed and all previous temporary-workflow findings are resolved and outdated.
  - command: final PR review, exact-head merge and develop verification
    result: PASS
    evidence: PR 766 merged exact head dd8595fe7a2d3559340d46d9c2b43e05aabbd0e0 as ac545041046e618c477e0ab5d999e11d261a742e, which is current develop.
blockers:
  - Exact blocker: the frozen decision interval does not end until 2026-07-31T18:00:00Z; evidence: the policy documentation fixes that end time; repository resolution is impossible because future exchange observations must not be fabricated; next action: the scheduled collector must complete the real interval; owner: approved capture runner and operator.
  - Exact blocker: the canonical exact-one-file capture request is not present on develop; evidence: the configured request path returns absent; repository completion does not authorize initializing a future external run; next action: an authorized operator must open the canonical request-only PR before 2026-07-31T06:00:00Z; owner: capture operator.
  - Exact blocker: no matching accepted liquidation archive is bound; evidence: WH-01 preflight returns a typed blocker; repository code cannot manufacture accepted liquidation evidence; next action: independently verify and bind an eligible immutable archive after capture; owner: evidence operator.
next_action: Before 2026-07-31T06:00:00Z, an authorized operator must open the exact-one-file canonical request PR and confirm the approved freqtrade-synology-staging runner and durable state; after 2026-07-31T18:00:00Z, independently verify and publish the real immutable capture, bind only an accepted liquidation archive and rerun WH-01 preflight without changing any authority flag.
```
