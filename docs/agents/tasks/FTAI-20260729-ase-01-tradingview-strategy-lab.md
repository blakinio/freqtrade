---
task_id: FTAI-20260729-ase-01-tradingview-strategy-lab
status: active
branch: agent/ase-01-tradingview-strategy-lab
base_branch: develop
created: 2026-07-29
updated: 2026-07-29
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - ai_strategy_engine/ARCHITECTURE.md
  - ai_strategy_engine/docs/IMPLEMENTATION_CHECKPOINT.md
  - docs/ai_platform/ROADMAP.md
search_first:
  - ai_strategy_engine/src/strategy_engine/features/supertrend.py
  - ai_strategy_engine/src/strategy_engine/features/squeeze.py
  - ai_platform/portal/learning/
  - ai_platform/portal/web/app/ai/experiments/
owned_paths:
  - ai_strategy_engine/strategies/
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
  - docs/ai_platform/ASE_01_TRADINGVIEW_STRATEGY_LAB.md
  - docs/agents/tasks/FTAI-20260729-ase-01-tradingview-strategy-lab.md
---

# ASE-01 TradingView Strategy Lab

## Goal

Deliver the first complete research-only TradingView-inspired strategy laboratory from canonical Strategy DSL through deterministic backtest, durable tenant-scoped experiment storage, API and Bot Management UI.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-29T11:38:00+02:00
checkpoint_carrier: self
validated_parent_head: eae105601d2408f7f1b7c3cd9e42736592f3d59d
branch: agent/ase-01-tradingview-strategy-lab
base_head: eae105601d2408f7f1b7c3cd9e42736592f3d59d
pr: null
status: active
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - ai_strategy_engine/ARCHITECTURE.md
  - docs/ai_platform/ASE_01_TRADINGVIEW_STRATEGY_LAB.md
owned_paths:
  - ai_strategy_engine/strategies/
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
  - docs/ai_platform/ASE_01_TRADINGVIEW_STRATEGY_LAB.md
  - docs/agents/tasks/FTAI-20260729-ase-01-tradingview-strategy-lab.md
proven:
  - ASE-00 provides canonical Strategy DSL, validators and independent Supertrend and Squeeze feature implementations.
  - Portal already owns tenant identity, authorization, SQLAlchemy persistence and the /ai/experiments product surface.
  - The new package extends those components instead of creating a competing backtester, experiment database or browser-to-Freqtrade path.
derived:
  - A synchronous bounded deterministic simulator is sufficient for the first usable vertical slice and can later be replaced by an asynchronous worker behind the same API contracts.
unknown:
  - Final exact-head workflow run identifiers until implementation validation completes.
conflicts: []
first_failure: null
rejected_hypotheses:
  - Copy proprietary Pine Script.
  - Use eval or exec.
  - Add live order or credential authority.
  - Use protected final holdout v2.
  - Add Optuna before deterministic laboratory acceptance.
changed_paths: []
validation:
  - command: local focused Strategy Lab tests (12 cases)
    result: PASS
    evidence: Catalog, parameter bounds, deterministic replay, no-lookahead, closed/confirmed-bar rejection, missing data, live-mode rejection, idempotency, tenant isolation, corrupt-result rejection and API vertical slice pass in the prepared implementation.
known_limitations:
  - Synthetic BTC/USDT 15m fixture is the only default dataset.
  - Long-only single-position simulator; no portfolio or intrabar execution model.
  - Synchronous bounded execution.
missing_functions:
  - tv_macd_mtf_v1 and tv_support_resistance_breakout_v1.
  - Optuna ParameterOptimizer execution.
  - Real historical-data provider integration.
blockers: []
next_action: Commit the prepared Strategy Lab vertical slice, open a draft PR to develop, run exact-head validation and repair only confirmed failures.
```
