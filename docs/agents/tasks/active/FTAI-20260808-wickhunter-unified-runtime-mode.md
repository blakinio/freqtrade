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
- reconstructed capability and zero-authority fields require exact boolean values, and `orders_submitted` requires an actual integer zero rather than merely falsey/equal values;
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

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-09T00:18:00+02:00
head: UNKNOWN
branch: feat/wickhunter-unified-runtime-mode-1396
pr: 1397
status: validating
context_routes:
  - docs/agents/PROMPTING_STANDARD.md
  - docs/agents/PROMPTING_HANDOVER.md
  - docs/agents/AUTONOMOUS_PROGRAM_CONTINUATION.md
  - ai_platform/wickhunter/runtime_mode.py
  - tests/ai_platform/test_wickhunter_runtime_mode.py
  - PR #1388 canonical RuntimeGeneration consumer
owned_paths:
  - ai_platform/wickhunter/runtime_mode.py
  - tests/ai_platform/test_wickhunter_runtime_mode.py
  - docs/agents/tasks/active/FTAI-20260808-wickhunter-unified-runtime-mode.md
proven:
  - canonical WickHunter BotMode is reused for SHADOW PAPER RESEARCH and LIVE_BLOCKED
  - SHADOW resolves with exact zero real-trading authority
  - PAPER requires typed positive authorization plus immutable authorization and candidate identity
  - malformed truthy PAPER authorization fails closed
  - reconstructed PAPER requires authorization identity and SHADOW forbids it
  - raw string runtime modes fail closed instead of relying on StrEnum equality
  - reconstructed zero-authority booleans and orders_submitted require exact canonical types
  - LIVE_BLOCKED and RESEARCH fail closed for this managed runtime path
  - canonical request and resolution digests bind mode and PAPER authorization identity
  - producer code before the latest type-hardening passed Freqtrade component CodeQL and zizmor gates
  - PR #1388 owns Portal RuntimeGeneration and rollout paths and this producer does not fork that authority
derived:
  - the producer can be consumed as immutable generation material after canonical RuntimeGeneration integration
unknown:
  - final Portal mode selector and desired versus observed mode binding until PR #1388 consumer integration is completed
conflicts: []
first_failure:
  marker: FINAL_REVIEW_P2_EXACT_ZERO_AUTHORITY_TYPES_AND_CHECKPOINT_CONTRACT
  evidence: Codex terminal review on aa1608b584d3d8daa945b865b4fae37a12b6aa68 identified falsey noncanonical authority values and an invalid custom checkpoint schema
rejected_hypotheses:
  - truthiness or equality is sufficient to prove canonical zero-authority field types
  - a custom checkpoint_version 3 record is acceptable to the repository checkpoint parser
changed_paths:
  - ai_platform/wickhunter/runtime_mode.py
  - tests/ai_platform/test_wickhunter_runtime_mode.py
  - docs/agents/tasks/active/FTAI-20260808-wickhunter-unified-runtime-mode.md
validation:
  - command: Freqtrade CI on 137cac48e03f78e349793361153e12507bd7e544
    result: PASS
    evidence: run 31280734057
  - command: Risk-aware AI Platform component CI on 137cac48e03f78e349793361153e12507bd7e544
    result: PASS
    evidence: run 31280734172 including tests lint format codespell and sensitive-data scan
  - command: CodeQL on 137cac48e03f78e349793361153e12507bd7e544
    result: PASS
    evidence: run 31280708632
  - command: zizmor on 137cac48e03f78e349793361153e12507bd7e544
    result: PASS
    evidence: run 31280708686
  - command: exact final head CI after zero-authority type hardening and checkpoint repair
    result: NOT_RUN
    evidence: resolve PR #1397 live head after this documentation successor and require all applicable gates before merge
blockers:
  - full stack Portal completion depends on canonical RuntimeGeneration consumer PR #1388
  - producer merge requires fresh exact-final-head CI and independent review with no material P1 or P2
next_action: Resolve PR #1397 live head after this checkpoint commit, run exact-final-head CI and independent review, merge the producer only when all applicable gates pass, then integrate it into PR #1388 rather than creating a parallel RuntimeGeneration authority.
```
