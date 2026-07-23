---
task_id: FTAI-20260722-portal-p10-simulator-e2e
status: active
branch: feat/portal-p10-simulator-e2e-final
base_branch: develop
created: 2026-07-22
updated: 2026-07-23
related_pr: "#170"
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
  - current develop and open PRs/tasks overlapping simulator/E2E ownership
  - current Portal Web Playwright harness and private execution boundary
  - current merged P7 risk, P8 intelligence and P9 learning contracts
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
updated_at: 2026-07-23T10:45:00+02:00
head: 65c2a48b6113e1d475c2277cdd0bd9e9d7358201
branch: feat/portal-p10-simulator-e2e-final
pr: "#170"
status: validating
context_routes:
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/AGENT_EXECUTION_PLAN.md
  - docs/ai_platform/portal/DELIVERY_ROADMAP.md
  - docs/ai_platform/portal/E2E_AND_AUTONOMOUS_VALIDATION_ARCHITECTURE.md
owned_paths:
  - ai_platform/portal/simulator/
  - tests/ai_platform/portal/simulator/
  - .github/workflows/portal-universal-e2e.yml
  - docs/ai_platform/portal/DETERMINISTIC_SIMULATOR_E2E.md
  - docs/agents/tasks/FTAI-20260722-portal-p10-simulator-e2e.md
proven:
  - P7.2 risk-gated trading terminal is merged to develop as 0e4c4f1ff3ac574efaba218d4fb78fd2e2944a8b.
  - P8 trade intelligence is merged to develop as 0c0a9e28598f60d61bf4e75bbd4d5c8bba8dc456.
  - P9 safe continual learning is merged to develop as 41857e7d4eb9ce72f74ca99941fff6e292308569.
  - Final PR #170 is recreated directly from merged P9 develop and its diff contains only the 11 declared P10 paths.
  - DeterministicExchangeSimulator derives trusted risk snapshot exposure from explicit market ticks and accepts ApprovedExecutionIntent only.
  - UniversalScenarioRunner creates a dry-run bot and risk policy, executes simulated trade, records P8 analysis, creates a bounded P9 candidate and asserts active model immutability.
  - Portal Universal E2E uses read-only workflow permissions and runs backend deterministic scenario plus Chromium Playwright journeys.
derived:
  - Final merge is allowed only after required CI validates the clean PR #170 merge-state and the branch remains current with develop.
unknown: []
conflicts: []
first_failure:
  marker: ruff-e501
  evidence: The earlier stacked P10 validation passed simulator tests and Universal E2E but Ruff rejected an overlong result_summary line; the line was wrapped before recreating final PR #170.
rejected_hypotheses:
  - Merge stacked PR #159 after retargeting even though its diff duplicated already-merged P9 files.
  - Use live exchange credentials or production order submission to validate P10.
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
validation:
  - command: P9 PR #158 required CI
    result: PASS
    evidence: AI Platform CI 29990377687, Freqtrade CI 29990377694 and zizmor 29990377697 passed before squash-merge.
  - command: compare develop...feat/portal-p10-simulator-e2e-final before PR #170 validation
    result: PASS
    evidence: behind_by=0 and exactly 11 P10-owned files differ from develop.
  - command: Earlier stacked P10 Portal Universal E2E 29963597670
    result: PASS
    evidence: Backend deterministic scenario and Chromium journey passed before clean-branch recreation.
blockers: []
next_action: Validate all required AI Platform, Freqtrade, Portal Universal E2E and zizmor gates on clean PR #170, fix only evidence-backed failures, verify current develop and review state, then squash-merge P10 and write the final validated compact checkpoint with exactly one P11 next_action.
```
