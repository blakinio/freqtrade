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
status: implementing
base_branch: develop
trusted_base_sha: 3f60af82000cac47baa0a3a4302603eb1522363f
branch: feat/wickhunter-unified-runtime-mode-1396
related_issue: 1396
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
- `A9`: focused tests prove SHADOW, eligible PAPER, ineligible PAPER, LIVE/RESEARCH rejection and zero-authority invariants.
- `A10`: do not modify paths owned by PR #1388; document the consumer handoff needed for full Portal/runtime-generation/browser completion.

## Owned paths for this slice

```yaml
owned_paths:
  - ai_platform/wickhunter/runtime_mode.py
  - tests/ai_platform/wickhunter/test_runtime_mode.py
  - docs/agents/tasks/active/FTAI-20260808-wickhunter-unified-runtime-mode.md
```

## Required consumer after #1357 / PR #1388

The canonical Portal integration must later bind this mode contract into:

```text
BotConfigRevision
  -> normalized runtime config digest
  -> RuntimeGeneration
  -> explicit rollout
  -> observed generation reconciliation
```

The UI may offer SHADOW and PAPER only according to server-provided eligibility. LIVE remains visibly unavailable until a separate live-capital authorization package exists.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-08T23:36:00+02:00
branch: feat/wickhunter-unified-runtime-mode-1396
issue: 1396
status: implementing
phase: producer_contract
execution_mode: chat_github_actions
context_pressure: low
context_growth: stable
decomposition_decision: phased
session_rotation_count: 0
invocation_started_at: 2026-08-08T23:31:00+02:00
last_progress_at: 2026-08-08T23:36:00+02:00
ci_checks_for_current_head: 0
unchanged_state_checks: 0
identical_failure_retries: 0
repair_cycles_for_current_gate: 0
repair_cycle_generation: unified_runtime_mode_contract
context_reconstruction_attempts: 0
stall_warnings: 0
proven:
  - canonical WickHunter BotMode already defines RESEARCH, SHADOW, PAPER, LIVE_BLOCKED
  - existing PAPER request and observation contracts accept SHADOW/PAPER and enforce zero real-trading authority
  - PR 1388 owns Portal RuntimeGeneration and rollout paths, so this slice must not fork that authority
unknown:
  - final Portal mode selector and RuntimeGeneration binding until PR 1388 integration seam is stable
conflicts: []
blockers:
  - full_stack_completion_depends_on_pr_1388
next_action: Implement and test the conflict-free WickHunter runtime-mode producer contract, then hand it to the canonical RuntimeGeneration consumer instead of creating a parallel authority.
```
