---
task_id: FTAI-20260730-closure-simulator
status: ready
branch: agent/closure-simulator
base_branch: develop
created: 2026-07-30
updated: 2026-07-30
related_pr: null
dependencies:
  - none
owned_paths:
  - docs/agents/tasks/FTAI-20260730-closure-simulator.md
  - ai_platform/portal/simulator/schema.py
  - ai_platform/portal/simulator/exchange.py
  - ai_platform/portal/simulator/costs.py
  - ai_platform/portal/simulator/latency.py
  - ai_platform/portal/simulator/funding.py
  - ai_platform/portal/simulator/gap_stop.py
  - tests/ai_platform/portal/simulator/test_execution_costs.py
  - tests/ai_platform/portal/simulator/test_latency_funding_gap_stop.py
  - tests/ai_platform/portal/simulator/test_deterministic_replay.py
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

# Closure simulator fidelity

## Goal

Add the missing latency, funding and gap-through-stop fidelity to the canonical deterministic simulator while preserving existing fee, slippage and replay behavior.

## Evidence at Gate 0

Strategy Lab already models fees and slippage, and P10/ASE-03 prove deterministic replay. The canonical portal simulator currently records zero fees and has no latency, funding or gap-stop model.

## Deliverables

- Versioned deterministic fee/slippage/cost contract reused by simulator scenarios.
- Latency model tied to scenario time rather than wall-clock sleeps.
- Funding accrual with explicit timestamps and signs.
- Gap-through-stop fill semantics with deterministic reason codes.
- Replay and negative safety tests.

## Non-negotiable boundaries

- Paper, shadow or dry-run only; no live-capital authority.
- No browser-to-Freqtrade, exchange or Vault path.
- No protected-holdout reuse and no changes to frozen thresholds `0.006/-0.009`.
- Stay inside exact `owned_paths`; stop on the first incompatible shared-contract requirement.
- Add tests at the same layer and merge only through normal green CI.

## Acceptance criteria

- Same manifest and seed produce byte-stable evidence.
- No real exchange or order endpoint is called.
- Costs and stop behavior are explicit in reconciliation evidence.

## Validation

Run narrow tests first, then all repository workflows required by the changed paths. Validate this task checkpoint before every handoff.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-30T10:55:00+02:00
head: 1d347a785eddc900f4484c30e06c3ab4e8851b29
branch: agent/closure-simulator
pr: null
status: ready
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260730-ai-program-closure-orchestration.md
  - docs/ai_platform/PROGRAM_CLOSURE_MATRIX.md
owned_paths:
  - docs/agents/tasks/FTAI-20260730-closure-simulator.md
  - ai_platform/portal/simulator/schema.py
  - ai_platform/portal/simulator/exchange.py
  - ai_platform/portal/simulator/costs.py
  - ai_platform/portal/simulator/latency.py
  - ai_platform/portal/simulator/funding.py
  - ai_platform/portal/simulator/gap_stop.py
  - tests/ai_platform/portal/simulator/test_execution_costs.py
  - tests/ai_platform/portal/simulator/test_latency_funding_gap_stop.py
  - tests/ai_platform/portal/simulator/test_deterministic_replay.py
proven:
  - Strategy Lab already models fees and slippage, and P10/ASE-03 prove deterministic replay. The canonical portal simulator currently records zero fees and has no latency, funding or gap-stop model.
derived:
  - The bounded implementation scope is restricted to 10 exact path entries.
unknown:
  - Exact implementation HEAD, PR number and CI run IDs until the worker starts.
conflicts: []
first_failure:
  marker: PRE_IMPLEMENTATION_GATE
  evidence: Implementation has not started; the Gate 0 dispatch condition is the first enforced gate.
rejected_hypotheses:
  - An unchecked backlog box alone proves missing implementation.
  - A downstream worker may redefine shared contracts.
  - Repository fixtures may be described as real external acceptance.
changed_paths: []
validation:
  - command: python tools/agents/checkpoint.py <task-path> --require-checkpoint
    result: PASS
    evidence: Gate 0 validates this compact checkpoint before dispatch.
blockers: []
next_action: Create the branch from current develop, extend only the declared simulator paths, run simulator tests, and open one focused PR.
```
