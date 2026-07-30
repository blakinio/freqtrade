---
task_id: FTAI-20260730-closure-simulator
status: ready
branch: agent/closure-simulator-restack
base_branch: develop
created: 2026-07-30
updated: 2026-07-30
related_pr: 787
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
updated_at: 2026-07-30T13:32:28+02:00
head: b040f03939aed4bd8dba224a8817ccd9d74ed91c
branch: agent/closure-simulator-restack
pr: 787
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
  - Gate 0 is merged and the dispatch table marks closure-simulator READY with no dependencies.
  - Develop advanced only in five disjoint time-leakage paths through merged PR 777.
  - PR 787 is a no-force restack from develop commit 979744f1143246bd42e42fc2213c7e79fc68ea57.
  - PR 787 is not behind develop and changes exactly the ten assigned paths.
  - Versioned cost, latency, funding and gap-stop models remain simulation-only and fail closed.
  - Zero-cost, zero-latency and no-stop defaults preserve the existing universal scenario result.
  - Same manifest and seed produce canonical evidence with deterministic UUID5 identities and SHA-256.
  - AI Platform CI run 30538061822 passed compile, tests, Ruff, format, codespell and JSON validation.
  - Portal Universal E2E run 30538061770 passed backend and Chromium journeys.
  - Security run 30538061796 passed zizmor analysis.
  - Freqtrade CI run 30538061837 passed pre-commit, docs, Python 3.11-3.14 core tests, coverage, distributions and CI Gate.
derived:
  - Positive funding is a cash outflow for BUY positions and an inflow for SELL positions.
  - A stop crossed between discrete ticks fills at the adverse observed price.
  - Scenario latency uses the first tick at or after readiness and raises when no tick exists.
unknown: []
conflicts: []
first_failure:
  marker: BASE_ADVANCED_RESTACKED
  evidence: Develop advanced after PR 779 became green; the work was restacked from current develop without force-push and revalidated on PR 787.
rejected_hypotheses:
  - Merge PR 779 while one commit behind develop.
  - Force-update the original branch.
  - Use wall-clock sleeps or network data to model latency.
  - Treat repository simulation as real exchange submission evidence.
  - Modify runner, Risk Core, shared execution contracts, exports or CI outside assigned ownership.
changed_paths:
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
validation:
  - command: AI Platform CI run 30538061822
    result: PASS
    evidence: Compile, full tests, Ruff, format, codespell and JSON validation passed.
  - command: Portal Universal E2E run 30538061770
    result: PASS
    evidence: Deterministic backend scenario and critical Chromium journey passed.
  - command: GitHub Actions Security Analysis run 30538061796
    result: PASS
    evidence: Zizmor completed successfully.
  - command: Freqtrade CI run 30538061837
    result: PASS
    evidence: Pre-commit, docs, Python 3.11-3.14 core tests, coverage, distributions and CI Gate passed.
  - command: compare develop...agent/closure-simulator-restack
    result: PASS
    evidence: Branch is ahead, not behind, mergeable, and changes exactly ten assigned paths.
blockers: []
next_action: Merge PR 787 normally after all required checks on the final checkpoint head are green.
```
