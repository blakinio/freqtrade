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
implementation_authorized: documentation_only
live_capital_authorized: false
protected_production_deployment_authorized: false
owned_paths:
  - ARCHITECTURE_REGISTRY.yaml
  - docs/ai_platform/portal/ARCHITECTURE_DECISIONS.md
  - docs/agents/tasks/active/FTAI-20260808-portal-runtime-architecture-1358.md
  - docs/agents/tasks/archive/FTAI-20260808-portal-runtime-architecture-1358.md
```

## Objective

Record the owner's acceptance of Issue #1358 Option C as the binding dry-run runtime-control architecture, reconcile the canonical architecture registry, and leave implementation/runtime behavior unchanged.

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
- [x] `ARCHITECTURE_REGISTRY.yaml` removes closed #1251/#1252 from open findings, marks the completed architecture review truthfully, and indexes ADR-020 plus still-open runtime architecture findings.
- [x] Registry preserves accepted-decision precedence over older target-state text.
- [x] No product code, deployment, credentials, trading configuration or runtime behavior changes.
- [ ] Documentation/governance validation passes on the exact final head.
- [ ] Fresh documentation audit finds no material contradiction.
- [ ] Related PRs are terminal and Issues #1356/#1358 are reconciled only after merge.

## Context checkpoint

```yaml
checkpoint_version: 2
updated_at: 2026-08-08T09:24:08+02:00
status: validating
phase: exact_head_documentation_validation
base_head: 62dc76164bd771e47365d7076af10cbd878061dd
branch: docs/portal-runtime-architecture-1358-20260808
pull_request: 1367
proven:
  - owner explicitly accepted Option C from Issue 1358
  - Issues 1251 and 1252 are closed/completed
  - no competing open PR was found for Issue 1358 or architecture registry work
  - ADR-020 and the registry reconciliation are committed on the task branch
  - the branch was merge-forwarded without force to current develop 62dc76164bd771e47365d7076af10cbd878061dd
  - the develop delta since task start is WickHunter-only and does not overlap owned paths
  - PR 1367 is the sole delivery PR for this architecture acceptance change
unknown:
  - exact-head CI result for the final validation head
  - fresh documentation audit result
blockers: []
next_action: Run fresh documentation consistency audit and exact-head required CI for PR #1367, then terminalize the PR if all gates pass.
```

## Recovery checkpoint

```yaml
recovery:
  policy_version: 1
  generation: 1
  session_id: portal-runtime-architecture-20260808T0915+0200
  session_started_at: 2026-08-08T09:15:00+02:00
  checkpointed_at: 2026-08-08T09:24:08+02:00
  last_progress_at: 2026-08-08T09:24:08+02:00
  phase: exact_head_documentation_validation
  exact_head: 35069acfbc310c166ed86433bb215089d8db5fc4
  pull_request: 1367
  active_operation: exact-head CI and fresh documentation audit
  external_run_ids: []
  operation_started_at: 2026-08-08T09:24:08+02:00
  wait_deadline_at: 2026-08-08T10:09:08+02:00
  check_generation: architecture-acceptance-1367
  checks_used: 0
  status: active
  safe_to_resume: true
  resume_condition: PR 1367 exact-head CI/review state changes or current develop advances materially on owned architecture paths
  next_action: Inspect the fresh exact diff for semantic contradictions, then observe aggregate required CI for the final head.
```
