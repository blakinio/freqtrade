---
task_id: FTAI-20260722-portal-p10-simulator-e2e
status: active
branch: feat/portal-p10-simulator-e2e
base_branch: feat/portal-p9-learning-loop
created: 2026-07-22
updated: 2026-07-22
related_pr: null
owned_paths:
  - ai_platform/portal/simulator/
  - tests/ai_platform/portal/simulator/
  - docs/ai_platform/portal/DETERMINISTIC_SIMULATOR_E2E.md
  - docs/agents/tasks/FTAI-20260722-portal-p10-simulator-e2e.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/AGENT_EXECUTION_PLAN.md
  - docs/ai_platform/portal/DELIVERY_ROADMAP.md
  - docs/ai_platform/portal/E2E_AND_AUTONOMOUS_VALIDATION_ARCHITECTURE.md
search_first:
  - current P7.2, P8 and P9 merge state before final P10 integration
  - existing simulator or scenario ownership overlap
  - current Portal Web Playwright harness and private execution boundary
optional_reads:
  - production Freqtrade order-submission implementation only if P10 simulator isolation is blocked
---

# AI Trading Portal P10 — Deterministic Simulator and Universal E2E

## Goal

Deliver deterministic no-capital exchange simulation and a universal scenario that proves bot -> risk -> simulated execution -> post-trade intelligence -> bounded learning candidate while preserving failure evidence and active model immutability.

## Acceptance criteria

1. Scenario manifests pin deterministic market ticks and identities.
2. Simulator accepts only approved execution intent and exposes trusted server-side risk snapshot facts.
3. Universal scenario executes a simulated trade and produces normalized synchronized PNL outcome.
4. P8 analysis and P9 learning candidate are produced from the simulated outcome.
5. Candidate creation cannot mutate the bot's active model assignment.
6. First scenario failure evidence preserves scenario/correlation/stage/reason without silent retry.
7. No fixed sleeps are used for readiness.
8. No live exchange credentials or live-capital path are introduced.
9. Critical browser/security E2E remains covered by the Portal Web Playwright harness after P7.2 synchronization.
10. Required tests and repository CI pass before final merge/handoff.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-22T23:50:00+02:00
head: f4e7dd2ca6fd42537734a6ac63229e9ff0f0b0ac
branch: feat/portal-p10-simulator-e2e
pr: none
status: active
context_routes:
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/AGENT_EXECUTION_PLAN.md
  - docs/ai_platform/portal/DELIVERY_ROADMAP.md
  - docs/ai_platform/portal/E2E_AND_AUTONOMOUS_VALIDATION_ARCHITECTURE.md
proven:
  - P10 branch is intentionally stacked on P9 so the full P8/P9 provenance workflow can be exercised before sequential merges complete.
  - DeterministicExchangeSimulator derives risk snapshot exposure from explicit market ticks and accepts ApprovedExecutionIntent only.
  - UniversalScenarioRunner creates a dry-run bot and risk policy, executes deterministic risk approval and simulated trade, records P8 analysis, creates P9 hypothesis/experiment/candidate, and asserts the active model is unchanged.
  - Scenario manifests and first-failure reports use explicit correlation identity and no fixed sleeps.
  - Production Freqtrade order submission remains outside P10 simulator authority and remains fail-closed.
derived:
  - After P7.2/P8/P9 merge, P10 must synchronize with develop and re-run Web, AI Platform, Freqtrade and zizmor gates on the final integrated head.
unknown: []
conflicts: []
first_failure:
  marker: none
  evidence: P10 executable CI has not run yet.
changed_paths:
  - ai_platform/portal/simulator/__init__.py
  - ai_platform/portal/simulator/exchange.py
  - ai_platform/portal/simulator/runner.py
  - ai_platform/portal/simulator/schema.py
  - tests/ai_platform/portal/simulator/scenarios/profitable.json
  - tests/ai_platform/portal/simulator/test_universal_scenario.py
  - docs/ai_platform/portal/DETERMINISTIC_SIMULATOR_E2E.md
  - docs/agents/tasks/FTAI-20260722-portal-p10-simulator-e2e.md
validation: []
blockers:
  - Final P10 integration must wait for sequential P7.2, P8 and P9 merges because this branch is intentionally stacked on P9 and does not yet contain the final merged P7.2 terminal surface.
next_action: Open the stacked P10 PR against P9, validate the deterministic simulator/E2E slice, then sequentially merge P7.2, P8 and P9, retarget/synchronize P10 to develop, run final integrated gates, update this checkpoint, validate it, and generate the compact resume output.
```
