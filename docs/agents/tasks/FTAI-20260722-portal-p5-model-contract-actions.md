---
task_id: FTAI-20260722-portal-p5-model-contract-actions
status: active
branch: fix/portal-p5-model-lifecycle-actions
base_branch: develop
created: 2026-07-22
updated: 2026-07-22
related_pr: null
owned_paths:
  - ai_platform/portal/contracts/audit.py
  - ai_platform/portal/contracts/events.py
  - tests/ai_platform/portal/test_model_lifecycle_contract_actions.py
  - docs/agents/tasks/FTAI-20260722-portal-p5-model-contract-actions.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/AGENT_EXECUTION_PLAN.md
  - ai_platform/portal/contracts/audit.py
  - ai_platform/portal/contracts/events.py
search_first:
  - current develop and open contract-change PRs
  - P5 model_control checkpoint and rollback vocabulary gap
optional_reads:
  - only P1 contract tests needed for the additive vocabulary change
---

# AI Trading Portal P5 — Additive model lifecycle contract actions

## Goal

Add the smallest P1 vocabulary extension required for P5 to represent model registration and rollback unambiguously in canonical audit/outbox evidence.

## Deliverables

- add canonical audit action for `model.registered`;
- add canonical audit action and event type for `model.rolled_back`;
- preserve all existing contract fields and enum values;
- add focused contract regression coverage;
- do not implement model-control persistence or services in this task.

## Non-negotiable boundaries

- Additive enum vocabulary only; no schema field or version change.
- Do not modify P2, P4 or `model_control` implementation paths.
- Do not perform research, promotion, model assignment, training, tuning or holdout access.
- Do not alter frozen thresholds, completed Phase 6, `selected_model = null`, or PyTorch/RL evidence.
- Do not introduce ad-hoc event/audit strings outside canonical P1 contracts.

## Acceptance criteria

1. `AuditAction.MODEL_REGISTERED` serializes as `model.registered`.
2. `AuditAction.MODEL_ROLLED_BACK` serializes as `model.rolled_back`.
3. `EventType.MODEL_ROLLED_BACK` serializes as `model.rolled_back`.
4. Existing `model.promoted` audit/event values remain unchanged.
5. Focused contract tests and required repository CI pass.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-22T19:38:00+02:00
head: 8c0fb81e7b605a74c41b32f48ecfab7fa6094ff5
branch: fix/portal-p5-model-lifecycle-actions
pr: null
status: active
context_routes:
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/AGENT_EXECUTION_PLAN.md
owned_paths:
  - ai_platform/portal/contracts/audit.py
  - ai_platform/portal/contracts/events.py
  - tests/ai_platform/portal/test_model_lifecycle_contract_actions.py
  - docs/agents/tasks/FTAI-20260722-portal-p5-model-contract-actions.md
proven:
  - P2 writes state, audit and outbox evidence atomically for domain mutations.
  - Canonical P1 vocabulary contained model.promoted but no dedicated rollback action/event.
  - Using model.promoted for rollback would make the business action ambiguous.
  - Candidate registration had EventType.MODEL_REGISTERED but no matching canonical AuditAction.
  - The implementation adds only AuditAction.MODEL_REGISTERED, AuditAction.MODEL_ROLLED_BACK and EventType.MODEL_ROLLED_BACK while preserving existing enum values.
derived:
  - After this additive contract change merges, P5 can implement registration, promotion and rollback evidence without ad-hoc action/event strings.
unknown: []
conflicts: []
first_failure:
  marker: none
  evidence: No validation failure has been observed yet.
rejected_hypotheses:
  - Encode rollback as model.promoted with a payload flag.
  - Emit raw model.rollback strings outside P1 enums.
changed_paths:
  - ai_platform/portal/contracts/audit.py
  - ai_platform/portal/contracts/events.py
  - tests/ai_platform/portal/test_model_lifecycle_contract_actions.py
  - docs/agents/tasks/FTAI-20260722-portal-p5-model-contract-actions.md
validation:
  - command: GitHub live-state preflight
    result: PASS
    evidence: Branch created from develop 23724dff8674da37bcdfa4d7c8e363d1afd2629d after confirming the P5 vocabulary gap.
  - command: Focused/local contract validation
    result: NOT_RUN
    evidence: Local repository execution is unavailable in this connector-only session; GitHub CI will be used as the executable validation gate.
blockers: []
next_action: Open a pull request against current develop, verify the diff remains additive and scope-limited, then use required CI as the validation gate before merging and resuming P5 model_control.
```
