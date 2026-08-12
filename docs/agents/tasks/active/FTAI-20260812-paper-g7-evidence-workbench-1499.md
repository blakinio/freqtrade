# FTAI-20260812 PAPER G7 Evidence Workbench producer

```yaml
policy_version: 2
prompting_standard_version: 2.1
task_id: FTAI-20260812-paper-g7-evidence-workbench-1499
project_lane: paper-platform
phase: validate
status: validating
execution_mode: codex
run_scope: single_task
continuation_policy: continue_until_real_stop
task_completion_policy: checkpoint_only
user_communication: terminal_only
feature_scope:
  type: contract_producer
  user_facing: false
  backend_required: true
  frontend_required: false
  integration_required: false
  e2e_required: false
  completion_claim: partial_producer
branch: codex/paper-g7-evidence-workbench
base: develop@ec41d2542bff57f74cd10856b7dc22265213d991
pull_request: pending
issue: 1499
invocation_started_at: 2026-08-12T10:58:00+02:00
last_progress_at: 2026-08-12T11:19:00+02:00
ci_checks_for_current_head: 0
unchanged_state_checks: 0
identical_failure_retries: 0
repair_cycles_for_current_gate: 1
context_reconstruction_attempts: 0
stall_warnings: 0
```

## Objective and ownership

Produce deterministic, immutable, fail-closed PAPER eligibility decisions from supplied evidence
and explicit policy. Owned paths are `ai_platform/portal/evidence_workbench/**`,
`tests/ai_platform/portal/evidence_workbench/**`, and this record.

## Safety and delivery boundary

This is a dependency-light `partial_producer`. It adds no persistence, migrations, execution,
exchange credentials, orders, withdrawals, deployment, promotion, or runtime authority. SHADOW is
distinct and cannot satisfy PAPER mode. LIVE is rejected and remains unavailable. AI suggestions
are evidence only and cannot override deterministic rules.

## Acceptance and future integrations

- Immutable canonical evidence and stable decision identities.
- Explicit AVAILABLE, UNAVAILABLE, STALE, INVALID, CONFLICTING and NOT_APPLICABLE states.
- Fail-closed identity, generation, profile, provenance, freshness, validation, completeness and
  realism checks with stable reason codes.
- Duplicate exact evidence is idempotent; conflicting slot reuse is rejected.
- Future consumers/adapters: G4 reconciliation, PaperExecutionProfile, Portfolio Risk,
  RuntimeGeneration/run evidence, durable storage, Portal API and UI.
- Real E2E: `NOT_APPLICABLE` because this isolated producer intentionally has no integrated
  persistence, runtime, API, or UI consumer.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-12T09:16:00Z
head: ec41d2542bff57f74cd10856b7dc22265213d991
branch: codex/paper-g7-evidence-workbench
pr: none
status: validating
context_routes:
  - docs/ai_platform/portal/PAPER_PLATFORM_IMPLEMENTATION_PLAN.md
owned_paths:
  - ai_platform/portal/evidence_workbench/**
  - tests/ai_platform/portal/evidence_workbench/**
  - docs/agents/tasks/active/FTAI-20260812-paper-g7-evidence-workbench-1499.md
proven:
  - live develop was ec41d2542bff57f74cd10856b7dc22265213d991 at task start
  - PRs 1494 through 1498 own separate producer paths with no Evidence Workbench conflict
  - focused pytest passed 20 tests; Ruff, mypy, compileall and diff-check passed
  - Gemma extracted conventions and adversarial cases; Codex independently verified used results
  - fresh Gemma review found one material optional-identity weakness; exact binding repair passed regression
derived:
  - isolated producer can integrate later through read-only ports without binding unfinished producers
unknown:
  - exact-head GitHub CI result after draft PR publication
conflicts:
  - none
first_failure:
  marker: none
  evidence: none
rejected_hypotheses:
  - direct imports from active G4/G6/G7 producers are unnecessary and would create unstable coupling
changed_paths:
  - ai_platform/portal/evidence_workbench/**
  - tests/ai_platform/portal/evidence_workbench/**
  - docs/agents/tasks/active/FTAI-20260812-paper-g7-evidence-workbench-1499.md
validation:
  - command: focused pytest
    result: PASS
    evidence: 20 passed
  - command: Ruff check and format check
    result: PASS
    evidence: local exact working tree
  - command: mypy and compileall
    result: PASS
    evidence: local exact working tree
  - command: producer E2E
    result: NOT_APPLICABLE
    evidence: isolated contract producer has no persistence runtime API or UI consumer
blockers:
  - none
next_action: Perform independent review, commit, push and open a draft PR targeting develop.
```
