---
task_id: FTAI-20260728-wickhunter-wh06-portal-risk-seam
status: completed
branch: feat/wickhunter-wh06-portal-risk-seam-v1
base_branch: develop
created: 2026-07-28
updated: 2026-07-28
related_pr: 588
depends_on:
  - FTAI-20260727-wickhunter-wh00-contracts-vertical-slice
owned_paths:
  - ai_platform/wickhunter/portal_risk.py
  - ai_platform/wickhunter/__init__.py
  - tests/ai_platform_integration/test_wickhunter_portal_risk.py
  - docs/ai_platform/WICKHUNTER_PORTAL_RISK_INTEGRATION.md
  - docs/agents/programs/FTAI_WICKHUNTER_LIQUIDATION_BOT_PROGRAM.md
  - docs/agents/tasks/FTAI-20260728-wickhunter-wh06-portal-risk-seam.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_WICKHUNTER_LIQUIDATION_BOT_PROGRAM.md
  - docs/ai_platform/portal/README.md
  - docs/ai_platform/portal/RISK_ENGINE_FOUNDATION.md
  - ai_platform/portal/contracts/risk.py
  - ai_platform/portal/risk/schema.py
  - ai_platform/portal/risk/service.py
---

# WH-06 portal Risk Engine and TradeIntent seam

## Goal

Map an already locally allowed `WickHunterTradeIntent` into the existing canonical portal `TradeIntent` and `RiskEvaluationSnapshot`, validate canonical approved/rejected result evidence and persist an atomic immutable audit bundle without changing portal contracts or activating any execution/order adapter.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-28T11:10:00+02:00
validated_code_head: 4f26bddb5d387931eee07b48f1f67f8186f734a3
branch: feat/wickhunter-wh06-portal-risk-seam-v1
pr: 588
status: completed
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_WICKHUNTER_LIQUIDATION_BOT_PROGRAM.md
  - docs/ai_platform/portal/README.md
  - docs/ai_platform/portal/RISK_ENGINE_FOUNDATION.md
owned_paths:
  - ai_platform/wickhunter/portal_risk.py
  - ai_platform/wickhunter/__init__.py
  - tests/ai_platform_integration/test_wickhunter_portal_risk.py
  - docs/ai_platform/WICKHUNTER_PORTAL_RISK_INTEGRATION.md
  - docs/agents/programs/FTAI_WICKHUNTER_LIQUIDATION_BOT_PROGRAM.md
  - docs/agents/tasks/FTAI-20260728-wickhunter-wh06-portal-risk-seam.md
proven:
  - WH-00 and WH-01 are merged and completed.
  - WH-02 remains blocked on a real accepted immutable historical dataset.
  - Portal P7 already provides canonical TradeIntent, RiskEvaluationSnapshot, RiskDecision and approved/rejected execution-intent contracts.
  - The current portal service exposes a manual-intent flow and is not reused as an autonomous strategy submission path.
  - Current open BM-05 work owns grid_control paths and does not overlap this WickHunter-only package.
  - Current open ASE-00 work owns ai_strategy_engine paths and does not overlap this package.
  - The package maps only locally allowed WickHunter evidence, rejects production structurally and calls no execution adapter.
  - The mapped notional conservatively includes the larger of base risk and bounded total DCA risk before leverage.
  - Request and result identities are deterministic and terminal evidence is written atomically without overwrite.
  - Exact code head 4f26bddb5d387931eee07b48f1f67f8186f734a3 passed AI Platform CI, full Freqtrade CI and security analysis.
  - Pre-commit, Python 3.11 through 3.14, coverage, documentation, smoke tests, Ruff, Ruff format, mypy, distribution build and CI Gate passed.
derived:
  - WH-06 can progress independently of the real-history WH-02 gate because its declared dependency is WH-00 plus a frozen portal seam.
  - Shared portal, bot-management, execution, database, migration and browser paths require separate ownership and remain untouched.
  - A local WickHunter rejection is a terminal veto and cannot be overridden by the portal bridge.
unknown:
  - The future runtime-owned mechanism that invokes the canonical portal risk authority remains outside WH-06 and requires its own ownership package.
conflicts: []
first_failure:
  gate: AI Platform CI Ruff
  run_id: 30342077738
  job_id: 90219712229
  cause: Import ordering and static formatting required the repository-pinned Ruff 0.15.21 repair.
  resolution: Captured and applied exact Ruff check --fix and Ruff format diffs, removed all temporary diagnostic workflows, then passed exact-head CI.
rejected_hypotheses:
  - Call RiskService.evaluate_manual_intent from WickHunter.
  - Import or call ExecutionAdapter.submit_approved_intent.
  - Add a browser or BFF route.
  - Modify portal risk contracts, migrations or bot-management paths.
  - Allow production or live-capital evidence.
changed_paths:
  - ai_platform/wickhunter/portal_risk.py
  - ai_platform/wickhunter/__init__.py
  - tests/ai_platform_integration/test_wickhunter_portal_risk.py
  - docs/ai_platform/WICKHUNTER_PORTAL_RISK_INTEGRATION.md
  - docs/agents/programs/FTAI_WICKHUNTER_LIQUIDATION_BOT_PROGRAM.md
  - docs/agents/tasks/FTAI-20260728-wickhunter-wh06-portal-risk-seam.md
validation:
  - command: AI Platform CI
    result: PASS
    evidence: Exact code head run 30344402321, including compile, all AI-platform tests, Ruff, format, codespell and JSON validation.
  - command: Freqtrade CI
    result: PASS
    evidence: Exact code head run 30344402267, including pre-commit, Python 3.11-3.14, coverage, docs, smoke tests, mypy, distribution build and CI Gate.
  - command: GitHub Actions Security Analysis with zizmor
    result: PASS
    evidence: Exact code head run 30344402256.
blockers: []
next_action: Keep WH-02 gated until a real accepted immutable historical import exists, then open a fresh WH-02 task from current develop. WH-07 remains dependency-blocked on WH-02 through WH-05.
```
