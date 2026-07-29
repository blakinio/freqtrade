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
updated_at: 2026-07-29T12:38:00+02:00
checkpoint_carrier: self
head: 29717cdb0ec5fc7bf6d4b73efef5177b1c8e291c
branch: agent/ase-01-tradingview-strategy-lab
base_head: eae105601d2408f7f1b7c3cd9e42736592f3d59d
pr: null
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
  - The owner explicitly assigned FTAI-20260729-ase-01-tradingview-strategy-lab with the TradingView laboratory acceptance criteria after ASE-00.
  - The earlier generic backlog reused ASE-01 for Feature Registry service; it is now separated as ASE-FR-01 so the task-specific owner instruction is authoritative and unambiguous.
  - Existing ASE-00 Strategy DSL, validator, Supertrend and Squeeze implementations are reused rather than duplicated.
  - Existing Portal identity, authorization, SQLAlchemy metadata and /ai/experiments route are extended rather than replaced.
  - Implementation commit 29717cdb0ec5fc7bf6d4b73efef5177b1c8e291c contains both clean-room strategies, deterministic simulator, tenant store, API, UI, comparison and tests.
derived:
  - Synchronous bounded execution is sufficient for the first vertical slice; an asynchronous worker can later implement the same contracts without changing browser authority.
unknown:
  - Exact workflow run identifiers and any repository-only formatting or integration failures until the branch is pushed and PR checks run.
conflicts: []
first_failure: null
rejected_hypotheses:
  - Copy proprietary Pine Script or claim 1:1 parity.
  - Use eval or exec.
  - Add live orders, private exchange credentials or Browser-to-Freqtrade access.
  - Use protected final holdout v2.
  - Add Optuna before deterministic laboratory acceptance.
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
  - .github/workflows/ai-strategy-engine.yml
  - docs/ai_platform/ASE_01_TRADINGVIEW_STRATEGY_LAB.md
  - docs/agents/tasks/FTAI-20260729-ase-01-tradingview-strategy-lab.md
validation:
  - command: focused local Strategy Lab pytest
    result: PASS
    evidence: 12 tests cover catalog, bounds, deterministic replay, no-lookahead, closed/confirmed bars, missing data, live rejection, idempotency, tenant isolation, permissions, holdout, corrupt results, API, comparison and control-plane route.
  - command: local Python compileall
    result: PASS
    evidence: Strategy Lab source and tests compile.
  - command: local TypeScript noEmit check
    result: PASS
    evidence: Strategy Lab contracts, API, fixtures, server actions, page and client typecheck with local module stubs.
known_limitations:
  - Synthetic BTC/USDT 15m fixture is the only default dataset.
  - Long-only single-position simulator; no portfolio or intrabar execution model.
  - Synchronous bounded execution.
missing_functions:
  - tv_macd_mtf_v1 and tv_support_resistance_breakout_v1.
  - Optuna ParameterOptimizer execution.
  - Real historical-data provider integration.
blockers: []
next_action: Push the checkpoint commit, open a draft PR to develop, run exact-head workflows and repair only confirmed failures.
```
