---
task_id: FTAI-20260730-closure-simulator
status: active
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
updated_at: 2026-07-30T12:45:00+02:00
head: 1fd17232cf31b6bfd29588f66ada76773206d394
branch: agent/closure-simulator
pr: null
status: active
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
  - Gate 0 is merged and the manual dispatch table marks closure-simulator READY with no dependencies.
  - Open PRs 758, 761 and 762 do not touch any simulator-owned path.
  - The existing universal scenario remains compatible through zero-cost, zero-latency and no-stop defaults.
  - Versioned cost, latency, funding and gap-stop models are implemented only inside assigned paths.
  - Canonical immutable simulation evidence uses deterministic UUID5 identities and SHA-256 over canonical JSON.
derived:
  - Scenario latency fails closed when no tick exists at or after the configured ready time.
  - Positive funding is a cash outflow for BUY positions and an inflow for SELL positions.
  - A stop crossed between discrete ticks fills at the adverse observed price rather than the configured stop.
unknown:
  - Exact Ruff, pytest and repository workflow conclusions until PR CI runs.
  - Review-thread count until the PR exists.
conflicts: []
first_failure:
  marker: VALIDATION_PENDING
  evidence: The sandbox cannot check out the GitHub repository, so exact repository tests must run through GitHub Actions on the focused PR.
rejected_hypotheses:
  - Use wall-clock sleeps or network data to model latency.
  - Treat repository simulation as real exchange submission evidence.
  - Modify runner, Risk Core, execution contracts, shared exports or CI outside assigned ownership.
changed_paths:
  - ai_platform/portal/simulator/schema.py
  - ai_platform/portal/simulator/exchange.py
  - ai_platform/portal/simulator/costs.py
  - ai_platform/portal/simulator/latency.py
  - ai_platform/portal/simulator/funding.py
  - ai_platform/portal/simulator/gap_stop.py
  - tests/ai_platform/portal/simulator/test_execution_costs.py
  - tests/ai_platform/portal/simulator/test_latency_funding_gap_stop.py
  - tests/ai_platform/portal/simulator/test_deterministic_replay.py
validation:
  - command: Python py_compile over the exact authored simulator and test file contents
    result: PASS
    evidence: All nine Python files compiled without syntax errors before repository writes.
  - command: compare develop...agent/closure-simulator
    result: PASS
    evidence: Branch is ahead by nine commits, behind by zero, and changes exactly the nine implementation/test paths expected before checkpoint update.
blockers: []
next_action: Open the focused PR against develop and use exact-head GitHub Actions results to repair any Ruff, pytest or compatibility failure.
```
