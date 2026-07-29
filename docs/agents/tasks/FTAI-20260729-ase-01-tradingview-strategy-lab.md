---
task_id: FTAI-20260729-ase-01-tradingview-strategy-lab
status: planning
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
search_first:
  - ai_strategy_engine/configs/feature_registry.v1.yaml
  - ai_strategy_engine/src/strategy_engine/registry.py
  - ai_strategy_engine/examples/strategy_classic.json
  - ai_strategy_engine/examples/strategy_miyagi_ensemble_research.json
  - ai_platform/research/strategy_engine/ase00_adapter.py
optional_reads:
  - docs/ai_platform/ROADMAP.md
owned_paths:
  - docs/agents/tasks/FTAI-20260729-ase-01-tradingview-strategy-lab.md
---

# ASE-01 TradingView strategy lab

## Goal

Resolve the authoritative bounded ASE-01 scope from repository evidence before implementation, preserving the research-only, point-in-time, fail-closed and no-direct-execution boundaries established by ASE-00.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-29T12:26:00+02:00
checkpoint_carrier: self
branch: agent/ase-01-tradingview-strategy-lab
base_head: eae105601d2408f7f1b7c3cd9e42736592f3d59d
pr: null
status: planning
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - ai_strategy_engine/ARCHITECTURE.md
  - ai_strategy_engine/TASKS.md
  - ai_strategy_engine/docs/IMPLEMENTATION_CHECKPOINT.md
proven:
  - ASE-00 PR 584 merged normally into develop as eae105601d2408f7f1b7c3cd9e42736592f3d59d after all required exact-head workflows passed.
  - Branch agent/ase-01-tradingview-strategy-lab exists and is identical to develop at eae105601d2408f7f1b7c3cd9e42736592f3d59d before this checkpoint commit.
  - The predecessor ASE-00 task record names FTAI-20260729-ase-01-tradingview-strategy-lab as the next package.
  - ai_strategy_engine/TASKS.md names ASE-01 as Feature Registry service with loader, schema, dependency resolver, listing API, parity fixtures, append-only replay tests and a read-only portal model.
  - No existing task record or implementation for FTAI-20260729-ase-01-tradingview-strategy-lab was present before this checkpoint.
  - ASE-00 already delivered canonical registry configuration, a registry implementation, Strategy DSL, examples, Leakage Guard and a research-only shadow adapter.
derived:
  - Implementing either a TradingView laboratory or a Feature Registry service without reconciling the conflicting package definitions would risk duplicate or mis-scoped work.
  - The first ASE-01 work must be repository inventory and gap analysis, not product or execution code.
unknown:
  - Whether the authoritative ASE-01 deliverable is the TradingView strategy laboratory named by the predecessor checkpoint, the Feature Registry service named by ai_strategy_engine/TASKS.md, or a bounded package combining only non-overlapping parts.
  - Final owned paths, API boundaries, acceptance criteria and PR decomposition.
conflicts:
  - The predecessor task-specific checkpoint names ASE-01 TradingView strategy lab, while the canonical AI Strategy Engine backlog names ASE-01 Feature Registry service.
first_failure: null
rejected_hypotheses:
  - Start UI, backtest API, execution integration or arbitrary TradingView parity work before scope reconciliation.
  - Duplicate the registry, Portal, Risk Core, liquidation ingestion or execution gateway delivered elsewhere.
  - Introduce Browser-to-Freqtrade access, live orders or proprietary indicator parity claims.
changed_paths:
  - docs/agents/tasks/FTAI-20260729-ase-01-tradingview-strategy-lab.md
validation:
  - command: Compare develop to ASE-01 branch before checkpoint creation
    result: PASS
    evidence: develop and agent/ase-01-tradingview-strategy-lab were identical at eae105601d2408f7f1b7c3cd9e42736592f3d59d.
known_limitations:
  - No ASE-01 implementation is authorized by this planning checkpoint.
  - ASE remains research/shadow-only and the protected final holdout remains unavailable for iterative work.
blockers:
  - Authoritative ASE-01 scope conflict must be resolved from repository evidence before implementation.
next_action: Perform a focused repository inventory and gap analysis that reconciles the predecessor TradingView strategy-lab package with ai_strategy_engine/TASKS.md ASE-01 Feature Registry service; then update this checkpoint with one bounded goal, owned paths, acceptance criteria and implementation next action before changing product code.
```
