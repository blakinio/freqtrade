---
task_id: FTAI-20260722-portal-p10-simulator-e2e
status: active
branch: feat/portal-p10-simulator-e2e-clean
base_branch: feat/portal-p9-learning-loop-clean
created: 2026-07-22
updated: 2026-07-22
related_pr: null
owned_paths:
  - ai_platform/portal/simulator/
  - tests/ai_platform/portal/simulator/
  - .github/workflows/portal-universal-e2e.yml
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
  - current P9 merge state and open PRs/tasks overlapping simulator/E2E ownership
  - current Portal Web Playwright harness and private execution boundary
  - current merged P7 risk/terminal and P8 trade-intelligence contracts
optional_reads:
  - production Freqtrade order-submission implementation only if simulator isolation is blocked
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
9. Critical browser/security E2E is exercised through the permanent Portal Universal E2E workflow.
10. Required tests and repository CI pass before final merge/handoff.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-22T23:55:00+02:00
head: 0a72c5401af1baf48531f7362f394a41fffbbf84
branch: feat/portal-p10-simulator-e2e-clean
pr: none
status: active
context_routes:
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/AGENT_EXECUTION_PLAN.md
  - docs/ai_platform/portal/DELIVERY_ROADMAP.md
  - docs/ai_platform/portal/E2E_AND_AUTONOMOUS_VALIDATION_ARCHITECTURE.md
proven:
  - P7.2 risk-gated trading terminal merged to develop as 0e4c4f1ff3ac574efaba218d4fb78fd2e2944a8b.
  - P8 trade intelligence merged to develop as 0c0a9e28598f60d61bf4e75bbd4d5c8bba8dc456.
  - P10 clean branch is based on the final clean P9 head so P9 content should collapse from the P10 diff after P9 squash-merge.
  - DeterministicExchangeSimulator derives risk snapshot exposure from explicit market ticks and accepts ApprovedExecutionIntent only.
  - UniversalScenarioRunner creates a dry-run bot and risk policy, executes deterministic risk approval and simulated trade, records P8 analysis, creates P9 hypothesis/experiment/candidate, and asserts the active model is unchanged.
  - Scenario manifests and first-failure reports use explicit correlation identity and no fixed sleeps.
  - Portal Universal E2E adds both deterministic backend scenario validation and the existing Chromium Playwright journey with read-only workflow permissions.
derived:
  - After P9 merges, P10 must be retargeted/synchronized to develop and its final diff verified to contain only P10-owned paths plus the permanent universal E2E workflow.
unknown: []
conflicts: []
first_failure:
  marker: none
  evidence: Clean P10 executable CI has not run yet.
changed_paths:
  - .github/workflows/portal-universal-e2e.yml
  - ai_platform/portal/simulator/__init__.py
  - ai_platform/portal/simulator/exchange.py
  - ai_platform/portal/simulator/runner.py
  - ai_platform/portal/simulator/schema.py
  - tests/ai_platform/portal/simulator/scenarios/profitable.json
  - tests/ai_platform/portal/simulator/test_universal_scenario.py
  - tests/ai_platform/portal/simulator/visual_acceptance_baseline.json
  - tests/ai_platform/portal/simulator/test_visual_baseline.py
  - docs/ai_platform/portal/DETERMINISTIC_SIMULATOR_E2E.md
  - docs/agents/tasks/FTAI-20260722-portal-p10-simulator-e2e.md
validation: []
blockers:
  - Final P10 merge-state validation waits for clean P9 PR #158 to merge to develop.
next_action: Open the clean stacked P10 PR against the clean P9 branch, validate P10 independently, merge P9 when its required gates pass, retarget P10 to develop, verify a P10-only diff, run final integrated gates, then update and validate this checkpoint before generating resume.py output.
```
