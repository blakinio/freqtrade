---
task_id: FTAI-20260722-portal-p5-model-control
status: active
branch: feat/portal-p5-model-control
base_branch: develop
created: 2026-07-22
updated: 2026-07-22
related_pr: null
owned_paths:
  - ai_platform/portal/model_control/
  - tests/ai_platform/portal/model_control/
  - docs/ai_platform/portal/MODEL_CONTROL_FOUNDATION.md
  - docs/agents/tasks/FTAI-20260722-portal-p5-model-control.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/AGENT_EXECUTION_PLAN.md
  - docs/ai_platform/portal/AI_ML_AND_LEARNING_ARCHITECTURE.md
  - docs/ai_platform/portal/ARCHITECTURE_DECISIONS.md
  - ai_platform/portal/contracts/models.py
  - ai_platform/portal/contracts/bots.py
  - ai_platform/portal/contracts/audit.py
  - ai_platform/portal/contracts/events.py
  - ai_platform/registry/README.md
search_first:
  - current develop and open PRs or active tasks overlapping model_control ownership
  - canonical P1 model, bot, audit and event contracts
  - existing research registry semantics
  - P2 transaction, audit and outbox patterns
optional_reads:
  - only model lifecycle implementation-adjacent files when a concrete blocker requires them
---

# AI Trading Portal P5 — Model Lifecycle Control

## Goal

Implement portal-side immutable model metadata and controlled registration, promotion, rollback and new-assignment validation without performing new model research, mutating model artifacts in place, or changing protected AI research evidence.

## Deliverables

- immutable tenant-scoped `ModelVersion` persistence using the canonical P1 identity contract;
- explicit candidate/validated model registration separated from activation;
- tenant/model-family/environment promotion slots for controlled future assignment policy;
- explicit audited promotion and rollback over immutable model versions;
- rollback restricted to a version previously promoted in the same tenant/family/environment slot;
- a read-only guard for validating a new `BotConfigRevision` model assignment without mutating P2-owned bot/config state;
- transactional audit/outbox evidence using canonical P1 actions/events;
- SQL migration, targeted tests and implementation documentation.

## Non-negotiable boundaries

- Do not modify upstream `freqtrade/` core.
- Do not perform training, tuning, backtesting, model comparison or new research in P5.
- Do not access protected final holdout v2 `20260801-20260930`.
- Do not alter frozen thresholds `0.006/-0.009`, completed Phase 6, authoritative `selected_model = null`, or frozen PyTorch/RL evidence.
- Existing research registry remains evidence-oriented and read-only input/reference; it is not runtime activation authority.
- Do not mutate an existing model artifact or canonical `ModelVersion` record in place.
- Registering a model must not change any promotion slot or existing `BotConfigRevision`.
- Promotion/rollback changes only P5 promotion-slot policy; it does not rewrite an existing P2 bot/config revision or running runtime.
- A new bot assignment remains an immutable P2 `BotConfigRevision`; P5 only validates whether its pinned model is the currently promoted slot target.
- Do not modify P2/P4 owned paths or P1 contracts in this task.
- Do not enable live capital or treat `LIVE_SMALL`/`PRODUCTION` model lifecycle states as P5-assignable.

## Acceptance criteria

1. Canonical `ModelVersion` JSON is stored immutably and duplicate identity cannot overwrite prior metadata.
2. Tenant isolation prevents cross-tenant model reads, promotion, rollback or assignment validation.
3. Registration writes model metadata + `model.registered` audit/outbox atomically but leaves promotion slots unchanged.
4. Promotion requires `model.promote`, an eligible non-live lifecycle state, and writes slot + transition + `model.promoted` audit/outbox atomically.
5. Rollback requires `model.promote`, targets a different immutable version previously promoted in the same slot, and writes `model.rolled_back` audit/outbox atomically.
6. Candidate/experimental/rejected/deprecated and live-capital lifecycle states cannot become P5 promotion-slot targets.
7. New-assignment validation accepts only a same-tenant `BotConfigRevision` whose pinned model matches the current promoted slot for that model family/environment; it does not mutate the revision.
8. Outbox failure rolls back model registration or promotion-slot mutation in the same transaction.
9. Protected research boundaries remain unchanged.
10. Targeted tests, AI Platform validation, Ruff, formatter, pre-commit, mypy and required repository CI pass before merge.

## Validation

- Use the narrowest model-control tests first when executable local runtime is available.
- In this connector-only session, use repository CI as the executable validation gate.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-22T20:05:00+02:00
head: 9a47f21e5a2c3b124ed2a24ecc0fad61bb8149c5
branch: feat/portal-p5-model-control
pr: null
status: active
context_routes:
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/AGENT_EXECUTION_PLAN.md
  - docs/ai_platform/portal/AI_ML_AND_LEARNING_ARCHITECTURE.md
owned_paths:
  - ai_platform/portal/model_control/
  - tests/ai_platform/portal/model_control/
  - docs/ai_platform/portal/MODEL_CONTROL_FOUNDATION.md
  - docs/agents/tasks/FTAI-20260722-portal-p5-model-control.md
proven:
  - PR #123 added canonical model.registered audit and model.rolled_back audit/event vocabulary and was squash-merged to develop as 9a47f21e5a2c3b124ed2a24ecc0fad61bb8149c5 after AI Platform CI, Freqtrade CI and zizmor passed.
  - P2 persists domain state, audit and outbox evidence atomically and BotConfigRevision already pins an immutable model_version.
  - Canonical ModelVersion pins artifact/hash/features/dataset/training pipeline/parameters/Git identity and is frozen by the P1 contract.
  - Existing research registry records evidence states and explicitly does not promote or execute models by itself.
  - MODEL_TRAIN, MODEL_READ and MODEL_PROMOTE permissions already exist; MODEL_REVIEWER has model.promote and model.read.
  - No model_control implementation path exists on current develop.
derived:
  - A P5-owned promotion slot can govern future model assignment without mutating existing immutable bot config revisions.
  - Rollback should select a previously promoted immutable version in the same slot, not mutate the current model artifact.
unknown: []
conflicts: []
first_failure:
  marker: none
  evidence: none
rejected_hypotheses:
  - Mutate ModelVersion lifecycle/artifact fields in place.
  - Treat research registry promotion_status as automatic runtime activation authority.
  - Maintain a second mutable bot model pointer that can diverge from BotConfigRevision.
  - Use model.promoted to ambiguously encode rollback.
changed_paths:
  - docs/agents/tasks/FTAI-20260722-portal-p5-model-control.md
validation:
  - command: PR #123 required CI
    result: PASS
    evidence: AI Platform CI 29942106177, Freqtrade CI 29942106185 and zizmor 29942109186 passed on the final contract-change head; Pre-commit Types update was skipped.
  - command: develop verification
    result: PASS
    evidence: develop was identical to contract merge SHA 9a47f21e5a2c3b124ed2a24ecc0fad61bb8149c5 before resetting this P5 branch.
blockers: []
next_action: Implement P5 model_control schema, repository and service with immutable model registration, promotion slots, explicit rollback, assignment validation and transactional audit/outbox evidence, then add targeted tests and migration coverage.
```
