---
task_id: FTAI-20260812-g3-runtime-gateway-1493
programme_id: FTAI-PROGRAM-AI-TRADING-PORTAL
project_lane: freqtrade-portal
status: validating
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

## Fresh coordinator finding and repair

The coordinator audited the Gateway's reviewed endpoints against the repository's actual Freqtrade API implementation. `freqtrade/rpc/api_server/api_trading.py` exposes `/status` and `/trades` but no `GET /open_orders`; the producer had mapped `read_open_orders` to a nonexistent `/api/v1/open_orders` endpoint. That mapping would have made the real G3 runtime E2E fail despite unit tests using a permissive fake upstream.

The producer is repaired so:

- `read_open_orders` reads Freqtrade's canonical `/api/v1/status` response;
- only orders with `is_open=true` are returned;
- malformed trade/order shapes fail closed with `MALFORMED_UPSTREAM_RESPONSE`;
- the nonexistent `/api/v1/open_orders` path is removed from the upstream allow-list;
- focused tests verify the real endpoint mapping, open-order derivation and malformed-response rejection.

## Checkpoint

```yaml
policy_version: 2
prompting_standard_version: 2.1
phase: exact_head_validation
session_id: coordinator-20260812-g3-gateway-1493
session_role: coordinator_auditor_and_repairer
execution_mode: github_only
execution_reason: producer audit found a repository-verifiable Freqtrade API compatibility defect
context_pressure: medium
context_growth: stable
context_score: 8
decomposition_decision: single
decomposition_reason: repair remains inside the producer-owned Gateway boundary
invocation_started_at: 2026-08-12T08:30:00Z
last_progress_at: 2026-08-12T10:36:00Z
ci_checks_for_current_head: 0
unchanged_state_checks: 0
identical_failure_retries: 0
repair_cycles_for_current_gate: 1
context_reconstruction_attempts: 0
stall_warnings: 0
status: validating
blockers: []
changed_paths:
  - ai_platform/portal/runtime_gateway/**
  - tests/ai_platform/portal/runtime_gateway/**
  - docs/agents/tasks/active/FTAI-20260812-g3-runtime-gateway-1493.md
verified_findings:
  - finding: nonexistent_Freqtrade_open_orders_endpoint
    evidence: freqtrade/rpc/api_server/api_trading.py exposes /status and /trades; no GET /open_orders route exists
    result: remediated
validation:
  - previous focused producer suite: PASS_24_tests_3_platform_skips
  - fresh exact-head GitHub CI: pending
dependencies:
  - G3 Runtime Supervisor producer
  - coordinator-owned Supervisor + Gateway real-runtime E2E
pull_request:
  number: 1497
  state: open_draft
completion_claim: partial_producer
live: unavailable
next_action: Complete fresh exact-head producer audit/CI, then coordinator composes Supervisor + Gateway and proves final G3 with real Docker/UDS E2E; do not merge this producer alone.
```
