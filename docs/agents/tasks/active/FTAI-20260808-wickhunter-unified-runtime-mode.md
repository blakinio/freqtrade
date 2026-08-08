# FTAI-20260808 — WickHunter Unified Runtime Mode

```yaml
task_id: FTAI-20260808-wickhunter-unified-runtime-mode
project_lane: freqtrade-wickhunter
programme: WickHunter
policy_version: 2
prompting_standard_version: 2.1
task_kind: implementation
feature_scope:
  type: full_stack
  user_facing: true
  backend_required: true
  frontend_required: true
  integration_required: true
  e2e_required: true
  completion_claim: partial_producer
execution_mode: chat_github_actions
run_scope: autonomous_program
continuation_policy: continue_until_real_stop
task_completion_policy: checkpoint_and_handover
implementation_authorized: true
status: validating
base_branch: develop
trusted_base_sha: 3f60af82000cac47baa0a3a4302603eb1522363f
branch: feat/wickhunter-unified-runtime-mode-1396
related_issue: 1396
related_pr: 1397
depends_on_issue: 1357
depends_on_pr: 1388
live_capital_authorized: false
trading_credentials_authorized: false
real_order_adapter_authorized: false
real_exchange_execution_authorized: false
```

## Objective

Implement the first conflict-free producer slice for Issue #1396: one canonical WickHunter runtime-mode contract that reuses the existing `BotMode` domain and safely resolves `SHADOW`, `PAPER`, and `LIVE_BLOCKED` without creating a second RuntimeGeneration authority.

This slice deliberately avoids every Portal/runtime-generation path currently owned by PR #1388. Full Portal selection, immutable RuntimeGeneration binding, desired/observed mode truth and browser E2E remain mandatory consumers after #1388 lands or exposes a stable integration seam.

## Frozen semantics

- `SHADOW`: market observation, inference, decision/evidence journaling; no exchange execution authority.
- `PAPER`: simulated positions/execution evidence only; no real exchange credentials, no real order adapter, no exchange orders, no live capital.
- `LIVE_BLOCKED`: never executable under this task. Validation must fail closed.
- A platform capability for PAPER does not make every candidate/model PAPER-eligible. Eligibility is explicit immutable input and an ineligible PAPER request must fail closed with a machine-readable reason.
- Mode changes are generation material. No API in this slice may mutate a running mode in place.

## Acceptance inventory

- `A1`: reuse canonical `BotMode`; do not create a competing WickHunter mode enum.
- `A2`: provide an immutable/versioned runtime-mode request/policy contract suitable for later inclusion in normalized bot config and RuntimeGeneration digest material.
- `A3`: resolve SHADOW to zero-authority observation capabilities.
- `A4`: resolve PAPER only when explicit PAPER eligibility/authorization evidence is present; otherwise reject fail-closed.
- `A5`: resolve PAPER to simulator/paper capabilities with zero real-trading authority.
- `A6`: reject `LIVE_BLOCKED` and `RESEARCH` as managed executable trading runtime modes in this product path.
- `A7`: expose stable machine-readable rejection reason codes.
- `A8`: prove canonical serialization/digest changes when mode or eligibility identity changes.
- `A9`: focused tests prove SHADOW, eligible PAPER, ineligible/malformed PAPER, LIVE/RESEARCH rejection, reconstruction/type invariants and zero-authority invariants.
- `A10`: do not modify paths owned by PR #1388; document the consumer handoff needed for full Portal/runtime-generation/browser completion.

## Owned paths for this slice

```yaml
owned_paths:
  - ai_platform/wickhunter/runtime_mode.py
  - tests/ai_platform/test_wickhunter_runtime_mode.py
  - docs/agents/tasks/active/FTAI-20260808-wickhunter-unified-runtime-mode.md
```

## Producer result

The bounded producer contract now provides:

- canonical `BotMode` reuse rather than another mode enum;
- immutable `ManagedRuntimeModeRequest` with canonical request digest;
- immutable `RuntimeModeResolution` with canonical resolution digest;
- SHADOW capability resolution with zero real-trading authority;
- PAPER capability resolution only with positive, typed boolean authorization plus immutable authorization/candidate identity material;
- direct reconstruction guards requiring a real `BotMode`, requiring a PAPER authorization digest for PAPER and forbidding it for SHADOW;
- raw string modes such as `"paper"` / `"shadow"` fail closed instead of relying on `StrEnum` equality;
- stable fail-closed reasons for missing, negative or malformed PAPER eligibility, LIVE-blocked requests, RESEARCH requests and unsupported mode/schema state;
- explicit `orders_submitted=0`, no credentials, no real order adapter, no real exchange execution, no live capital and no automatic promotion in every successful managed resolution.

The current WH09 H900 deployment is not made PAPER-eligible by this producer. It remains SHADOW until its own PAPER eligibility/authorization evidence exists.

## Required consumer after #1357 / PR #1388

The canonical Portal integration must bind this mode contract into:

```text
BotConfigRevision
  -> normalized runtime config digest
  -> RuntimeGeneration
  -> explicit rollout
  -> observed generation reconciliation
```

The UI may offer SHADOW and PAPER only according to server-provided eligibility. LIVE remains visibly unavailable until a separate live-capital authorization package exists.

## Validation evidence

```yaml
producer_code_head: 137cac48e03f78e349793361153e12507bd7e544
freqtrade_ci:
  run_id: 31280734057
  conclusion: success
risk_aware_component_ci:
  run_id: 31280734172
  conclusion: success
  ai_platform_tests_and_lint: success
codeql:
  run_id: 31280708632
  conclusion: success
zizmor:
  run_id: 31280708686
  conclusion: success
review_findings_repaired:
  - pytest_reserved_request_parameter
  - ruff_getattr_literal_field_access
  - ruff_format_runtime_mode_expression
  - PAPER_resolution_missing_authorization_identity
  - PAPER_non_boolean_authorization_input
  - reconstructed_raw_string_mode_bypassed_identity_checks
```

The documentation successor containing this checkpoint is not authorized to merge based on `producer_code_head`. Resolve PR #1397 live `head_sha` and require fresh exact-final-head CI/review before merge.

## Context checkpoint

```yaml
checkpoint_version: 3
updated_at: 2026-08-09T00:05:00+02:00
branch: feat/wickhunter-unified-runtime-mode-1396
issue: 1396
pr: 1397
status: validating
phase: producer_final_exact_head
execution_mode: chat_github_actions
context_pressure: medium
context_growth: controlled
decomposition_decision: phased
session_rotation_count: 0
invocation_started_at: 2026-08-08T23:31:00+02:00
last_progress_at: 2026-08-09T00:05:00+02:00
producer_code_head: 137cac48e03f78e349793361153e12507bd7e544
live_head_source: pr_1397
exact_final_head_required: true
ci_checks_for_current_head: 4
unchanged_state_checks: 0
identical_failure_retries: 0
repair_cycles_for_current_gate: 6
repair_cycle_generation: unified_runtime_mode_contract
context_reconstruction_attempts: 0
stall_warnings: 0
proven:
  - canonical WickHunter BotMode defines RESEARCH, SHADOW, PAPER, LIVE_BLOCKED and is reused
  - SHADOW resolves with zero real-trading authority
  - PAPER requires typed positive authorization plus immutable authorization/candidate identity and remains simulation-only
  - malformed truthy authorization input fails closed
  - reconstructed PAPER resolution cannot omit authorization identity and SHADOW cannot carry it
  - reconstructed/request modes must be actual BotMode instances; raw strings fail closed
  - LIVE_BLOCKED and RESEARCH fail closed for this managed runtime path
  - canonical request/resolution digests bind mode and PAPER authorization identity
  - code head 137cac48 passed Freqtrade CI, risk-aware AI Platform component CI, CodeQL and zizmor
  - all material P2 findings on the producer code head were repaired before this checkpoint
  - PR 1388 owns Portal RuntimeGeneration and rollout paths, so this producer did not fork that authority
unknown:
  - final Portal mode selector and RuntimeGeneration binding until PR 1388 consumer integration is completed
conflicts: []
blockers:
  - full_stack_completion_depends_on_pr_1388
next_action: Resolve PR #1397 live head, require fresh exact-final-head CI and independent review with no material P1/P2, merge the producer, then integrate it into canonical PR #1388 RuntimeGeneration/rollout truth rather than creating a parallel authority.
```
