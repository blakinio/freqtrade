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

Record the owner's acceptance of Issue #1358 Option C as the binding dry-run runtime-control architecture, reconcile the known stale registry state without claiming the separate #1356 lifecycle-validator repair complete, and leave product/runtime behavior unchanged.

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
- [x] `ARCHITECTURE_REGISTRY.yaml` removes closed #1251/#1252 from open findings and marks their completed architecture review truthfully.
- [x] Historical #1251 review SHA/report provenance remains unchanged; the new ADR-020 decision records its own verified base SHA separately.
- [x] Registry indexes ADR-020 plus still-open runtime architecture findings #1353/#1354/#1355/#1357.
- [x] Registry keeps #1356 open because its preventive lifecycle validator is a separate implementation task not required to record the owner's ADR-020 decision.
- [x] Registry preserves accepted-decision precedence over older target-state text.
- [x] No product code, deployment, credentials, trading configuration or runtime behavior changes.
- [x] Fresh architecture-document audit found no remaining material contradiction after remediation.
- [ ] Documentation/governance exact-head CI passes for the final documentation-only head.
- [ ] PR #1367 is terminal and Issue #1358 is closed by the merged decision change.

## Fresh architecture-document audit

Audit input was reconstructed from the exact PR diff, the owner-accepted #1358 proposal, live Issues #1251/#1252/#1353/#1354/#1355/#1356/#1357/#1358 and the current accepted decision hierarchy rather than from the implementation summary.

Material findings found and remediated:

1. **Historical review provenance was initially overwritten by current synchronization metadata.** The FTAI-ARCH-001 `audited_base_sha`/`synchronized_base_sha` and review date now remain bound to the original #1251/#1255 review evidence; ADR-020 has a separate `latest_architecture_change.base_sha`.
2. **The task initially expanded into the preventive #1356 CI guard.** That introduced a `tests/ci/**` path, which intentionally routes full Freqtrade CI. The full run exposed three unrelated WickHunter failures already present in code outside this task's owned paths. The test addition was removed, #1356 remains open, and the architecture-acceptance PR is again documentation-only rather than taking over the active WickHunter lane.

Unrelated full-CI evidence from the superseded head `fad6bf25382feaaf9a5bcb40fa68e3d07e9e2e94`:

- Freqtrade CI run `31246886198` failed only in `Online / live compatibility tests` after 6707 passes and 128 skips;
- failures were entirely under `tests/ai_platform_integration/test_wickhunter_*` and concern `ShadowRuntimeTick`, the WickHunter PAPER supervisor entrypoint and parity-service dataclass replay;
- the lightweight required PR gate, pre-commit, documentation build, CodeQL, zizmor and the complete risk-aware component CI all passed;
- no changed path in PR #1367 touches WickHunter runtime or its tests.

No remaining critical/high/material-medium finding was identified in the narrowed architecture-documentation diff. Open #1353/#1354/#1355/#1357 remain implementation findings and are not misrepresented as implemented merely because their architectural direction is accepted by ADR-020. Issue #1356 remains an explicit medium governance finding.

## Context checkpoint

```yaml
checkpoint_version: 5
updated_at: 2026-08-08T10:05:00+02:00
status: validating
phase: terminal_documentation_ci
base_head: 62dc76164bd771e47365d7076af10cbd878061dd
branch: docs/portal-runtime-architecture-1358-20260808
pull_request: 1367
proven:
  - owner explicitly accepted Option C from Issue 1358
  - Issues 1251 and 1252 are closed/completed
  - Issues 1353, 1354, 1355, 1356 and 1357 remain open findings
  - no competing open PR was found for Issue 1358 or architecture registry work
  - ADR-020 and the registry reconciliation are committed on the task branch
  - the branch is based on current develop 62dc76164bd771e47365d7076af10cbd878061dd
  - fresh documentation audit found and repaired the historical-provenance defect
  - the attempted #1356 guard was removed after full CI exposed unrelated WickHunter failures outside task ownership
  - PR 1367 is narrowed back to documentation/governance only
unknown:
  - exact-head documentation/governance CI result for the narrowed final head
blockers: []
next_action: Validate the narrowed documentation-only PR head; if its routed required gates pass and current-base/review state remains clean, merge PR #1367 without bypass.
```

## Recovery checkpoint

```yaml
recovery:
  policy_version: 1
  generation: 4
  session_id: portal-runtime-architecture-20260808T0915+0200
  session_started_at: 2026-08-08T09:15:00+02:00
  checkpointed_at: 2026-08-08T10:05:00+02:00
  last_progress_at: 2026-08-08T10:05:00+02:00
  phase: terminal_documentation_ci
  pull_request: 1367
  active_operation: narrowed exact-head documentation/governance CI
  external_run_ids: []
  check_generation: architecture-acceptance-1367-docs-only
  checks_used: 0
  status: active
  safe_to_resume: true
  resume_condition: PR 1367 exact-head CI/review state changes or current develop advances materially on owned architecture paths
  next_action: Aggregate routed required CI for the narrowed PR #1367 head and merge only after every applicable gate passes.
```
