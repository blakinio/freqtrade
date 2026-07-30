---
task_id: FTAI-20260730-closure-research-data
status: blocked
branch: agent/closure-research-data
base_branch: develop
created: 2026-07-30
updated: 2026-07-30
related_pr: null
dependencies:
  - Gate 0 merged
  - PR #761 merged or closed
  - current source identities/time metadata rechecked
owned_paths:
  - docs/agents/tasks/FTAI-20260730-closure-research-data.md
  - ai_strategy_engine/src/strategy_engine/features/market_structure.py
  - ai_strategy_engine/src/strategy_engine/research/__init__.py
  - ai_strategy_engine/src/strategy_engine/research/liquidation_alignment.py
  - ai_strategy_engine/tests/unit/test_market_structure.py
  - ai_strategy_engine/tests/unit/test_liquidation_alignment.py
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260730-ai-program-closure-orchestration.md
  - docs/ai_platform/PROGRAM_CLOSURE_MATRIX.md
  - ai_strategy_engine/TASKS.md
  - ai_strategy_engine/src/strategy_engine/features/market_structure.py
  - ai_platform/research/liquidations/contracts.py
search_first:
  - current develop, open PRs and exact owned-path conflicts
  - canonical implementation and tests before adding code
  - shared contract/dependency state before editing
---

# Closure research data and market structure

## Goal

Implement point-in-time OI/funding alignment and clean-room market-structure research after active Liquid20 source work is terminal.

## Deliverables

- Source-separated OI/funding as-of alignment with availability timestamps.
- Clean-room BOS/CHoCH, HH/HL/LH/LL, EQH/EQL, confirmed FVG and own zone heuristic.
- Provenance, deduplication and negative-lookahead tests.

## Non-negotiable boundaries

- Paper, shadow or dry-run only; no live-capital authority.
- No browser-to-Freqtrade, exchange or Vault path.
- No protected-holdout reuse and no changes to frozen thresholds `0.006/-0.009`.
- Stay inside exact `owned_paths`; stop on the first incompatible shared-contract requirement.
- Add tests at the same layer and merge only through normal green CI.

## Acceptance criteria

- No observation is used before availability.
- Structure events use confirmed pivots and explicit detected/available times.
- No proprietary/LuxAlgo implementation or parity claim.

## Validation

Run narrow validation first, then all repository gates selected by affected paths. Open one focused PR, verify exact implementation HEAD, required CI and unresolved review threads, synchronize normally and merge only after green checks.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-30T11:35:00+02:00
head: 0208666d98849386e2f2d9acf534b13891e4afa2
branch: agent/closure-research-data
pr: null
status: blocked
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260730-ai-program-closure-orchestration.md
  - docs/ai_platform/PROGRAM_CLOSURE_MATRIX.md
owned_paths:
  - docs/agents/tasks/FTAI-20260730-closure-research-data.md
  - ai_strategy_engine/src/strategy_engine/features/market_structure.py
  - ai_strategy_engine/src/strategy_engine/research/__init__.py
  - ai_strategy_engine/src/strategy_engine/research/liquidation_alignment.py
  - ai_strategy_engine/tests/unit/test_market_structure.py
  - ai_strategy_engine/tests/unit/test_liquidation_alignment.py
proven:
  - PR #753 is merged; liquidation aggregation, dedup and latency metadata are proven.
derived:
  - PR #761 can still extend source identity/time metadata; this task must wait.
unknown:
  - Final PR #761 merge/close state and frozen source contract.
conflicts: []
first_failure:
  marker: PRE_IMPLEMENTATION_GATE
  evidence: Implementation has not started; the matrix dispatch condition is the first enforced gate.
rejected_hypotheses:
  - An unchecked backlog box alone proves missing implementation.
  - A downstream worker may redefine shared contracts or edit another owner path.
  - Repository fixtures may be described as real P11 acceptance.
changed_paths: []
validation:
  - command: python tools/agents/checkpoint.py <task-path> --require-checkpoint
    result: PASS
    evidence: Gate 0 validated this compact checkpoint against the repository governance contract.
blockers:
  - PR #761 remains open.
next_action: After PR #761 reaches terminal state, verify source contracts and create `agent/closure-research-data` from the resulting develop.
```
