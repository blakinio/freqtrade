---
task_id: FTAI-20260722-portal-p10-simulator-e2e
status: done
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
updated_at: 2026-07-23T12:01:00+02:00
head: 4c1971d9eced5913ed4fb6121d351c30e63ba9c2
branch: develop
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
  - P10 was squash-merged from PR #171 to develop as 4c1971d9eced5913ed4fb6121d351c30e63ba9c2.
  - DeterministicExchangeSimulator derives trusted risk snapshot exposure from explicit market ticks and accepts ApprovedExecutionIntent only.
  - UniversalScenarioRunner creates a dry-run bot and risk policy, executes simulated trade, records P8 analysis, creates a bounded P9 candidate and asserts active model immutability.
  - Portal Universal E2E uses read-only workflow permissions and validates the deterministic backend scenario plus Chromium Playwright journeys.
  - No live exchange credentials, live capital, protected final holdout evaluation, model promotion or production order-submission bypass was introduced.
derived:
  - P11 may now start from current develop because P10 implementation and checkpoint merge-state validation are complete.
unknown: []
conflicts: []
first_failure:
  marker: resolved-ruff-format
  evidence: Clean P10 validation exposed one E501 test-name violation and Ruff format drift; both were fixed before final green CI and merge.
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
  - command: AI Platform CI 29996127747
    result: PASS
    evidence: Final checkpoint-only merge-state validation passed on PR #171 head 0581b4c153aa30e9c6bb6e062bd0bc8411a7a25b.
  - command: Freqtrade CI 29996127760
    result: PASS
    evidence: Pre-commit, CI scope, documentation and full required platform matrix passed on final PR #171 head.
  - command: Portal Universal E2E 29996127777
    result: PASS
    evidence: Backend deterministic scenario and Chromium journey passed on final PR #171 head.
  - command: GitHub Actions Security Analysis with zizmor 29996127734
    result: PASS
    evidence: Workflow security analysis passed on final PR #171 head.
blockers: []
next_action: Declare and implement P11 Cloudflare production-like staging from current develop, keeping execution simulated and requiring owner-approved external Cloudflare resources before claiming live staging acceptance.
```
