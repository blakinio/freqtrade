# FTAI-20260810 — PAPER G0 Registry Terminal Finding Isolation

```yaml
task_id: FTAI-20260810-paper-g0-registry-terminal-inventory-isolation-1356
programme_id: FTAI-PAPER-PLATFORM
repository: blakinio/freqtrade
project_lane: freqtrade-portal
task_kind: repair_isolation
phase: validation
status: waiting
priority: high
execution_mode: github_only
run_scope: autonomous_program
continuation_policy: continue_until_real_stop
base_branch: develop
trusted_base_sha: 5a19ae32f1f71b112130ea66cb8d56d9a3e44049
delivery_branch: fix/architecture-registry-lifecycle-1356
delivery_pr: 1447
issue: 1356
parent_task: FTAI-20260810-paper-g0-registry-lifecycle-1356
isolation_reason: parent task exhausted max_repair_cycles_per_gate after Codex found a third P2
paper_gate: G0
live_capital_authorized: false
protected_production_deployment_authorized: false
```

## Objective

Reuse authoritative PR #1447 and close the single remaining lifecycle-guard defect without broadening scope: known terminal architecture findings must be represented by a pinned terminal identity inventory that is independent from the editable registry open/resolved sets. The validator must fail if one of those terminal identities is omitted from `review.resolved_findings`, remapped, or left in any open set.

## Acceptance inventory

- `I1`: preserve all already-proven #1356 guard invariants.
- `I2`: maintain a pinned set of known terminal `(issue, finding_id)` identities outside the registry payload.
- `I3`: require registry `review.resolved_findings` to match the pinned terminal identity inventory, forcing future terminal-set changes to update both sources intentionally.
- `I4`: require pinned terminal Issues and finding IDs to be disjoint from canonical top-level open findings.
- `I5`: the pinned inventory covers current terminal findings #1251, #1252, #1353, #1357 and candidate terminal #1356 with their exact stable finding IDs.
- `I6`: do not add network-dependent GitHub API calls to unit/CI tests; the pinned inventory is the bounded independent source accepted for this guard.
- `I7`: independent Codex review must verify the lifecycle guard and recovery records with no remaining material finding.
- `I8`: exact-head routed CI, CodeQL/zizmor as applicable and zero unresolved review threads are required before merge.
- `I9`: runtime/browser E2E remains `NOT_APPLICABLE` because the repair is CI/governance-only.
- `I10`: before final exact-head CI, archive both the exhausted parent task and this successor in the same PR according to `REPAIR_PR_ECONOMY.md`.
- `I11`: every active task record in this delivery remains consumable by `tools/agents/checkpoint.py --require-checkpoint` using the complete canonical v1 context-checkpoint schema.

## Owned paths

```yaml
owned_paths:
  - tests/ci/test_architecture_registry.py
  - docs/agents/tasks/active/FTAI-20260810-paper-g0-registry-lifecycle-1356.md
  - docs/agents/tasks/active/FTAI-20260810-paper-g0-registry-terminal-inventory-isolation-1356.md
shared_read_only:
  - ARCHITECTURE_REGISTRY.yaml
```

## Implementation and review evidence

```yaml
pinned_terminal_findings:
  - [1251, FTAI-ARCH-001]
  - [1252, FTAI-CI-001]
  - [1353, FTAI-ARCH-RUNTIME-TRUSTED-STATE]
  - [1356, FTAI-ARCH-REGISTRY-LIFECYCLE-GUARD]
  - [1357, FTAI-ARCH-BOT-REVISION-STATE]
validator_invariants:
  - registry resolved identity set equals the pinned terminal identity set
  - pinned terminal Issue IDs are disjoint from top-level open Issue IDs
  - pinned terminal finding IDs are disjoint from top-level open finding IDs
  - existing exact-integer identity, uniqueness, domain-index, ADR-binding and provenance guards remain intact
network_dependency_added: false
repair_cycles_for_current_isolation: 3
independent_review_history:
  - reviewed_head: 404de0a9ba89d6eb044e5aef2b560ff856d2d7f9
    severity: P1
    thread: PRRT_kwDOTdDTU86YAbOp
    finding: active task records used noncanonical checkpoint headings
    disposition: remediated
  - reviewed_head: 08b16c822e61e78671c1725c710a9a21e13dda4c
    severity: P1
    thread: PRRT_kwDOTdDTU86YAlUi
    finding: renamed checkpoint sections still lacked the complete parser-required v1 schema
    disposition: remediated_by_parser_valid_parent_and_successor_records
  - reviewed_head: 95ec792ecd6faae88f0a4ae81f012ef853e78dad
    severity: none_material
    finding: fresh Codex review produced no new material lifecycle finding; exact-head CI later exposed only a codespell wording failure in the parent task record
    disposition: mechanical_codespell_repair_a5061c11e463f9d806485341603dcbe43ccec10f
```

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-10T20:52:00Z
head: a5061c11e463f9d806485341603dcbe43ccec10f
branch: fix/architecture-registry-lifecycle-1356
pr: 1447
status: waiting
invocation_started_at: 2026-08-10T20:37:00Z
last_progress_at: 2026-08-10T20:52:00Z
ci_checks_for_current_head: 2
unchanged_state_checks: 0
review_checks_for_current_head: 1
identical_failure_retries: 0
repair_cycles_for_current_gate: 3
context_reconstruction_attempts: 0
stall_warnings: 0
context_routes:
  - PAPER G0 architecture registry lifecycle
  - terminal finding identity isolation
  - durable checkpoint parser validation
owned_paths:
  - tests/ci/test_architecture_registry.py
  - docs/agents/tasks/active/FTAI-20260810-paper-g0-registry-lifecycle-1356.md
  - docs/agents/tasks/active/FTAI-20260810-paper-g0-registry-terminal-inventory-isolation-1356.md
proven:
  - PR 1447 remains the sole delivery PR for Issue 1356.
  - The registry guard contains an independent pinned terminal identity inventory for Issues 1251, 1252, 1353, 1356 and 1357.
  - Resolved identities must equal the pinned terminal inventory and pinned Issue/finding IDs must be absent from open findings.
  - Exact integer, uniqueness, domain-index, accepted-ADR and historical provenance invariants remain present.
  - Parent task is parser-valid, blocked and ownership-transferred rather than silently resumed after repair-budget exhaustion.
  - The successor checkpoint uses the canonical v1 schema required by checkpoint.py.
  - Codespell-only failure on predecessor 95ec792ecd6faae88f0a4ae81f012ef853e78dad was repaired by a5061c11e463f9d806485341603dcbe43ccec10f without changing lifecycle logic.
  - On a5061c11e463f9d806485341603dcbe43ccec10f CodeQL run 31430105103 and zizmor run 31430105148 passed.
  - Runtime/browser/deployment/trading E2E is not applicable to this CI/governance-only package.
derived:
  - The second and final ordinary aggregate CI observation on a5061c11e463f9d806485341603dcbe43ccec10f still had Freqtrade run 31430106545 in progress and Risk-aware run 31430105875 queued; no third same-SHA poll is allowed.
  - Fresh Codex review was requested for a5061c11e463f9d806485341603dcbe43ccec10f after the mechanical codespell repair.
unknown:
  - Terminal result of Freqtrade 31430106545 and Risk-aware 31430105875.
  - Fresh Codex disposition on a5061c11e463f9d806485341603dcbe43ccec10f.
conflicts:
  - none
first_failure:
  marker: exact-head pre-commit codespell failure on predecessor 95ec792ecd6faae88f0a4ae81f012ef853e78dad
  evidence: Freqtrade run 31426411160 job 93579083570; only disjointness wording in parent task record
rejected_hypotheses:
  - Treat codespell wording as a new material lifecycle defect; rejected because lifecycle test logic and registry payload were unchanged.
  - Perform a third ordinary CI query on a5061c11e463f9d806485341603dcbe43ccec10f; rejected by anti-stall per-head cap.
  - Continue with a fourth material repair cycle in this isolation task; rejected by max_repair_cycles_per_gate.
changed_paths:
  - ARCHITECTURE_REGISTRY.yaml
  - tests/ci/test_architecture_registry.py
  - docs/agents/tasks/active/FTAI-20260810-paper-g0-registry-lifecycle-1356.md
  - docs/agents/tasks/active/FTAI-20260810-paper-g0-registry-terminal-inventory-isolation-1356.md
validation:
  - command: independent Codex review of 95ec792ecd6faae88f0a4ae81f012ef853e78dad
    result: PASS_NO_NEW_MATERIAL_FINDING
    evidence: review PRR_kwDOTdDTU88AAAABJBrROA
  - command: exact-head CI observation 2 on a5061c11e463f9d806485341603dcbe43ccec10f
    result: WAITING
    evidence: Freqtrade 31430106545 in_progress; Risk-aware 31430105875 queued; CodeQL 31430105103 PASS; zizmor 31430105148 PASS
  - command: runtime/browser E2E
    result: NOT_APPLICABLE
    evidence: CI/governance-only lifecycle guard; no runtime or user-facing behavior changes
blockers:
  - External exact-head CI and fresh independent review are pending; ordinary same-SHA observation budget is exhausted.
next_action: On a later live-state change, resolve PR 1447 head once. If the head remains the checkpoint successor and external gates are clear with no new material finding, archive both parent and successor task records in this PR, then perform final exact-head closeout validation before merge. If a new material finding appears, rotate to a fresh isolation task rather than a fourth repair here.
```
