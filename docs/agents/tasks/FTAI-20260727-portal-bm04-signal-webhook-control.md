---
task_id: FTAI-20260727-portal-bm04-signal-webhook-control
status: validating
branch: feat/portal-bm04-signal-webhook-control
base_branch: develop
created: 2026-07-27
updated: 2026-07-27
related_pr: 544
owned_paths:
  - ai_platform/portal/signal_control/**
  - tests/ai_platform/portal/signal_control/**
  - docs/agents/tasks/FTAI-20260727-portal-bm04-signal-webhook-control.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/BOT_MANAGEMENT_PRODUCT_ARCHITECTURE.md
  - docs/ai_platform/portal/BOT_MANAGEMENT_AGENT_PLAN.md
  - docs/ai_platform/portal/SYSTEM_ARCHITECTURE.md
  - docs/ai_platform/portal/SECURITY_ARCHITECTURE.md
  - docs/agents/prompts/PORTAL_BOT_MANAGEMENT_AGENT_PROMPTS.md
---

# BM-04 signal and webhook control

## Goal

Implement tenant-scoped, immutable and secret-safe signal endpoint configuration plus replay-resistant signal validation and deterministic advisory-or-command-intent mapping. No accepted signal is represented as execution success.

## Delivered

- Immutable endpoint revisions with optimistic revision checks and bounded replay/timestamp policy.
- Versioned strict `signal.v1` payload schema and explicit authentication-mode vocabulary.
- Opaque signature-verification interface with fail-closed unavailable-provider handling.
- Canonical payload digests, nonce hashing, signal replay protection and deterministic idempotency replay/conflict behavior.
- Stable validation, mapping and audit reason codes with deterministic serialization.
- Exact tenant, endpoint, bot, configuration and runtime revision binding.
- Deterministic mapping only to merged BM-00 signal intent and BM-03 lifecycle/position command vocabulary.
- Advisory-only and execution-authorized classifications; the latter creates a risk-gated command intent only.
- Simulator/preview processing that neither persists evidence nor consumes replay state.
- In-memory feature repository only; migrations and shared API composition remain integration-owner work.

## Safety boundary

The package does not resolve a secret provider, serialize or log a secret, call an exchange or Freqtrade, submit a BM-03 command, place or cancel an order, mutate runtime or position state, activate PI-08 or authorize live capital. `execution_performed` is structurally fixed to false.

## Validation

- `python -m compileall ai_platform/portal/signal_control tests/ai_platform/portal/signal_control` — pass.
- `pytest -q -o addopts='' tests/ai_platform/portal/signal_control` — 39 passed.
- Exact Ruff 0.15.21 fixes and formatting were generated and applied from isolated diagnostic artifact `8669739984`; the diagnostic PRs were closed or targeted only the feature branch and did not modify `develop`.
- Terminal exact-head AI Platform CI, Freqtrade CI/final gate and security analysis are pending this checkpoint head.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-28T00:15:00+02:00
head_parent: e22e8b60b18e0a831080a67d662327c6d3fadda4
branch: feat/portal-bm04-signal-webhook-control
pr: 544
status: validating
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/portal/BOT_MANAGEMENT_PRODUCT_ARCHITECTURE.md
  - docs/ai_platform/portal/BOT_MANAGEMENT_AGENT_PLAN.md
  - ai_platform/portal/contracts/bot_management/signals.py
  - ai_platform/portal/contracts/bot_management/commands.py
  - ai_platform/portal/bot_operations/service.py
owned_paths:
  - ai_platform/portal/signal_control/**
  - tests/ai_platform/portal/signal_control/**
  - docs/agents/tasks/FTAI-20260727-portal-bm04-signal-webhook-control.md
proven:
  - BM-00, BM-02 and BM-03 are merged into develop; BM-03 command acceptance remains intent-only.
  - A stale incomplete pre-existing BM-04 branch was safely reset to current develop before the bounded implementation was rebuilt.
  - Focused compile and 39 focused tests pass.
  - AI Platform tests passed before the original Ruff-only failure; exact Ruff 0.15.21 fixes and formatting are now applied.
  - GitHub Actions security analysis run 30307720858 passed on the preceding functional head.
  - The branch is synchronized with develop commit 2129c6ba1cfe578ac0113b457a87b9cd939d465a.
  - The PR changes exactly thirteen declared feature, test and checkpoint paths.
  - The package contains no API route, migration, BFF change, provider implementation or execution adapter call.
derived:
  - Shared API registration and durable database migration remain integration-owner responsibilities.
unknown:
  - Terminal exact-head required workflow results after the final checkpoint update.
conflicts: []
first_failure:
  marker: STALE_INCOMPLETE_EXISTING_BRANCH
  evidence: The discovered branch imported a nonexistent signal_control.service and had no tests or task checkpoint; it was reset before implementation.
rejected_hypotheses:
  - Treat a valid signal as execution success.
  - Resolve a real signing secret provider inside BM-04.
  - Map arbitrary payload JSON to arbitrary internal commands.
  - Modify root API, migration, BFF, credential or runtime adapter paths.
changed_paths:
  - ai_platform/portal/signal_control/__init__.py
  - ai_platform/portal/signal_control/authentication.py
  - ai_platform/portal/signal_control/command_mapping.py
  - ai_platform/portal/signal_control/replay.py
  - ai_platform/portal/signal_control/repository.py
  - ai_platform/portal/signal_control/schema.py
  - ai_platform/portal/signal_control/service.py
  - tests/ai_platform/portal/signal_control/__init__.py
  - tests/ai_platform/portal/signal_control/support.py
  - tests/ai_platform/portal/signal_control/test_endpoint_and_authentication.py
  - tests/ai_platform/portal/signal_control/test_mapping_preview_and_safety.py
  - tests/ai_platform/portal/signal_control/test_validation_and_replay.py
  - docs/agents/tasks/FTAI-20260727-portal-bm04-signal-webhook-control.md
validation:
  - command: focused Python compilation
    result: PASS
  - command: focused pytest suite
    result: PASS
    evidence: 39 passed
  - command: exact Ruff 0.15.21 and Ruff format
    result: PASS
    evidence: isolated diagnostic artifact 8669739984 supplied the exact applied patch
  - command: terminal exact-head required repository workflows
    result: PENDING
blockers:
  - Terminal exact-head required workflows must pass before squash merge.
next_action: Validate the final PR 544 exact head, repair only task-caused failures, audit review and changed paths, then squash-merge it.
```
