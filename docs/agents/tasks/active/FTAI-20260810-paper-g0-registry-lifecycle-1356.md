# FTAI-20260810 — PAPER G0 Architecture Registry Lifecycle Guard

```yaml
task_id: FTAI-20260810-paper-g0-registry-lifecycle-1356
programme_id: FTAI-PAPER-PLATFORM
repository: blakinio/freqtrade
project_lane: freqtrade-portal
task_kind: ci_governance
phase: validation
status: blocked
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
repair_budget_exhausted: true
successor_task: FTAI-20260810-paper-g0-registry-terminal-inventory-isolation-1356
ownership_transferred_to_successor: true
```

## Objective

Close PAPER implementation gate G0 finding #1356 by delivering a bounded automated architecture-registry lifecycle guard together with the registry reconciliation. This task reached the anti-stall repair-cycle limit before terminal validation; its remaining narrow defect was transferred to the fresh isolation successor named above. PR #1447 remains the authoritative delivery vehicle and must not be duplicated.

## Acceptance inventory

- `A1`: resolved findings cannot remain in `open_architecture_findings`, even if an Issue or finding ID is accidentally remapped.
- `A2`: every architecture finding identity uses a positive exact integer Issue number, a non-empty unique finding ID and valid lifecycle status; YAML booleans are rejected as Issue identifiers.
- `A3`: domain-local open-finding indexes cannot retain an entry that is absent from the canonical top-level open set.
- `A4`: the registry's latest accepted ADR exists as `accepted` in the binding decision log.
- `A5`: historical review provenance (`audited_base_sha` and `synchronized_base_sha`) remains distinct from the latest architecture-change base.
- `A6`: #1356 is moved from registry open sets into `review.resolved_findings` together with the preventive guard.
- `A7`: exact-head routed CI, CodeQL/zizmor as applicable, independent Codex review and PR hygiene are green before merge.
- `A8`: runtime/browser E2E is `NOT_APPLICABLE`; this task changes only CI/governance evidence and grants no runtime, deployment, credentials, order or LIVE authority.

## Owned paths released to successor

```yaml
released_paths:
  - ARCHITECTURE_REGISTRY.yaml
  - tests/ci/test_architecture_registry.py
  - docs/agents/tasks/active/FTAI-20260810-paper-g0-registry-lifecycle-1356.md
successor_may_add:
  - docs/agents/tasks/active/FTAI-20260810-paper-g0-registry-terminal-inventory-isolation-1356.md
```

## Review and repair history

```yaml
repair_cycles_for_gate: 3
ci_format_repair:
  run: 31421127334
  repair_commit: 1e6be5adadd6ae5f26355b1aaa3bd58a19a09dce
independent_review_findings:
  - reviewed_head: 48c177b299c848da18d031ca41aa03ff5db689b5
    severity: P2
    thread: PRRT_kwDOTdDTU86X_6vx
    disposition: remediated
  - reviewed_head: 4d4a2f8961af81b75b3ffaf3cb0bfd2aff6bc282
    severity: P2
    thread: PRRT_kwDOTdDTU86YABz6
    disposition: remediated
  - reviewed_head: 5d2e65944c0a2a2d07f88ab403e9bd75b2b14e3f
    severity: P2
    thread: PRRT_kwDOTdDTU86YAPja
    disposition: transferred_to_fresh_isolation_task
```

## Proven state

- #1356 remains the only Issue being repaired by PR #1447; do not create a duplicate delivery PR.
- The guard enforces unique exact integer Issue IDs, unique finding IDs, resolved/open separation, domain index consistency, latest accepted ADR binding and historical review provenance separation.
- The successor isolation task owns the independent pinned terminal identity inventory and final parser-valid recovery repair.
- Runtime/browser/deployment/trading E2E is `NOT_APPLICABLE` for this CI/governance package.
- PAPER remains the only authorized operational mode; LIVE remains unreachable/fail-closed.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-10T19:54:00Z
head: 08b16c822e61e78671c1725c710a9a21e13dda4c
branch: fix/architecture-registry-lifecycle-1356
pr: 1447
status: blocked
context_routes:
  - PAPER G0 architecture registry lifecycle
  - repair isolation handoff
owned_paths: []
proven:
  - Parent task exhausted its three repair cycles and transferred ownership to FTAI-20260810-paper-g0-registry-terminal-inventory-isolation-1356.
  - PR 1447 is the authoritative delivery vehicle for Issue 1356.
  - The parent task must not resume implementation or create a replacement PR.
derived:
  - Final validation and closeout belong to the successor isolation task.
unknown:
  - Terminal result of PR 1447 after successor repairs and final exact-head validation.
conflicts:
  - none
first_failure:
  marker: parent repair budget exhausted
  evidence: three bounded repair cycles recorded above
rejected_hypotheses:
  - Continue repairing under the exhausted parent task; rejected by anti-stall max_repair_cycles_per_gate.
changed_paths:
  - ARCHITECTURE_REGISTRY.yaml
  - tests/ci/test_architecture_registry.py
  - docs/agents/tasks/active/FTAI-20260810-paper-g0-registry-lifecycle-1356.md
validation:
  - command: runtime/browser E2E
    result: NOT_APPLICABLE
    evidence: CI/governance-only lifecycle guard
blockers:
  - Parent repair budget exhausted; successor task owns remaining validation and closeout.
next_action: Resume only through FTAI-20260810-paper-g0-registry-terminal-inventory-isolation-1356 on PR 1447; do not mutate from this parent task.
```
