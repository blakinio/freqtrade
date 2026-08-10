# FTAI-20260810 — PAPER G0 Architecture Registry Lifecycle Guard

```yaml
task_id: FTAI-20260810-paper-g0-registry-lifecycle-1356
programme_id: FTAI-PAPER-PLATFORM
repository: blakinio/freqtrade
project_lane: freqtrade-portal
task_kind: ci_governance
phase: validation
status: validating
priority: high
prompting_standard_version: 2.1
execution_policy_version: 2
execution_mode: github_only
run_scope: autonomous_program
continuation_policy: continue_until_real_stop
base_branch: develop
trusted_base_sha: 5a19ae32f1f71b112130ea66cb8d56d9a3e44049
delivery_branch: fix/architecture-registry-lifecycle-1356
delivery_pr: 1447
issue: 1356
paper_gate: G0
live_capital_authorized: false
protected_production_deployment_authorized: false
```

## Objective

Close PAPER implementation gate G0 finding #1356 by restoring a bounded automated architecture-registry lifecycle guard and reconciling the registry only after the guard is present and exact-head CI is green.

## Acceptance inventory

- `A1`: resolved findings cannot remain in `open_architecture_findings`.
- `A2`: every top-level open architecture finding has `status: open` and stable Issue/finding identity.
- `A3`: domain-local open-finding indexes cannot retain an entry that is absent from the canonical top-level open set.
- `A4`: the registry's latest accepted ADR exists as `accepted` in the binding decision log.
- `A5`: historical review provenance remains distinct from the latest architecture-change base.
- `A6`: #1356 is moved from the registry open sets into `review.resolved_findings` in PR #1447 together with the preventive guard.
- `A7`: exact-head routed CI, CodeQL/zizmor as applicable, and PR hygiene are green before merge.
- `A8`: runtime/browser E2E is `NOT_APPLICABLE`; this task changes only CI/governance evidence and grants no runtime, deployment, credentials, order or LIVE authority.

## Owned paths

```yaml
owned_paths:
  - ARCHITECTURE_REGISTRY.yaml
  - tests/ci/test_architecture_registry.py
  - docs/agents/tasks/active/FTAI-20260810-paper-g0-registry-lifecycle-1356.md
```

## Context checkpoint

```yaml
checkpoint_version: 2
updated_at: 2026-08-10T20:51:00+02:00
head: 0457b1da63dedd3bdd50db96d0247a899e61b3f0
branch: fix/architecture-registry-lifecycle-1356
pr: 1447
status: validating
proven:
  - develop exact base is 5a19ae32f1f71b112130ea66cb8d56d9a3e44049
  - Issue 1356 is open and dedicated to the preventive registry lifecycle validator
  - PR 1447 contains the restored bounded tests/ci architecture registry guard
  - the guard rejects resolved/open overlap duplicate identities non-open top-level findings stale domain-local open indexes and missing acceptance of the latest ADR
  - PR 1367 previously prepared then intentionally removed an earlier validator because that architecture task was over-scoped
  - current PAPER plan G0 explicitly requires resolving 1356 before later PAPER gates are claimed complete
  - runtime browser deployment and trading E2E are not applicable to this CI/governance-only package
unknown:
  - exact final-head CI run IDs until GitHub Actions completes
  - final independent audit result until the exact diff is rechecked after reconciliation
blockers: []
next_action: Commit the registry reconciliation on PR 1447, require exact-head CI, audit the exact diff and merge only if every applicable gate passes.
```
