# FTAI-20260810 — PAPER G0 Registry Terminal Finding Isolation

```yaml
task_id: FTAI-20260810-paper-g0-registry-terminal-inventory-isolation-1356
programme_id: FTAI-PAPER-PLATFORM
repository: blakinio/freqtrade
project_lane: freqtrade-portal
task_kind: repair_isolation
phase: validation
status: validating
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
- `I7`: independent Codex review must verify the third P2 is closed and introduce no new material finding.
- `I8`: exact-head routed CI, CodeQL/zizmor as applicable and zero unresolved review threads are required before merge.
- `I9`: runtime/browser E2E remains `NOT_APPLICABLE` because the repair is CI/governance-only.
- `I10`: before final exact-head CI, archive both the exhausted parent task and this successor in the same PR according to `REPAIR_PR_ECONOMY.md`.

## Owned paths

```yaml
owned_paths:
  - tests/ci/test_architecture_registry.py
  - docs/agents/tasks/active/FTAI-20260810-paper-g0-registry-lifecycle-1356.md
  - docs/agents/tasks/active/FTAI-20260810-paper-g0-registry-terminal-inventory-isolation-1356.md
shared_read_only:
  - ARCHITECTURE_REGISTRY.yaml
```

## Review finding being isolated

```yaml
reviewed_head: 5d2e65944c0a2a2d07f88ab403e9bd75b2b14e3f
reviewer: chatgpt-codex-connector
severity: P2
thread: PRRT_kwDOTdDTU86YAPja
summary: both open and resolved identity sets come from the same editable registry, so a terminal Issue can stay only in the open set unless an independent terminal-state source is checked
selected_remediation: pinned terminal identity inventory in the validator
remediation_head: b10426611f9a910fa035d371e788a8307326d849
```

## Implementation evidence

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
repair_cycles_for_current_isolation: 1
```

## Checkpoint

```yaml
checkpoint_version: 2
updated_at: 2026-08-10T21:26:29+02:00
last_progress_at: 2026-08-10T21:26:29+02:00
status: validating
next_action: Resolve the P2 review thread as remediated, request a fresh Codex review of the current PR head, inspect exact changed paths and exact-head CI once, then prepare same-PR task archival only after the independent review is materially clear.
```
