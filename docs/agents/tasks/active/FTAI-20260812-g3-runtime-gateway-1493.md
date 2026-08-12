---
task_id: FTAI-20260812-g3-runtime-gateway-1493
programme_id: FTAI-PROGRAM-AI-TRADING-PORTAL
project_lane: freqtrade-portal
status: ready
task_kind: implementation
priority: high
repository: blakinio/freqtrade
base_branch: develop
base_head: 111b861426cd73072c507da4d2c4dbbcdc80dc51
dispatch_anchor: 111b861426cd73072c507da4d2c4dbbcdc80dc51
branch: codex/g3-runtime-gateway-1493
related_pr: 1497
issue: 1493
created: 2026-08-12
updated: 2026-08-12
live_capital_authorized: false
production_deployment_authorized: false
---

# G3 generation-bound Runtime Gateway producer

## Delivery classification

```yaml
feature_scope:
  type: contract_producer
  user_facing: false
  backend_required: true
  frontend_required: false
  integration_required: true
  e2e_required: true
  completion_claim: partial_producer
delivery_matrix:
  persistence: not_applicable_no_gateway_owned_persistence
  backend_domain: required
  authorization: required
  validation: required
  api_or_transport_contract: required
  frontend_data_access: dependent_on_G4_reconciliation
  frontend_ui: not_applicable_non_public_machine_boundary
  integration: dependent_on_G3_supervisor
  e2e: dependent_on_G3_supervisor_and_final_G3_real_runtime_E2E
```

## Scope and ownership

Owned paths are `ai_platform/portal/runtime_gateway/**`,
`tests/ai_platform/portal/runtime_gateway/**`, and this task record. Runtime Supervisor,
container-engine lifecycle, RuntimeGeneration persistence/migrations, deployment, web,
WickHunter, G4 reconciliation, and G6/G7 producers are excluded.

The Gateway is PAPER-only, generation-local, UDS-only, and a narrow allow-listed
protocol boundary. It never receives Docker authority, creates containers, exposes a
generic upstream proxy, accepts LIVE mode, or treats acknowledgement as execution truth.

## Checkpoint

```yaml
policy_version: 2
prompting_standard_version: 2.1
phase: handover
session_id: codex-20260812-g3-gateway-1493
session_role: producer
execution_mode: codex
execution_reason: bounded multi-file protocol implementation and focused security tests
context_pressure: medium
context_growth: stable
context_score: 8
decomposition_decision: single
decomposition_reason: one cohesive producer boundary with coordinator-owned integration
invocation_started_at: 2026-08-12T08:30:00Z
last_progress_at: 2026-08-12T09:00:00Z
ci_checks_for_current_head: 0
unchanged_state_checks: 0
identical_failure_retries: 0
repair_cycles_for_current_gate: 0
context_reconstruction_attempts: 0
stall_warnings: 0
status: ready
blockers: []
changed_paths:
  - ai_platform/portal/runtime_gateway/**
  - tests/ai_platform/portal/runtime_gateway/**
  - docs/agents/tasks/active/FTAI-20260812-g3-runtime-gateway-1493.md
validation:
  - command: python -m pytest -q -o addopts='' --confcutdir=tests/ai_platform tests/ai_platform/portal/runtime_gateway
    result: PASS_24_tests_3_platform_skips
  - command: python -m ruff check ai_platform/portal/runtime_gateway tests/ai_platform/portal/runtime_gateway
    result: PASS
  - command: python -m mypy ai_platform/portal/runtime_gateway tests/ai_platform/portal/runtime_gateway
    result: PASS
dependencies:
  - G3 Runtime Supervisor producer
  - coordinator-owned Supervisor + Gateway real-runtime E2E
pull_request:
  number: 1497
  state: open_draft
completion_claim: partial_producer
live: unavailable
next_action: Coordinator audits PR 1497 and composes G3 Supervisor integration plus final G3 E2E; do not merge this producer alone.
```
