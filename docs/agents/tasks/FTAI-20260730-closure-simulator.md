---
task_id: FTAI-20260730-closure-simulator
status: active
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
updated_at: 2026-07-30T13:20:00+02:00
head: 3f30b9f376280cf8368907e539d8082f2998b03a
branch: agent/closure-simulator-restack
pr: 787
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
  - Gate 0 is merged and the dispatch table marks closure-simulator READY with no dependencies.
  - PR 779 passed AI Platform CI, Portal Universal E2E, security and the complete Freqtrade CI gate on its exact head.
  - Develop then advanced only in five disjoint time-leakage paths through merged PR 777.
  - PR 787 is a no-force restack from develop commit 979744f1143246bd42e42fc2213c7e79fc68ea57.
  - Versioned cost, latency, funding and gap-stop models remain simulation-only and fail closed.
  - Zero-cost, zero-latency and no-stop defaults preserve the existing universal scenario result.
  - Same manifest and seed produce canonical evidence with deterministic UUID5 identities and SHA-256.
derived:
  - Positive funding is a cash outflow for BUY positions and an inflow for SELL positions.
  - A stop crossed between discrete ticks fills at the adverse observed price.
  - Scenario latency uses the first tick at or after readiness and raises when no tick exists.
unknown:
  - Exact-head CI conclusions for restacked PR 787.
conflicts: []
first_failure:
  marker: BASE_ADVANCED_AFTER_GREEN_CI
  evidence: Develop advanced by merged PR 777 after PR 779 became green; the connector could not create a normal merge commit without a tree SHA, so the work was restacked without force-push.
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
  - command: AI Platform CI run 30536561953 on PR 779 exact head
    result: PASS
    evidence: Compile, tests, Ruff, format, codespell and JSON validation passed.
  - command: Portal Universal E2E run 30536561940 on PR 779 exact head
    result: PASS
    evidence: Deterministic backend scenario and critical Chromium journey passed.
  - command: GitHub Actions Security Analysis run 30536562029 on PR 779 exact head
    result: PASS
    evidence: Zizmor completed successfully.
  - command: Freqtrade CI run 30536561954 on PR 779 exact head
    result: PASS
    evidence: Pre-commit, docs, Python 3.11-3.14 core tests, coverage, distributions and CI Gate passed.
  - command: compare 91ddbf60...979744f1
    result: PASS
    evidence: The new develop commit changes five time-leakage paths with no overlap with simulator ownership.
blockers: []
next_action: Run all required workflows on PR 787 exact head, finalize the checkpoint as ready, close superseded PR 779, and merge PR 787 normally.
```
