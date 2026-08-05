# FTAI-20260805 Platform Continuous Assurance

```yaml
task_id: FTAI-20260805-platform-continuous-assurance
programme_id: FTAI-20260805-platform-continuous-assurance
repository: blakinio/freqtrade
project_lane: freqtrade-assurance
task_kind: continuous_assurance_program
phase: validate_and_coordinate
status: waiting
priority: high
prompting_standard_version: 2.1
execution_policy_version: 2
context_pressure: medium
decomposition_decision: bounded_waves
execution_mode: github_only
run_scope: autonomous_program
continuation_policy: continue_until_real_stop
task_completion_policy: checkpoint_and_continue
user_communication: terminal_only
base_branch: develop
base_head: 108eff8149f3c5dba77bfcdeaea0c63c8a22b551
branch: audit/platform-continuous-assurance-wave-004-20260805
current_wave: wave-004-focused-core-ci-contract-repair
current_findings: [1250, 1257, 1265]
current_prs: [1215, 1258, 1271]
owned_paths:
  - docs/agents/tasks/active/FTAI-20260805-platform-continuous-assurance.md
  - docs/agents/programs/FTAI_PLATFORM_CONTINUOUS_ASSURANCE_COVERAGE.md
shared_path_leases: []
live_capital_authorized: false
withdrawals_enabled: false
protected_production_deployment_authorized: false
```

## Objective

Continuously audit the complete Quant Platform repository in bounded, evidence-producing waves. Deduplicate live work, respect active ownership, create durable findings for proven gaps, remediate unowned repository-local gaps, validate exact heads, preserve branch protection and maintain a truthful resume point.

## Completed waves

### Wave 001 — governance and durable-state consistency

- Issue `#1250` records stale Portal remediation state.
- PR `#1253` passed exact-head CI and merged as `37e12c1e7b118196543f23c5626959d870012748`.

### Wave 002 — PR terminality and operational blockers

- PRs `#1217` and `#1215` were ordered and updated without force-push.
- Issue `#1254` recorded an unavailable `freqtrade-staging` runner.
- PR `#1256` passed exact-head CI and merged as `8093f546eddf567b4d775a1cfa664fd8384d67f3`.

### Wave 003 — required CI bounds and terminal delivery

- PR `#1217` passed exact-head CI and merged as `5dadfe32c7cc2ba7af95652b06c4e0624d2f11b4`.
- Issue `#1257` and PR `#1258` add evidence-based 30-minute job and 300-second per-test bounds to the online compatibility lane, with a fail-closed regression contract.
- Checkpoint PR `#1259` passed exact-head CI and merged as `74d1ba5ca603d7b116a36f966592fac7f49cee08`.
- The trusted health runner later recovered. Issue `#1254` was closed after a fresh heartbeat, connected sources and acceptable disk capacity were reported.

## Wave 004 — focused-core CI dependency contract

### Proven failure

PR `#1215` exact head `d4cd9e0a512c12abee9ef5c2482c570aba50e8fc` passed compile, Ruff and mypy, then failed before test collection in run `31019942269`, job `92354598878`:

```text
ModuleNotFoundError: No module named 'xdist'
```

The required `core-light` job invoked `pytest -n auto`, and `tests/conftest.py` imported `xdist`, while the bounded dependency installation omitted `pytest-xdist`. The failure is independent of the Issue Form changes in PR `#1215`.

### Finding and repair ownership

- Issue `#1265` is the canonical P1/high-risk finding.
- Issues `#1266`, `#1267` and `#1268` were accidental duplicates and were immediately closed with reason `duplicate`; no separate work is authorized.
- PR `#1271` is the deduplicated repair owned by an already-active parallel worker on branch `fix/ci-core-light-xdist-1265`.
- The continuous-assurance coordinator detected that live ownership and did not overwrite the branch.
- Independent diff inspection of PR `#1271` found exactly two intended paths:
  - `.github/workflows/ci.yml` adds pinned `pytest-xdist==3.8.0` to `core-light`;
  - `tests/ci/test_core_light_dependency_contract.py` couples the pinned install to the `pytest -n auto` command.
- PR `#1271` exact head is `3ff2b1ded28617175ab29dfa1f4b9977f6fa5fdd`, based on `develop@108eff8149f3c5dba77bfcdeaea0c63c8a22b551`.
- Exact-head Freqtrade, risk-aware and security validation is active. No material audit finding is open against the diff.

### Related delivery

- PR `#1258` exact head `4351c01fa5ae1d04773062f95ee5909c892a7b4b` has successful Freqtrade, risk-aware and security workflows. Auto-merge was re-enabled after independent diff review; current-base/branch-protection completion remains pending.
- PR `#1215` must not be rerun unchanged. After PR `#1271` merges, update it to the repaired `develop` baseline without force-push and run fresh exact-head CI.

## Safety and scope

This wave changes only CI dependency and regression-contract surfaces. Runtime E2E is `NOT_APPLICABLE` because the deliverable is an internal CI harness contract; the exact-head required workflow is the real system boundary and must execute the repaired focused-core job. No credentials, exchange state, strategy, model, order authority, deployment, withdrawal or live-capital setting is changed.

## Context checkpoint

```yaml
checkpoint_version: 7
updated_at: 2026-08-05T16:05:00Z
status: waiting
head: 108eff8149f3c5dba77bfcdeaea0c63c8a22b551
branch: audit/platform-continuous-assurance-wave-004-20260805
wave: wave-004-focused-core-ci-contract-repair
proven:
  - PR 1259 merged as 74d1ba5ca603d7b116a36f966592fac7f49cee08
  - Issue 1254 recovered and closed after structured healthy monitor evidence
  - PR 1215 fails on the missing xdist dependency rather than its Issue Form changes
  - Issue 1265 is the canonical finding; 1266-1268 are terminal duplicates
  - PR 1271 implements the minimal two-path repair at exact head 3ff2b1ded28617175ab29dfa1f4b9977f6fa5fdd
  - parallel ownership of PR 1271 was detected and respected
  - PR 1258 exact-head workflows are green and auto-merge is enabled
unknown:
  - terminal exact-head result and merge commit for PR 1271
  - terminal current-base result and merge commit for PR 1258
  - terminal repaired-baseline result for PR 1215
blockers: []
next_action: Aggregate the required-check result for PR 1271 exact head 3ff2b1ded28617175ab29dfa1f4b9977f6fa5fdd; if every required gate passes, enable protected auto-merge, then update PR 1215 to the resulting develop head and rerun exact-head CI.
```

## Recovery checkpoint

```yaml
recovery:
  policy_version: 1
  generation: 1
  session_id: assurance-20260805T155000Z
  session_started_at: 2026-08-05T15:50:00Z
  checkpointed_at: 2026-08-05T16:05:00Z
  last_progress_at: 2026-08-05T16:05:00Z
  phase: exact_head_ci_and_delivery_reconciliation
  exact_head: 3ff2b1ded28617175ab29dfa1f4b9977f6fa5fdd
  pull_request: 1271
  active_operation: required exact-head CI
  external_run_ids: [31023291525, 31023296388, 31023294147]
  operation_started_at: 2026-08-05T16:01:50Z
  wait_deadline_at: 2026-08-05T16:46:50Z
  check_generation: pr-1271-head-3ff2b1d
  checks_used: 1
  status: waiting
  safe_to_resume: true
  resume_condition: required workflows for PR 1271 become terminal
  next_action: Inspect one aggregate required-check snapshot for PR 1271; merge only through branch protection after all exact-head gates pass.
```
