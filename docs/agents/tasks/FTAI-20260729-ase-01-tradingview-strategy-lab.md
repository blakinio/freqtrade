---
task_id: FTAI-20260729-ase-01-tradingview-strategy-lab
status: validating
branch: agent/ase-01-tradingview-strategy-lab
base_branch: develop
created: 2026-07-29
updated: 2026-07-29
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - ai_strategy_engine/ARCHITECTURE.md
  - ai_strategy_engine/TASKS.md
  - ai_strategy_engine/docs/IMPLEMENTATION_CHECKPOINT.md
  - docs/ai_platform/ROADMAP.md
search_first:
  - ai_strategy_engine/strategies/
  - ai_platform/portal/strategy_lab/
  - ai_platform/portal/web/app/ai/experiments/
  - tests/ai_platform/portal/strategy_lab/
owned_paths:
  - ai_strategy_engine/strategies/
  - ai_strategy_engine/TASKS.md
  - ai_platform/portal/strategy_lab/
  - ai_platform/research/strategy_lab/
  - ai_platform/portal/control_plane/api.py
  - ai_platform/portal/control_plane/api_core.py
  - ai_platform/portal/control_plane/database.py
  - ai_platform/portal/web/app/ai/experiments/
  - ai_platform/portal/web/lib/strategy-lab-*.ts
  - ai_platform/portal/web/e2e/strategy-lab.spec.ts
  - tests/ai_platform/portal/strategy_lab/
  - tests/ai_platform_integration/test_ase01_strategy_lab_e2e.py
  - .github/workflows/ai-strategy-engine.yml
  - docs/ai_platform/ASE_01_TRADINGVIEW_STRATEGY_LAB.md
  - docs/agents/tasks/FTAI-20260729-ase-01-tradingview-strategy-lab.md
---

# ASE-01 TradingView Strategy Lab

## Goal

Deliver the first complete research-only TradingView-inspired strategy laboratory from canonical Strategy DSL through deterministic backtest, durable tenant-scoped experiment storage, API and Bot Management UI.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-29T15:55:00+02:00
checkpoint_carrier: self
head: 65172feb238a4f59b7a66f164e18fab303e660c7
branch: agent/ase-01-tradingview-strategy-lab
base_head: f898c01dd3f3165571be257eee3947b555124bad
pr: 679
status: validating
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - ai_strategy_engine/ARCHITECTURE.md
  - ai_strategy_engine/TASKS.md
  - docs/ai_platform/ASE_01_TRADINGVIEW_STRATEGY_LAB.md
owned_paths:
  - ai_strategy_engine/strategies/
  - ai_strategy_engine/TASKS.md
  - ai_platform/portal/strategy_lab/
  - ai_platform/research/strategy_lab/
  - ai_platform/portal/control_plane/api.py
  - ai_platform/portal/control_plane/api_core.py
  - ai_platform/portal/control_plane/database.py
  - ai_platform/portal/web/app/ai/experiments/
  - ai_platform/portal/web/lib/strategy-lab-contracts.ts
  - ai_platform/portal/web/lib/strategy-lab-fixtures.ts
  - ai_platform/portal/web/lib/strategy-lab-api.ts
  - ai_platform/portal/web/e2e/strategy-lab.spec.ts
  - tests/ai_platform/portal/strategy_lab/
  - tests/ai_platform_integration/test_ase01_strategy_lab_e2e.py
  - .github/workflows/ai-strategy-engine.yml
  - docs/ai_platform/ASE_01_TRADINGVIEW_STRATEGY_LAB.md
  - docs/agents/tasks/FTAI-20260729-ase-01-tradingview-strategy-lab.md
proven:
  - ASE-00 merged normally into develop as eae105601d2408f7f1b7c3cd9e42736592f3d59d after exact-head validation.
  - Owner instruction authorizes autonomous normal merge after required checks and immediate continuation to the next bounded package.
  - Clean-room strategies tv_supertrend_v1@1.0.0 and tv_squeeze_momentum_v1@1.0.0 are canonical Strategy DSL artifacts; no proprietary Pine Script or parity claim is present.
  - The deterministic simulator uses only closed and confirmed candles, evaluates signals on the current closed bar and fills at the next bar open.
  - Tenant-scoped SQLAlchemy persistence records result identity, trades, equity and signal explanations with idempotency and corruption detection.
  - Portal control-plane API and /ai/experiments Testy / Laboratorium UI are extended without Browser-to-Freqtrade authority.
  - Protected final holdout v2 is rejected; order submission, live execution, private exchange credentials, eval and exec remain absent.
  - Implementation head 285e360769c2cfc9e9b28baf47ae52cc7d0c313b passed every exact-head workflow before the final develop synchronization.
  - develop synchronization PRs 682 and 692 were merged normally without force push or branch-protection bypass.
derived:
  - Synchronous bounded execution is sufficient for the first research vertical slice; an asynchronous worker may later implement the same contracts without changing browser authority.
unknown:
  - Final conclusions of the exact-head workflows started after synchronization commit 65172feb238a4f59b7a66f164e18fab303e660c7 and this checkpoint carrier commit.
conflicts: []
first_failure: null
rejected_hypotheses:
  - Copy proprietary Pine Script or claim 1:1 parity.
  - Use eval or exec.
  - Add live orders, private exchange credentials or Browser-to-Freqtrade access.
  - Use protected final holdout v2.
  - Add Optuna before deterministic laboratory acceptance.
  - Force-push over concurrent develop work.
changed_paths:
  - ai_strategy_engine/strategies/
  - ai_strategy_engine/TASKS.md
  - ai_platform/portal/strategy_lab/
  - ai_platform/research/strategy_lab/
  - ai_platform/portal/control_plane/api.py
  - ai_platform/portal/control_plane/api_core.py
  - ai_platform/portal/control_plane/database.py
  - ai_platform/portal/web/app/ai/experiments/
  - ai_platform/portal/web/lib/strategy-lab-contracts.ts
  - ai_platform/portal/web/lib/strategy-lab-fixtures.ts
  - ai_platform/portal/web/lib/strategy-lab-api.ts
  - ai_platform/portal/web/e2e/strategy-lab.spec.ts
  - tests/ai_platform/portal/strategy_lab/
  - tests/ai_platform_integration/test_ase01_strategy_lab_e2e.py
  - .github/workflows/ai-platform.yml
  - .github/workflows/ai-strategy-engine.yml
  - docs/ai_platform/ASE_01_TRADINGVIEW_STRATEGY_LAB.md
  - docs/agents/tasks/FTAI-20260729-ase-01-tradingview-strategy-lab.md
validation:
  - command: AI Platform CI run 30456574929 on 285e360769c2cfc9e9b28baf47ae52cc7d0c313b
    result: PASS
    evidence: tests, Ruff, Ruff format, codespell and manifest/schema validation completed successfully.
  - command: AI Strategy Engine run 30456574761 on 285e360769c2cfc9e9b28baf47ae52cc7d0c313b
    result: PASS
    evidence: package tests, 12 Strategy Lab tests, Ruff, mypy, compileall, ASE-00/ASE-01 deterministic E2E, schema validation and security/architecture scans completed successfully.
  - command: Portal Web CI run 30456574388 on 285e360769c2cfc9e9b28baf47ae52cc7d0c313b
    result: PASS
    evidence: typecheck, lint, production build and Chromium regression completed successfully.
  - command: Portal Universal E2E run 30456574325 on 285e360769c2cfc9e9b28baf47ae52cc7d0c313b
    result: PASS
    evidence: backend scenario and critical Chromium journey completed successfully.
  - command: Freqtrade CI run 30456574888 on 285e360769c2cfc9e9b28baf47ae52cc7d0c313b
    result: PASS
    evidence: pre-commit, documentation, Python 3.11/3.12/3.13/3.14 matrix and distribution build completed successfully.
  - command: GitHub Actions Security Analysis run 30456574861 on 285e360769c2cfc9e9b28baf47ae52cc7d0c313b
    result: PASS
    evidence: workflow security analysis completed successfully.
  - command: synchronized exact-head workflow set
    result: RUNNING
    evidence: AI Strategy Engine 30458027494; AI Platform CI 30458027823; Freqtrade CI 30458027840; Portal Universal E2E 30458030836; Security Analysis 30458030845; Portal Web CI 30458030861. Pre-commit Types update 30458028067 skipped normally.
known_limitations:
  - Synthetic BTC/USDT 15m fixture is the only default dataset.
  - Long-only single-position simulator; no portfolio or intrabar execution model.
  - Synchronous bounded execution.
missing_functions:
  - tv_macd_mtf_v1 and tv_support_resistance_breakout_v1.
  - Optuna ParameterOptimizer execution.
  - Real historical-data provider integration.
blockers: []
next_action: Verify all workflows on the checkpoint carrier head, update PR 679 with final evidence, mark ready and merge normally if develop remains unchanged.
```
