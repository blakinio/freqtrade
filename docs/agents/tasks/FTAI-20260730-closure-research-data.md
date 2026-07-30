---
task_id: FTAI-20260730-closure-research-data
status: ready
branch: agent/closure-research-data
base_branch: develop
created: 2026-07-30
updated: 2026-07-30
related_pr: null
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
updated_at: 2026-07-30T17:35:00+02:00
head: acfd66f6fb6f8db03eb4425e8c1a5c8ae4e83ff0
branch: agent/closure-research-data
pr: null
status: ready
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
  - PR 761 merged normally as 141e59a3c7da441432b3990a54903e5fcfc935c8.
  - The merged Liquid20 source contract preserves explicit exchange event, receive and heartbeat times plus source-separated identities.
  - Open PRs 801, 780 and 758 do not touch any Research Data owned path.
derived:
  - The terminal-source dependency is satisfied and no active duplicate or ownership conflict exists.
unknown:
  - Exact implementation head, PR number and CI run IDs until the worker starts.
conflicts: []
first_failure:
  marker: NONE
  evidence: The prior PR 761 dependency is terminal and live owned paths are disjoint.
rejected_hypotheses:
  - Copy proprietary or LuxAlgo implementation details.
  - Use observations before their availability time.
  - Redefine shared source or strategy contracts.
changed_paths:
  - docs/agents/tasks/FTAI-20260730-closure-research-data.md
validation:
  - command: PR 761 terminal-state verification
    result: PASS
    evidence: PR 761 merged as 141e59a3c7da441432b3990a54903e5fcfc935c8.
  - command: Open PR changed-path comparison against Research Data ownership
    result: PASS
    evidence: PR 801, PR 780 and PR 758 have no overlap with the six declared paths.
blockers: []
next_action: Start docs/agents/prompts/ai-program-closure/RESEARCH-DATA-AGENT-PROMPT.md in a new chat from current develop.
```
