---
task_id: FTAI-20260722-portal-p5-model-control
status: active
branch: feat/portal-p5-model-control
base_branch: develop
created: 2026-07-22
updated: 2026-07-22
related_pr: "#124"
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
updated_at: 2026-07-22T20:50:00+02:00
head: 6032c00d2114c6f64ac1c75214b83c4be5988ed9
branch: feat/portal-p5-model-control
pr: "#124"
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
  - P5 stores canonical ModelVersion JSON under tenant/model identity with no repository update path and rejects duplicate identities instead of overwriting metadata.
  - Registration is separate from promotion slots and writes model metadata, canonical audit and canonical outbox evidence in one transaction.
  - Promotion slots are scoped by tenant/model_family/environment and do not modify existing immutable BotConfigRevision state.
  - Promotion and rollback append transition history and write audit/outbox evidence atomically with slot mutation.
  - Rollback targets must have prior explicit PROMOTE history in the same slot and must remain in an assignable non-live lifecycle state.
  - New-assignment validation is read-only and requires the BotConfigRevision pinned model to equal the current promoted slot target.
  - Targeted tests cover immutable duplicate rejection, tenant isolation, permissions, lifecycle eligibility, no silent activation, promotion, rollback provenance, assignment validation and transaction rollback on outbox failure.
  - SQLite test persistence returns timezone-aware columns as naive datetimes; repository read adapters normalize those values to UTC before rebuilding strict P1 contracts.
  - P5 package import ordering follows repository Ruff policy including two blank lines after imports; all temporary lint diagnostics and suppressions were removed before final validation.
  - Sync PR #131 merged current develop 7c8ced80b2b445144a26112e69f8c1cbd475b13e into feat/portal-p5-model-control as merge commit 6032c00d2114c6f64ac1c75214b83c4be5988ed9.
  - After synchronization, develop is the merge base and the PR #124 diff is limited to the 11 declared P5 model_control/test/docs/task files.
derived:
  - P5 controls future assignment policy without creating a mutable per-bot model pointer that can diverge from BotConfigRevision.
  - Applying a changed promoted model to a bot remains a future explicit immutable P2 revision workflow, not an in-place P5 mutation.
unknown: []
conflicts: []
first_failure:
  marker: sqlite-timezone-roundtrip
  evidence: Initial P5 AI Platform tests failed because SQLite returned DateTime(timezone=True) slot/history values without tzinfo and strict P1 UtcDateTime rejected them; repository read normalization to UTC resolved the failure.
rejected_hypotheses:
  - Mutate ModelVersion lifecycle/artifact fields in place.
  - Treat research registry promotion_status as automatic runtime activation authority.
  - Maintain a second mutable bot model pointer that can diverge from BotConfigRevision.
  - Use model.promoted to ambiguously encode rollback.
  - Persist temporary nested Ruff configuration or file-wide lint suppression as a production fix.
changed_paths:
  - ai_platform/portal/model_control/__init__.py
  - ai_platform/portal/model_control/database.py
  - ai_platform/portal/model_control/migrations/0001_model_control.sql
  - ai_platform/portal/model_control/models.py
  - ai_platform/portal/model_control/repository.py
  - ai_platform/portal/model_control/schema.py
  - ai_platform/portal/model_control/service.py
  - tests/ai_platform/portal/model_control/test_model_control_migration.py
  - tests/ai_platform/portal/model_control/test_model_control_service.py
  - docs/ai_platform/portal/MODEL_CONTROL_FOUNDATION.md
  - docs/agents/tasks/FTAI-20260722-portal-p5-model-control.md
validation:
  - command: PR #123 required CI
    result: PASS
    evidence: AI Platform CI 29942106177, Freqtrade CI 29942106185 and zizmor 29942109186 passed before the prerequisite contract change merged.
  - command: P5 clean implementation AI Platform CI 29947726640
    result: PASS
    evidence: Compile, AI Platform tests, Ruff, Ruff format, Codespell and JSON validation passed with temporary diagnostics removed before develop synchronization.
  - command: P5 live base synchronization
    result: PASS
    evidence: PR #131 merged develop 7c8ced80b2b445144a26112e69f8c1cbd475b13e into the P5 feature branch; compare now reports the feature branch ahead and 0 behind develop with only P5 paths in the diff.
blockers: []
next_action: Verify required CI and review state on the synchronized final checkpoint head of PR #124, fix any concrete failure, then squash-merge when green and verify develop before closing P5 with one successor next_action.
```
