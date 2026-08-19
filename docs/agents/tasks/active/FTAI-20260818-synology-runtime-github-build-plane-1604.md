---
task_id: FTAI-20260818-synology-runtime-github-build-plane-1604
repository: blakinio/freqtrade
issue: 1604
branch: arch/1604-synology-runtime-github-build-plane
status: validating
execution_mode: github_only
trusted_base: 6510077ea2e7a63c0d489f94391f461a3cab4ac1
pr: 1611
---

# Synology persistent runtime + GitHub-hosted build/disposable plane

## Objective

Record and reconcile the owner's 2026-08-18 decision that the current private Developer Quant Platform keeps persistent Portal/bot/application runtime on Synology while GitHub-hosted Actions remains the default for stateless/disposable CI, test, scan, build, GHCR publication and bounded workflow jobs.

## Authority and scope

- Issue #1604 records the owner decision.
- ADR-023 remains current product authority.
- ADR-025 is the proposed current runtime/CI-placement overlay and supersedes only ADR-024's separate-dedicated-Linux current target.
- PR #1609 hosted build-plane work is retained.
- Persistent application containers remain on Synology; GitHub-hosted runners are not a 24/7 application host.
- `deploy/runtime/**` remains optional future portability reference only.
- No runtime deployment, Synology mutation, runner registration/removal, secret change, model activation or capital authority is in this task.
- A deterministic test-only repair to `test_throttle_sleep_time` is in scope because exact-head required CI exposed real-wall-clock drift in the test harness; production worker behavior is unchanged.

## Risk

```yaml
risk:
  persistent_data: false
  research_integrity: false
  model_activation: false
  auth_or_secrets: false
  shared_synology_mutation: false
  deployment: false
  user_workflow_change: false
  destructive_operation: false
  real_capital: false
  governance_or_ci: true
risk_gates:
  - policy_regression
  - trusted_base_self_validation
  - independent_audit
```

## Owned paths

- `AGENTS.md`
- `ARCHITECTURE_REGISTRY.yaml`
- `deploy/runtime/README.md`
- `docs/ai_platform/portal/ADR-024_DEDICATED_LINUX_RUNTIME.md`
- `docs/ai_platform/portal/ADR-025_SYNOLOGY_PERSISTENT_RUNTIME_GITHUB_BUILD_PLANE.md`
- `docs/ai_platform/portal/ARCHITECTURE_DECISIONS.md`
- `docs/ai_platform/portal/DEVELOPER_QUANT_PORTAL_ARCHITECTURE.md`
- `docs/agents/tasks/active/FTAI-20260818-synology-runtime-github-build-plane-1604.md`
- `tests/freqtradebot/test_worker.py`

## Acceptance

- current architecture no longer requires provisioning or physical cutover to a separate dedicated Linux runtime host;
- Synology is canonical persistent runtime for Portal/bots/stateful long-lived services;
- GitHub-hosted Actions is canonical default for compatible stateless/disposable CI/build/test/scan/jobs;
- persistent containers are explicitly distinguished from short-lived workflow containers;
- Synology self-hosted runner target is narrow/deploy-only or disabled;
- ADR-024 remains truthful historical evidence and PR #1609 build-plane work remains valid;
- exact-head relevant CI and selected governance gates pass with no unresolved material finding.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-19T09:58:21+02:00
head: fbfcc48946eed111665bab0ffbce15e11b38e3b1
branch: arch/1604-synology-runtime-github-build-plane
pr: 1611
status: validating
context_routes:
  - Issue #1604 owner runtime-topology decision
  - ADR-023 current Developer Quant product authority
  - ADR-024 historical dedicated-Linux runtime decision
  - ADR-025 current Synology-runtime/GitHub-build proposal
  - PR #1609 hosted build-plane implementation evidence
  - PR #1610 compatible Liquid20 GHCR repair in progress
  - Freqtrade CI run 32153957725 attempt 2 timing-test failure and deterministic repair
owned_paths:
  - AGENTS.md
  - ARCHITECTURE_REGISTRY.yaml
  - deploy/runtime/README.md
  - docs/ai_platform/portal/ADR-024_DEDICATED_LINUX_RUNTIME.md
  - docs/ai_platform/portal/ADR-025_SYNOLOGY_PERSISTENT_RUNTIME_GITHUB_BUILD_PLANE.md
  - docs/ai_platform/portal/ARCHITECTURE_DECISIONS.md
  - docs/ai_platform/portal/DEVELOPER_QUANT_PORTAL_ARCHITECTURE.md
  - docs/agents/tasks/active/FTAI-20260818-synology-runtime-github-build-plane-1604.md
  - tests/freqtradebot/test_worker.py
risk:
  persistent_data: false
  research_integrity: false
  model_activation: false
  auth_or_secrets: false
  shared_synology_mutation: false
  deployment: false
  user_workflow_change: false
  destructive_operation: false
  real_capital: false
  governance_or_ci: true
risk_gates:
  - policy_regression
  - trusted_base_self_validation
  - independent_audit
authority_freeze:
  current_base_commit: 6510077ea2e7a63c0d489f94391f461a3cab4ac1
  note: Governance and CI acceptance remain frozen to the trusted develop base active when #1604 execution began; the task cannot use ADR-025 itself to waive exact-head CI or audit.
proven:
  - develop trusted base is 6510077ea2e7a63c0d489f94391f461a3cab4ac1
  - PR #1609 already moved portable Portal WickHunter and Liquid20 build publication toward GitHub-hosted runners
  - Issue #1604 records that a separate dedicated Linux host is not current target authority
  - PR #1611 was opened from the exact trusted base
  - architecture/governance diff audit passed on e0aee0daa6f4b3378ad2e34f8a84715a2e3b76b2 before the CI-only test repair
  - Risk-aware component CI CodeQL and zizmor passed on e0aee0daa6f4b3378ad2e34f8a84715a2e3b76b2
  - Freqtrade CI attempt 2 completed 7007 tests successfully and exposed one timing-only failure in test_throttle_sleep_time
  - time-machine 3.2.0 travel defaults to tick true so real runner elapsed time was included in the synthetic wall clock
  - commit fbfcc48946eed111665bab0ffbce15e11b38e3b1 changes only test_throttle_sleep_time from default ticking to tick false; freqtrade/worker.py is unchanged
derived:
  - PR #1610 remains implementation-compatible because it builds on GitHub-hosted Linux and deploys an immutable image to Synology
  - tick false makes the throttle test depend only on explicit Traveller.shift/move_to operations rather than GitHub runner scheduling delay
unknown:
  - exact-head CI result after the deterministic timing-test repair and this checkpoint update
  - fresh final-diff audit disposition on the final head that includes the test repair
conflicts: []
first_failure:
  marker: tests/freqtradebot/test_worker.py::test_throttle_sleep_time
  evidence: Freqtrade CI run 32153957725 attempt 2 job 95992736703 failed 1 of 7041 selected tests because expected approximately 4 seconds sleep was 3.215940237045288 after real elapsed time advanced a default-ticking time-machine clock
rejected_hypotheses:
  - use GitHub-hosted Actions as a 24/7 Portal or bot runtime
  - provision a separate Linux host solely to satisfy superseded ADR-024
  - revert the already merged GitHub-hosted build-plane work from PR #1609
  - attribute the CI failure to ADR-025 runtime semantics or production Worker behavior
  - weaken the throttle assertion tolerances to mask runner load
changed_paths:
  - AGENTS.md
  - ARCHITECTURE_REGISTRY.yaml
  - deploy/runtime/README.md
  - docs/ai_platform/portal/ADR-024_DEDICATED_LINUX_RUNTIME.md
  - docs/ai_platform/portal/ADR-025_SYNOLOGY_PERSISTENT_RUNTIME_GITHUB_BUILD_PLANE.md
  - docs/ai_platform/portal/ARCHITECTURE_DECISIONS.md
  - docs/ai_platform/portal/DEVELOPER_QUANT_PORTAL_ARCHITECTURE.md
  - docs/agents/tasks/active/FTAI-20260818-synology-runtime-github-build-plane-1604.md
  - tests/freqtradebot/test_worker.py
validation:
  - command: compare develop to architecture branch and inspect PR #1611 architecture diff
    result: PASS
    evidence: architecture scope matched owner decision and prior exact-head final-diff audit found no unresolved material finding
  - command: Freqtrade CI run 32153957725 attempt 2 on e0aee0daa6f4b3378ad2e34f8a84715a2e3b76b2
    result: FAIL
    evidence: 7007 passed 33 skipped 394 deselected and one flaky timing assertion failed in test_throttle_sleep_time; no product/runtime implementation failure
  - command: compare e0aee0daa6f4b3378ad2e34f8a84715a2e3b76b2..fbfcc48946eed111665bab0ffbce15e11b38e3b1
    result: PASS
    evidence: exactly one file changed with one insertion and one deletion in tests/freqtradebot/test_worker.py
  - command: exact-head repository CI after timing repair and checkpoint update
    result: NOT_RUN
    evidence: new final head must be validated after this checkpoint commit
blockers: []
next_action: Validate the new exact PR head; if required CI is green, perform a fresh final-diff audit and squash-merge PR #1611 to develop.
```
