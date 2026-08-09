---
task_id: FTAI-20260809-runtime-generation-plan-binding-1413
project_lane: freqtrade-portal
programme: AI Trading Portal
issue: 1413
pull_request: 1416
status: completed
phase: archived_repository_delivery
effective_on_merge: true
implementation_head: a78a014df90c4f45700c2984a27b4896a7ee4b7b
branch: feat/runtime-generation-isolation-plan-binding-1413
base_branch: develop
related_adr: ADR-020
related_issues:
  - 1353
  - 1354
  - 1355
  - 1357
related_prs:
  - 1388
  - 1395
feature_scope:
  type: infrastructure
  user_facing: false
  backend_required: true
  frontend_required: false
  integration_required: true
  e2e_required: false
  completion_claim: internal_only
implementation_authorized: true
live_capital_authorized: false
production_deployment_authorized: false
ownership_released_on_merge: true
---

# RuntimeGeneration isolation-plan binding — Issue #1413

## Repository result

Executable `RuntimeGeneration` now requires and durably persists the exact resolved runtime-isolation and TCB identities required by the accepted ADR-020 refinement:

- `isolation_plan_digest`;
- `gateway_artifact_digest`;
- `gateway_contract_digest`;
- `market_data_egress_policy_version`;
- `market_data_egress_policy_digest`.

The same identities are mandatory in trusted `RuntimeGenerationMaterial`, are included in `generation_spec_digest`, round-trip through the authoritative schema/repository, and cannot be supplied as activation authority by browser/API payloads.

Schema revision `20260809_04_runtime_isolation_binding` upgrades an exact empty revision-3 runtime-generation schema and fails closed instead of fabricating isolation/TCB identity when historical executable generation rows already exist.

## Validation

Implementation head before lifecycle archival:

```text
a78a014df90c4f45700c2984a27b4896a7ee4b7b
```

Verified before archival:

- prior full exact-head Freqtrade CI, CodeQL, zizmor, Portal API Mode Browser and Portal Exact-Image Supply Chain passed after the schema-order repair;
- Risk-aware component CI passed AI Platform tests/lint, SQLite schema authority, deterministic schema inventory, PostgreSQL migration/concurrency/backup-restore, exact-image integration and Portal browser/web gates on the repaired implementation;
- the specific revision-3-to-4 SQLite readiness regression was reproduced, causally isolated to physical column ordering, repaired without weakening schema fingerprint/readiness checks, and then passed the exact failing schema gate;
- post-audit negative tests now cover both missing and malformed isolation/Gateway/egress trusted material;
- existing idempotent activation/replay, SHADOW/PAPER and runtime-truth suites remain part of the required AI Platform regression set.

The delivery PR must still pass all repository-required checks on its exact final archive head before merge. This archived record becomes authoritative only when that exact PR is merged to `develop`.

## Independent audit

Fresh validator review read Issue #1413 acceptance directly, inspected the complete PR diff and primary CI evidence, and attempted to falsify required-field enforcement, server-only authority, persistence, migration safety, digest sensitivity and scope boundaries.

Finding `FTAI-1413-AUD-001`:

- severity: medium;
- evidence: missing-field tests existed, but no direct malformed-value test covered the five new trusted isolation/TCB bindings;
- impact: literal acceptance required missing **and malformed** trusted-material coverage;
- disposition: remediated on `a78a014df90c4f45700c2984a27b4896a7ee4b7b` with invalid SHA-256 and empty-policy-version cases.

Post-remediation audit result:

```text
PASS_ZERO_MATERIAL_FINDINGS
```

No container-engine authority, deployment authority, private exchange credential authority, order-submission authority or live-capital authority was introduced.

## E2E disposition

```yaml
result: NOT_APPLICABLE
reason: >-
  Issue #1413 is an internal immutable contract/persistence prerequisite. It does not deliver
  the physical Runtime Supervisor, Freqtrade mount/storage/network enforcement or a new
  user-facing capability. Real physical runtime isolation E2E remains acceptance work for
  #1353/#1354/#1355. Integration/API-mode/exact-image validation remains required here.
```

## PR hygiene

- authoritative delivery PR: #1416;
- duplicate implementation PR search: none found;
- unresolved review threads at audit: 0;
- #1388 and #1395 are historical merged prerequisites, not competing delivery PRs;
- #1353/#1354/#1355 remain intentionally open follow-up implementation work.

## Terminal merge condition

```yaml
closeout:
  implementation_complete: true
  audit:
    result: PASS_ZERO_MATERIAL_FINDINGS
    material_findings_open: 0
  e2e:
    result: NOT_APPLICABLE
    reason: internal contract/persistence prerequisite; physical runtime isolation belongs to follow-up issues
  final_ci:
    requirement: PASS on exact final PR #1416 head before merge
    evidence_source: GitHub required checks for PR #1416
  pull_requests:
    authoritative: 1416
    duplicate_open_prs: 0
    unresolved_review_threads: 0
  task_status: completed
  task_archived: true
  ownership_release: effective when PR #1416 merges
```

## Recovery checkpoint

```yaml
recovery:
  policy_version: 1
  generation: 1
  session_id: 20260809-runtime-generation-isolation-binding-closeout
  session_started_at: 2026-08-09T16:05:00Z
  checkpointed_at: 2026-08-09T16:14:38Z
  last_progress_at: 2026-08-09T16:14:38Z
  phase: terminal_exact_head_ci_and_merge
  exact_head: verify_live_pr_head_after_archive_move
  pull_request: 1416
  active_operation: final required GitHub Actions validation
  external_run_ids: []
  operation_started_at: null
  wait_deadline_at: null
  check_generation: final_archive_head
  checks_used: 0
  status: ready
  safe_to_resume: true
  resume_condition: PR #1416 final archive head exists and required checks are discoverable
  next_action: Verify exact final PR #1416 head, run/observe required final checks, then merge only if every merge gate passes.
```
