# FTAI-20260808 Portal Runtime Architecture 1358

```yaml
task_id: FTAI-20260808-portal-runtime-architecture-1358
programme_id: FTAI-PROGRAM-AI-TRADING-PORTAL
repository: blakinio/freqtrade
project_lane: freqtrade-portal
task_kind: documentation
phase: closeout
status: completed
priority: critical
prompting_standard_version: 2.1
execution_policy_version: 2
execution_mode: github_only
run_scope: single_task
continuation_policy: stop_at_task_boundary
base_branch: develop
initial_base_head: 62dc76164bd771e47365d7076af10cbd878061dd
delivery_branch: docs/portal-runtime-architecture-1358-20260808
delivery_pr: 1367
delivery_head: 87ccde32b770877411a48d3a1c336c585103ff22
delivery_merge_commit: 4f1005566d7c58be2748417ba9e1e4e9f2a74456
issue: 1358
related_open_issue: 1356
live_capital_authorized: false
protected_production_deployment_authorized: false
```

## Terminal result

The owner explicitly accepted Issue #1358 Option C, and PR #1367 recorded it as binding `ADR-020` plus the corresponding canonical architecture-registry update.

Accepted execution-plane architecture:

- immutable `RuntimeGeneration` execution identity;
- separate authored/draft, desired and observed active runtime revision/generation;
- narrow Runtime Supervisor as the only Portal component with container-engine authority;
- per-runtime Gateway as the only Portal-to-Freqtrade application boundary;
- same-host Gateway transport by generation-bound Unix domain socket + OS ACLs, with authenticated TLS/mTLS reserved for future multi-host transport;
- generation-local Freqtrade API credentials rather than Portal-worker credentials;
- credential-free `PUBLIC_DATA` connectivity for current dry-run runtimes;
- separated control-owned immutable evidence, immutable runtime mounts, durable generation-local writable state and bounded ephemeral state;
- mandatory runtime isolation profile;
- PostgreSQL/reconciliation as correctness authority, events only as latency optimization;
- monotonic `ExecutionSafetyEpoch` fencing for exposure-increasing commands;
- deployable roles split by privilege without prematurely splitting business domains into microservices.

No runtime implementation, deployment, exchange credential activation, trading configuration, withdrawal capability, model promotion or live-capital authority was introduced.

## Registry reconciliation

`ARCHITECTURE_REGISTRY.yaml` now:

- preserves the historical #1251/#1255 review provenance;
- records #1251/#1252 as resolved rather than open;
- records ADR-020 as the latest accepted architecture change on verified base `62dc76164bd771e47365d7076af10cbd878061dd`;
- preserves #1353/#1354/#1355/#1357 as open implementation findings;
- preserves #1356 as a separate open medium governance finding for the preventive lifecycle validator;
- states that conflicting older target-state wording is interpreted through ADR-020.

## Validation

Final delivery head `87ccde32b770877411a48d3a1c336c585103ff22`:

- Freqtrade CI run `31247683668`: PASS;
- Risk-aware component CI run `31247683772`: PASS;
- GitHub Actions Security Analysis with zizmor run `31247683662`: PASS;
- CodeQL Security Analysis run `31247683660`: PASS;
- Pre-commit Types update run `31247683650`: correctly SKIPPED;
- no unresolved PR review threads;
- PR #1367 mergeable and merged by squash without force/bypass;
- merge commit `4f1005566d7c58be2748417ba9e1e4e9f2a74456` became `develop` head;
- Issue #1358 closed as completed by the merge;
- Issue #1356 remained open intentionally.

A superseded over-scoped head temporarily added a `tests/ci/**` validator for #1356, which correctly triggered full CI and exposed unrelated existing WickHunter integration failures. That validator was removed from this task; the final delivery diff remained limited to architecture documentation/governance and passed its routed exact-head gates.

## Fresh audit

A fresh architecture-document audit challenged the accepted-decision recording against the exact diff, live Issue state and authority hierarchy.

Material findings found and repaired before final delivery:

1. historical FTAI-ARCH-001 review SHA provenance had initially been overwritten by current synchronization metadata;
2. the task had temporarily expanded into the separate #1356 preventive-validator lane.

After correction, no critical/high/material-medium finding remained in the delivered architecture-decision diff. Open implementation findings are explicitly not represented as implemented.

## E2E

`NOT_APPLICABLE`: this task changes architecture authority/documentation only and deliberately changes no runtime behavior or user-facing product path.

## PR hygiene

- delivery PR #1367: merged;
- no duplicate architecture-decision PR found;
- no unresolved review threads;
- lifecycle archive is delivered through the follow-up closeout PR for this same task.

## Final checkpoint

```yaml
checkpoint_version: 6
status: completed
phase: archived
completed_at: 2026-08-08T10:10:00+02:00
delivery_pr: 1367
delivery_merge_commit: 4f1005566d7c58be2748417ba9e1e4e9f2a74456
owner_decision_recorded: true
adr: ADR-020
open_related_findings:
  - 1353
  - 1354
  - 1355
  - 1356
  - 1357
blockers: []
next_action: none
```
