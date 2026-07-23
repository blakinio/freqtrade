---
task_id: FTAI-20260723-portal-p12-autonomous-repair-simulation-first
status: done
branch: develop
base_branch: develop
created: 2026-07-23
updated: 2026-07-23
related_pr: "#221"
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
  - current develop and P12 quality-agent implementation
  - P12 seeded repair acceptance evidence
optional_reads: []
---

# AI Trading Portal P12 — Simulation-First Autonomous Diagnosis and Bounded Repair

## Goal

Implement deterministic simulation-first diagnosis and bounded repair from P10/local/CI evidence without claiming real P11 Cloudflare acceptance or granting production deployment authority.

## Delivered

- typed diagnosis records for P10 first-failure evidence;
- deterministic product/test/environment/dependency/ambiguous classification;
- explicit reproducibility state;
- regression-test-first repair policy;
- owned-path and path-traversal enforcement;
- isolated `agent/...` repair branch metadata;
- explicit validation routing metadata;
- fail-closed rejection of safety weakening, production deployment, production credential access, live-capital enablement and false real-P11 acceptance claims;
- dedicated P12 validation workflow and simulation-first operational documentation.

## Non-negotiable boundaries

- Simulation/local/CI evidence remains labeled non-production.
- P12 does not deploy production or access production exchange credentials.
- Mandatory safety assertions cannot be weakened merely to make a test pass.
- Real P11 External E2E remains a separate deferred production-like staging gate.
- Protected final holdout and frozen research boundaries remain unchanged.

## Acceptance criteria

1. P10 `ScenarioFailureEvidence` is converted into typed deterministic diagnosis.
2. Repair authorization requires reproduced evidence, regression coverage, owned paths and validation commands.
3. Unsafe repair proposals fail closed.
4. Repair metadata is attributable to task/branch/correlation evidence.
5. Product/test/environment/dependency/ambiguous classification and denial paths are tested.
6. A seeded non-security simulator defect was reproduced, diagnosed, regression-tested before repair, minimally repaired and validated without weakening safety assertions.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-23T19:15:00+02:00
head: 1e724be35ce856d93b590415b9bb3860634d8993
branch: develop
pr: "#221"
status: done
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
  - PR #205 authorized simulation-first P12 while retaining real P11 External E2E as a later mandatory gate.
  - PR #215 durably recorded the owner-approved P11 infrastructure deferral.
  - Stale foundation PR #207 was closed and replaced rather than force-merged.
  - Foundation recovery PR #221 restored the exact seven bounded P12 files to live develop and squash-merged as 4f4389c103eb51de2a63f368815b6dea2d38546d.
  - PR #221 passed Portal P12 Simulation-First Validation 30024638442, AI Platform CI 30024638754, zizmor 30024638500 and Freqtrade CI 30024638000.
  - Seeded provenance PR #217 preserved the intentional defect, expected failing evidence, diagnosis and minimal repair history and was closed unmerged.
  - Final clean acceptance PR #222 contained exactly the durable regression test and attributable evidence record and squash-merged as 1e724be35ce856d93b590415b9bb3860634d8993.
  - PR #222 passed AI Platform CI 30025621176, Portal Universal E2E 30025621171, zizmor 30025621161 and Freqtrade CI 30025621399.
  - The seeded failure reason `simulated trade did not close after opening` was classified as high-confidence product_defect in the simulator layer.
  - The minimal repair restored only the declared exit timestamp; the existing safety assertion and new regression test remained intact.
derived:
  - P12 simulation-first acceptance criteria are satisfied.
  - P12 completion does not satisfy or replace deferred real P11 external staging acceptance.
unknown: []
conflicts: []
first_failure:
  marker: simulated-trade-did-not-close-after-opening
  evidence: Seeded PR #217 failed AI Platform CI 30021875591 and Portal Universal E2E backend scenario 30021875771 before repair; repaired validation later passed.
rejected_hypotheses:
  - Treat simulated evidence as proof of real P11 Cloudflare acceptance.
  - Weaken or delete mandatory safety assertions.
  - Merge the intentionally defective provenance branch.
  - Force stale/divergent branches into develop instead of replaying bounded outputs through CI.
changed_paths:
  - ai_platform/portal/quality_agent/__init__.py
  - ai_platform/portal/quality_agent/schema.py
  - ai_platform/portal/quality_agent/service.py
  - tests/ai_platform/portal/quality_agent/test_quality_agent_service.py
  - .github/workflows/portal-p12-simulation-first.yml
  - docs/ai_platform/portal/AUTONOMOUS_REPAIR_SIMULATION_FIRST.md
  - docs/agents/tasks/FTAI-20260723-portal-p12-autonomous-repair-simulation-first.md
validation:
  - command: Portal P12 Simulation-First Validation 30024638442
    result: PASS
    evidence: Bounded checkpoint, targeted P12 tests, full AI Platform compatibility, Ruff, Ruff format and codespell passed on the recovered foundation.
  - command: AI Platform CI 30024638754
    result: PASS
    evidence: Foundation full AI Platform tests and lint passed.
  - command: GitHub Actions Security Analysis with zizmor 30024638500
    result: PASS
    evidence: Foundation workflow security analysis passed.
  - command: Freqtrade CI 30024638000
    result: PASS
    evidence: Foundation required repository CI gate passed.
  - command: AI Platform CI 30025621176
    result: PASS
    evidence: Final clean seeded-repair acceptance head passed full AI Platform tests and lint.
  - command: Portal Universal E2E 30025621171
    result: PASS
    evidence: Final clean seeded-repair acceptance passed deterministic backend and Chromium journey.
  - command: GitHub Actions Security Analysis with zizmor 30025621161
    result: PASS
    evidence: Final acceptance workflow security analysis passed.
  - command: Freqtrade CI 30025621399
    result: PASS
    evidence: Final acceptance required repository CI gate passed.
blockers: []
next_action: Keep P11 deferred until the owner starts the real infrastructure phase, and declare P13 only if measured requirements justify scale/service extraction.
```
