---
task_id: FTAI-20260722-portal-p5-model-control
status: done
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

## Delivered

- immutable tenant-scoped canonical `ModelVersion` persistence;
- registration separated from promotion/activation policy;
- tenant/model-family/environment promotion slots;
- append-only promotion and rollback transition history;
- rollback restricted to versions previously promoted in the same slot;
- read-only validation for new immutable `BotConfigRevision` model assignments;
- atomic domain state + canonical audit + outbox persistence;
- tenant isolation, permission and lifecycle eligibility enforcement;
- SQL migration, implementation documentation and targeted regression tests.

## Non-negotiable boundaries preserved

- upstream `freqtrade/` core unchanged;
- no training, tuning, backtesting or new model research performed by P5;
- protected final holdout v2 `20260801-20260930` not accessed;
- frozen thresholds `0.006/-0.009`, completed Phase 6 and `selected_model = null` unchanged;
- PyTorch/RL research evidence not treated as promotion authorization;
- no live-capital enablement;
- P2 immutable bot/config state is not rewritten by P5 promotion or rollback.

## Acceptance result

All P5 acceptance criteria are satisfied on merged repository state.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-22T21:15:38+02:00
head: 0de1d3003d842f2f65890b21342ce9943458d5bd
branch: develop
pr: "#124"
status: done
context_routes:
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/AGENT_EXECUTION_PLAN.md
  - docs/ai_platform/portal/AI_ML_AND_LEARNING_ARCHITECTURE.md
proven:
  - PR #123 added canonical model.registered audit and model.rolled_back audit/event vocabulary and merged before P5 implementation.
  - P5 stores canonical ModelVersion JSON under tenant/model identity with no repository update path and rejects duplicate identities instead of overwriting metadata.
  - Registration leaves promotion slots unchanged and writes model metadata, audit and outbox evidence in one transaction.
  - Promotion and rollback mutate only P5 promotion policy, append transition history and write audit/outbox evidence atomically.
  - Rollback targets require prior explicit PROMOTE history in the same tenant/model-family/environment slot.
  - New-assignment validation is read-only and requires the immutable BotConfigRevision pinned model to match the current promotion slot.
  - SQLite datetime round-trip normalization is handled at the persistence-to-contract boundary before rebuilding strict UTC P1 contracts.
  - Targeted tests cover immutability, tenant isolation, permissions, lifecycle eligibility, no silent activation, promotion, rollback provenance, assignment validation and transaction rollback on outbox failure.
  - PR #124 final head 478c58afca078e61d38f282c5b0a778f71fcfcc7 passed AI Platform CI 29948943498, Freqtrade CI 29948943690 and zizmor 29948943482; Pre-commit Types update 29948943509 was skipped and not a failure gate.
  - PR #124 was squash-merged to develop as 0de1d3003d842f2f65890b21342ce9943458d5bd.
  - Post-merge comparison reports develop identical to 0de1d3003d842f2f65890b21342ce9943458d5bd.
  - P2 PR #116, P3 PR #118, P4 PR #119 and P5 PR #124 are merged, satisfying the stable-foundation entry condition for Wave C P6 web portal work.
derived:
  - P5 controls future model-assignment policy without creating a second mutable per-bot model pointer.
  - Applying a promoted model change to a bot remains a future explicit immutable P2 revision workflow.
unknown: []
conflicts: []
first_failure:
  marker: sqlite-timezone-roundtrip
  evidence: Initial P5 tests exposed SQLite returning timezone-aware columns as naive datetimes; UTC normalization in repository read adapters resolved the strict contract failure.
validation:
  - command: PR #124 final required CI
    result: PASS
    evidence: AI Platform CI 29948943498; Freqtrade CI 29948943690; zizmor 29948943482.
  - command: PR #124 review state
    result: PASS
    evidence: No submitted reviews and no review threads were present before merge.
  - command: Post-merge develop verification
    result: PASS
    evidence: develop is identical to squash merge SHA 0de1d3003d842f2f65890b21342ce9943458d5bd.
blockers: []
next_action: Declare and execute FTAI-20260722-portal-p6-web-shell from current develop, using canonical P1/P2 APIs and keeping all browser-to-Freqtrade access prohibited.
```
