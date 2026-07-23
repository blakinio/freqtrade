---
task_id: FTAI-20260723-portal-p12-autonomous-repair-simulation-first
status: active
branch: feat/portal-p12-simulation-first-repair-20260723
base_branch: develop
created: 2026-07-23
updated: 2026-07-23
related_pr: "#207"
owned_paths:
  - ai_platform/portal/quality_agent/
  - tests/ai_platform/portal/quality_agent/
  - .github/workflows/portal-p12-simulation-first.yml
  - docs/ai_platform/portal/AUTONOMOUS_REPAIR_SIMULATION_FIRST.md
  - docs/agents/tasks/FTAI-20260723-portal-p12-autonomous-repair-simulation-first.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/QUALITY_AND_AUTONOMOUS_E2E.md
  - docs/ai_platform/portal/AGENT_EXECUTION_PLAN.md
  - docs/ai_platform/portal/DETERMINISTIC_SIMULATOR_E2E.md
  - ai_platform/portal/simulator/schema.py
  - ai_platform/portal/simulator/runner.py
search_first:
  - existing P12 quality-agent implementation
  - P10 deterministic failure evidence contracts
optional_reads: []
---

# AI Trading Portal P12 — Simulation-First Autonomous Diagnosis and Bounded Repair

## Goal

Implement the first deterministic P12 diagnosis and repair-planning boundary using P10 simulated/local/CI failure evidence, without claiming real P11 Cloudflare acceptance and without granting production deployment authority.

## Deliverables

- typed diagnosis records for P10 first-failure evidence;
- deterministic failure classification;
- simulation-first repair-plan contract;
- regression-test-first enforcement;
- owned-path enforcement;
- explicit rejection of security weakening, production deployment, secret access and live-capital actions;
- isolated branch naming and validation routing metadata;
- tests for safe and unsafe repair proposals;
- simulation-first operational documentation.

## Non-negotiable boundaries

- Input evidence is simulated/local/CI only for this work package.
- P12 output may propose bounded fixes and PR metadata; it does not deploy production.
- Simulated evidence cannot prove real Cloudflare Tunnel, Access, WAF, origin firewall or direct-Freqtrade denial.
- Mandatory safety assertions cannot be weakened merely to make a test pass.
- A repair proposal without a regression test or outside declared owned paths is rejected.
- No live capital, production exchange secrets or protected final holdout access.

## Acceptance criteria

1. P10 `ScenarioFailureEvidence` can be deterministically converted into a typed diagnosis record.
2. A safe simulation-first repair proposal requires reproducible evidence, at least one regression test, owned changed paths and explicit validation commands.
3. Unsafe proposals are rejected for path escape, missing regression tests, security weakening, production deployment, secret access or live-capital enablement.
4. Repair metadata includes an isolated task branch name and PR evidence summary without performing deployment.
5. Tests cover product/test/environment/dependency/ambiguous classification and repair-policy denial paths.
6. Real P11 External E2E remains explicitly outside the evidence claims of this task.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-23T17:25:00+02:00
head: 5ff78a32459ed560fa3089b4bdbbd2a589f148e1
branch: feat/portal-p12-simulation-first-repair-20260723
pr: "#207"
status: validating
context_routes:
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/QUALITY_AND_AUTONOMOUS_E2E.md
  - docs/ai_platform/portal/AGENT_EXECUTION_PLAN.md
  - docs/ai_platform/portal/DETERMINISTIC_SIMULATOR_E2E.md
owned_paths:
  - ai_platform/portal/quality_agent/
  - tests/ai_platform/portal/quality_agent/
  - .github/workflows/portal-p12-simulation-first.yml
  - docs/ai_platform/portal/AUTONOMOUS_REPAIR_SIMULATION_FIRST.md
  - docs/agents/tasks/FTAI-20260723-portal-p12-autonomous-repair-simulation-first.md
proven:
  - PR #205 merged as 5ff78a32459ed560fa3089b4bdbbd2a589f148e1 and authorizes P12 simulation-first sequencing while retaining real P11 External E2E as the production-like staging acceptance gate.
  - P10 exposes ScenarioFailureEvidence with scenario_id, correlation_id, stage and reason_code and preserves first failure without retry or sleep.
  - Current develop had no ai_platform/portal/quality_agent implementation before this task.
  - PR #207 adds typed diagnosis/repair contracts, deterministic classification, fail-closed repair policy, targeted tests, a bounded evidence-capture workflow and simulation-first documentation within declared P12 paths.
  - The first full-suite failure was a pytest module-name collision between quality_agent/test_service.py and control_plane/test_service.py; targeted P12 tests passed and the test file was renamed to a unique module name.
derived:
  - P12 can evaluate bounded repair proposals from deterministic P10/local/CI evidence without requiring real external infrastructure.
  - The module-name failure was a test-collection defect rather than a product defect; renaming the P12 test module preserves test semantics and removes the collision.
unknown: []
conflicts: []
first_failure:
  marker: pytest-module-name-collision
  evidence: Full AI Platform pytest collection imported tests/ai_platform/portal/control_plane/test_service.py as test_service before reaching the P12 file with the same basename; the bounded fix renames only the P12 test module.
rejected_hypotheses:
  - Treat simulated P10 evidence as proof that real P11 Cloudflare staging passed.
  - Give the diagnosis module direct production deployment authority.
  - Permit repairs outside the declared task-owned paths.
  - Permit assertion weakening without an intentional separately reviewed contract change.
changed_paths:
  - ai_platform/portal/quality_agent/__init__.py
  - ai_platform/portal/quality_agent/schema.py
  - ai_platform/portal/quality_agent/service.py
  - tests/ai_platform/portal/quality_agent/test_quality_agent_service.py
  - .github/workflows/portal-p12-simulation-first.yml
  - docs/ai_platform/portal/AUTONOMOUS_REPAIR_SIMULATION_FIRST.md
  - docs/agents/tasks/FTAI-20260723-portal-p12-autonomous-repair-simulation-first.md
validation:
  - command: Portal P12 Simulation-First Validation targeted tests 30018431416
    result: PASS
    evidence: Targeted P12 tests and bounded checkpoint validation passed before the full-suite compatibility gate exposed the pytest module-name collision.
  - command: Portal P12 Simulation-First Validation full AI suite 30018431416
    result: FAIL
    evidence: First full-suite failure was pytest import-file mismatch caused by duplicate test_service.py basenames; no product assertion ran before collection failed.
  - command: AI Platform CI
    result: NOT_RUN
    evidence: Final-head validation after the unique test-module rename is pending.
  - command: Freqtrade CI
    result: NOT_RUN
    evidence: Final-head validation after the unique test-module rename is pending.
  - command: GitHub Actions Security Analysis with zizmor
    result: NOT_RUN
    evidence: Final-head validation after the unique test-module rename is pending.
blockers: []
next_action: Verify PR #207 targeted P12 validation, full AI Platform compatibility, AI Platform CI, Freqtrade CI and zizmor on the final renamed-test head, then merge the PR if all required gates are green.
```
