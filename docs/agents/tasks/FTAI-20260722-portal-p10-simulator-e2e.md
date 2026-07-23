---
task_id: FTAI-20260722-portal-p10-simulator-e2e
status: active
branch: feat/portal-p10-simulator-e2e-final
base_branch: develop
created: 2026-07-22
updated: 2026-07-23
related_pr: "#171"
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
updated_at: 2026-07-23T11:37:00+02:00
head: cdf254ea80f75da2aa4e7ae252cbd8d176570f46
branch: feat/portal-p10-simulator-e2e-final
pr: "#171"
status: ready
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
  - Final clean PR #171 differs from develop only in the 11 declared P10 paths and was 0 commits behind develop before this checkpoint-only update.
  - DeterministicExchangeSimulator derives trusted risk snapshot exposure from explicit market ticks and accepts ApprovedExecutionIntent only.
  - UniversalScenarioRunner creates a dry-run bot and risk policy, executes simulated trade, records P8 analysis, creates a bounded P9 candidate and asserts active model immutability.
  - Portal Universal E2E uses read-only workflow permissions and validates the deterministic backend scenario plus Chromium Playwright journeys.
  - No live exchange credentials, live capital, protected final holdout evaluation, model promotion or production order-submission bypass is introduced.
derived:
  - This checkpoint-only task-record change must be revalidated on PR #171 merge-state before squash-merge.
unknown: []
conflicts: []
first_failure:
  marker: resolved-ruff-format
  evidence: Earlier clean P10 runs exposed one E501 test-name violation and then Ruff format drift; the test name was shortened and canonical Ruff formatting was applied before final implementation validation.
rejected_hypotheses:
  - Merge stacked PR #159 after retargeting even though its diff duplicated already-merged P9 files.
  - Merge superseded PR #170 after GitHub failed to generate required check-runs for that PR.
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
  - command: AI Platform CI 29994058848
    result: PASS
    evidence: Full AI Platform tests, Ruff, Ruff format and remaining validation steps passed on implementation head cdf254ea80f75da2aa4e7ae252cbd8d176570f46.
  - command: Freqtrade CI 29994058839
    result: PASS
    evidence: Pre-commit, CI scope, documentation and full required platform matrix passed on implementation head cdf254ea80f75da2aa4e7ae252cbd8d176570f46.
  - command: Portal Universal E2E 29994058988
    result: PASS
    evidence: Deterministic backend universal scenario and Chromium journey passed on implementation head cdf254ea80f75da2aa4e7ae252cbd8d176570f46.
  - command: GitHub Actions Security Analysis with zizmor 29994059019
    result: PASS
    evidence: Workflow security analysis passed on implementation head cdf254ea80f75da2aa4e7ae252cbd8d176570f46.
  - command: compare develop...feat/portal-p10-simulator-e2e-final
    result: PASS
    evidence: Before the checkpoint-only update, behind_by=0 and exactly 11 P10-owned files differed from develop.
blockers: []
next_action: Verify required CI and review/base state on this checkpoint-only PR #171 head, squash-merge P10 if green, then start the P11 Cloudflare production-like staging preflight from current develop without enabling live capital.
```
