---
task_id: FTAI-20260730-closure-research-data
status: blocked
branch: agent/closure-research-data
base_branch: develop
created: 2026-07-30
updated: 2026-07-30
related_pr: null
dependencies:
  - PR #753 merged or closed with a durable replacement
  - PR #761 merged or closed
  - current Liquid20 and WickHunter source contracts frozen
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
search_first:
  - current develop, open PRs and exact owned-path conflicts
  - canonical implementation and tests before adding code
  - shared contract freeze commit and dependency state
---

# Closure research data and market structure

## Goal

Implement point-in-time OI/funding alignment and clean-room market-structure research after active source work freezes its canonical inputs.

## Evidence at Gate 0

Liquidation aggregation, deduplication, receive-time metadata and bounded cross-exchange evidence already exist. OI/funding alignment is absent, and the market-structure module intentionally raises NotImplementedError.

## Deliverables

- Source-separated OI and funding as-of alignment with availability timestamps.
- Clean-room BOS/CHoCH, HH/HL/LH/LL, EQH/EQL, confirmed FVG and independently specified zone heuristic.
- Provenance, deduplication and negative lookahead tests.
- Explicit license boundary and no proprietary-code copying.

## Non-negotiable boundaries

- Paper, shadow or dry-run only; no live-capital authority.
- No browser-to-Freqtrade, exchange or Vault path.
- No protected-holdout reuse and no changes to frozen thresholds `0.006/-0.009`.
- Stay inside exact `owned_paths`; stop on the first incompatible shared-contract requirement.
- Add tests at the same layer and merge only through normal green CI.

## Acceptance criteria

- Alignment never uses observations unavailable at decision time.
- Structure events use confirmed pivots and expose detected and available times.
- Source conflicts and missing data produce explicit unknown or degraded states.

## Validation

Run narrow tests first, then all repository workflows required by the changed paths. Validate this task checkpoint before every handoff.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-30T10:55:00+02:00
head: 1d347a785eddc900f4484c30e06c3ab4e8851b29
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
  - Liquidation aggregation, deduplication, receive-time metadata and bounded cross-exchange evidence already exist. OI/funding alignment is absent, and the market-structure module intentionally raises NotImplementedError.
derived:
  - The bounded implementation scope is restricted to 6 exact path entries.
unknown:
  - Exact implementation HEAD, PR number and CI run IDs until the worker starts.
conflicts: []
first_failure:
  marker: ACTIVE_SOURCE_OWNERSHIP
  evidence: Active PRs #753 and #761 can still change canonical source identities and time metadata; downstream alignment must not start against unstable inputs.
rejected_hypotheses:
  - An unchecked backlog box alone proves missing implementation.
  - A downstream worker may redefine shared contracts.
  - Repository fixtures may be described as real external acceptance.
changed_paths: []
validation:
  - command: python tools/agents/checkpoint.py <task-path> --require-checkpoint
    result: PASS
    evidence: Gate 0 validates this compact checkpoint before dispatch.
blockers:
  - PR #753 owns WickHunter market-evidence source and Portal paths.
  - PR #761 owns active Liquid20 source catalog, runtime and Portal read-model paths.
next_action: After PR #753 and PR #761 reach terminal state, verify their frozen source contracts and then create the declared branch from the new develop.
```
