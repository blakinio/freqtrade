---
task_id: FTAI-20260730-closure-research-data
status: active
branch: agent/closure-research-data
base_branch: develop
created: 2026-07-30
updated: 2026-07-30
related_pr: 821
dependencies:
  - Gate 0 merged
  - PR #761 merged as 141e59a3c7da441432b3990a54903e5fcfc935c8
  - source identities and time metadata rechecked
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
  - ai_platform/research/liquidations/contracts.py
---

# Closure research data and market structure

## Goal

Implement point-in-time OI and funding alignment plus clean-room market-structure research against the terminal source contract.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-30T21:50:00+02:00
head: 7014f70340f9135a351cdd03c0df4673209c6d79
branch: agent/closure-research-data
pr: 821
status: active
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
  - PR 761 merged normally as 141e59a3c7da441432b3990a54903e5fcfc935c8 and preserves source identity plus event and receive times.
  - Branch agent/closure-research-data was created from develop 9bb8edad795e122a2e513b354cd4aafa16d5917b.
  - Open PRs 816 and 758 do not overlap any Research Data owned path.
  - Point-in-time OI and funding alignment now preserves source, schema/data version and event, receive and availability times.
  - Alignment distinguishes missing, delayed and stale observations and rejects conflicting deterministic identities.
  - Clean-room confirmed pivots now produce HH/HL/LH/LL, EQH/EQL, close-confirmed BOS/CHoCH, third-bar-confirmed FVG and versioned pre-break zones.
  - Focused isolated unit validation passed 10 tests and Python compile validation passed.
derived:
  - All assigned Research Data gaps are implemented without redefining the terminal Liquid20 contract or adding signal, promotion or execution authority.
  - Develop advanced to 94e15dde23e0a2402b580ef263d51af689e989b6 only through the disjoint Signal Wizard task checkpoint.
unknown:
  - Exact-head GitHub Actions conclusions and unresolved review-thread count for PR 821.
conflicts: []
first_failure:
  marker: NONE
  evidence: Focused implementation validation is green; repository CI has not concluded yet.
rejected_hypotheses:
  - Copy proprietary or LuxAlgo implementation details.
  - Use observations or pivots before their availability time.
  - Redefine shared source or strategy contracts.
changed_paths:
  - docs/agents/tasks/FTAI-20260730-closure-research-data.md
  - ai_strategy_engine/src/strategy_engine/features/market_structure.py
  - ai_strategy_engine/src/strategy_engine/research/__init__.py
  - ai_strategy_engine/src/strategy_engine/research/liquidation_alignment.py
  - ai_strategy_engine/tests/unit/test_market_structure.py
  - ai_strategy_engine/tests/unit/test_liquidation_alignment.py
validation:
  - command: isolated python -m compileall -q strategy_engine
    result: PASS
  - command: isolated pytest -q test_market_structure.py test_liquidation_alignment.py
    result: PASS
    evidence: 10 passed
  - command: Open PR changed-path comparison against Research Data ownership
    result: PASS
    evidence: PRs 816 and 758 are disjoint; develop-only PR 818 changed only the Signal Wizard task checkpoint.
  - command: PR 821 exact-head repository CI
    result: PENDING
blockers: []
next_action: Verify PR 821 exact-head CI and resolve the first failing check or review thread.
```
