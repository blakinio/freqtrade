# FTAI-20260808 Portal Runtime Architecture 1358

```yaml
task_id: FTAI-20260808-portal-runtime-architecture-1358
programme_id: FTAI-PROGRAM-AI-TRADING-PORTAL
repository: blakinio/freqtrade
project_lane: freqtrade-portal
task_kind: documentation
phase: validate
status: validating
priority: critical
prompting_standard_version: 2.1
execution_policy_version: 2
execution_mode: github_only
run_scope: single_task
continuation_policy: stop_at_task_boundary
task_completion_policy: finalize_archive_and_continue
user_communication: terminal_only
base_branch: develop
base_head: 62dc76164bd771e47365d7076af10cbd878061dd
branch: docs/portal-runtime-architecture-1358-20260808
pull_request: 1367
issue: 1358
related_issue: 1356
implementation_authorized: documentation_and_governance_test
live_capital_authorized: false
protected_production_deployment_authorized: false
owned_paths:
  - ARCHITECTURE_REGISTRY.yaml
  - docs/ai_platform/portal/ARCHITECTURE_DECISIONS.md
  - tests/ci/test_architecture_registry.py
  - docs/agents/tasks/active/FTAI-20260808-portal-runtime-architecture-1358.md
  - docs/agents/tasks/archive/FTAI-20260808-portal-runtime-architecture-1358.md
```

## Objective

Record the owner's acceptance of Issue #1358 Option C as the binding dry-run runtime-control architecture, reconcile the canonical architecture registry, add the bounded registry lifecycle guard required by #1356, and leave product/runtime behavior unchanged.

## Accepted architecture scope

- `RuntimeGeneration` is the immutable execution identity.
- Bot config authoring, desired revision and observed active runtime revision/generation are distinct.
- A narrow Runtime Supervisor is the only Portal boundary with container-engine authority.
- A per-runtime Gateway is the only Portal-to-Freqtrade application boundary.
- Same-host Portal-to-Gateway transport defaults to Unix domain sockets with OS ACLs; future multi-host transport uses authenticated TLS/mTLS; plain routable HTTP is not an accepted boundary.
- Freqtrade API credentials are generation-local between Gateway and Freqtrade, not Portal-worker credentials.
- Dry-run uses public-data exchange connectivity without requiring private trading credentials.
- Runtime control evidence, immutable mounts, durable writable runtime state and ephemeral state are separate trust/storage classes.
- Runtime isolation is mandatory and generation-bound.
- Reconciliation remains authoritative; events reduce latency but are not system-of-record authority.
- Kill-switch enforcement uses a monotonic execution safety epoch/fence.
- Deployable process roles are split by privilege while preserving modular-monolith domain ownership.

## Acceptance inventory

- [x] `ARCHITECTURE_DECISIONS.md` contains accepted ADR-020 with migration/consequence boundaries and no live-capital authority.
- [x] `ARCHITECTURE_REGISTRY.yaml` removes closed #1251/#1252 from open findings and marks the completed architecture review truthfully.
- [x] Historical #1251 review SHA/report provenance remains unchanged; the new ADR-020 decision records its own verified base SHA separately.
- [x] Registry indexes ADR-020 plus still-open runtime architecture findings #1353/#1354/#1355/#1357.
- [x] Registry preserves accepted-decision precedence over older target-state text.
- [x] `tests/ci/test_architecture_registry.py` prevents resolved findings from also remaining in the open-finding set and verifies the latest accepted ADR exists in the binding decision log.
- [x] The provenance guard permits a future bounded architecture review to replace the historical #1251 review identity without hard-coding the repository permanently to that review.
- [x] No product code, deployment, credentials, trading configuration or runtime behavior changes.
- [x] Fresh architecture-document audit found no remaining material contradiction after remediation.
- [ ] Focused registry guard and required exact-head CI pass.
- [ ] PR #1367 is terminal; Issues #1356/#1358 are closed by the merged decision/governance change.

## Fresh architecture-document audit

Audit input was reconstructed from the exact PR diff, the owner-accepted #1358 proposal, live Issues #1251/#1252/#1353/#1354/#1355/#1356/#1357/#1358 and the current accepted decision hierarchy rather than from the implementation summary.

Material findings found and remediated before final CI:

1. **Historical review provenance was initially overwritten by current synchronization metadata.** The FTAI-ARCH-001 `audited_base_sha`/`synchronized_base_sha` and review date now remain bound to the original #1251/#1255 review evidence; ADR-020 has a separate `latest_architecture_change.base_sha`.
2. **The initial PR incorrectly proposed closing #1356 without its preventive lifecycle guard.** A focused CI regression test now enforces resolved/open finding disjointness and accepted-ADR linkage, so #1356 can close with the merged change.

Validation hardening performed after the material findings were fixed:

- the provenance regression test was generalized so a future bounded architecture review can replace the review identity/provenance together instead of requiring an unrelated test rewrite; the known #1251 audited SHA remains protected only while #1251 is still the declared registry review.

No remaining critical/high/material-medium documentation finding was identified. Open #1353/#1354/#1355/#1357 remain implementation findings and are not misrepresented as implemented merely because their architectural direction is accepted by ADR-020.

## Context checkpoint

```yaml
checkpoint_version: 4
updated_at: 2026-08-08T09:32:49+02:00
status: validating
phase: terminal_exact_head_validation
base_head: 62dc76164bd771e47365d7076af10cbd878061dd
branch: docs/portal-runtime-architecture-1358-20260808
pull_request: 1367
validation_input_head: 5f4063a07fc11e4a8f9cabb52679df91c0eac3e6
proven:
  - owner explicitly accepted Option C from Issue 1358
  - Issues 1251 and 1252 are closed/completed
  - Issues 1353, 1354, 1355 and 1357 remain open implementation findings
  - Issue 1356 has its requested lifecycle guard in this PR and is intended to close only on merge
  - no competing open PR was found for Issue 1358 or architecture registry work
  - ADR-020 and the registry reconciliation are committed on the task branch
  - the branch was merge-forwarded without force to develop 62dc76164bd771e47365d7076af10cbd878061dd
  - the develop delta since task start is WickHunter-only and does not overlap owned paths
  - fresh documentation audit found and repaired two material governance-documentation defects
  - the focused lifecycle/provenance guard is reviewable and does not freeze future legitimate architecture reviews
  - PR 1367 is the sole delivery PR for this architecture acceptance change and is ready for review
unknown:
  - exact-head focused/required CI result after this final checkpoint commit
blockers: []
next_action: Observe aggregate required CI for the final PR head; if green and current-base/review state remains clean, merge PR #1367 without bypass.
```

## Recovery checkpoint

```yaml
recovery:
  policy_version: 1
  generation: 3
  session_id: portal-runtime-architecture-20260808T0915+0200
  session_started_at: 2026-08-08T09:15:00+02:00
  checkpointed_at: 2026-08-08T09:32:49+02:00
  last_progress_at: 2026-08-08T09:32:49+02:00
  phase: terminal_exact_head_validation
  exact_head: 5f4063a07fc11e4a8f9cabb52679df91c0eac3e6
  pull_request: 1367
  active_operation: exact-head focused and required CI
  external_run_ids: []
  operation_started_at: 2026-08-08T09:32:49+02:00
  wait_deadline_at: 2026-08-08T10:17:49+02:00
  check_generation: architecture-acceptance-1367-final
  checks_used: 0
  status: active
  safe_to_resume: true
  resume_condition: PR 1367 exact-head CI/review state changes or current develop advances materially on owned architecture paths
  next_action: Aggregate exact-head workflow state for PR 1367 and merge only after every required gate passes.
```
