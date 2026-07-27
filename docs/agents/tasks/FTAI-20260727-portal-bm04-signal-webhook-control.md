---
task_id: FTAI-20260727-portal-bm04-signal-webhook-control
status: validating
branch: feat/portal-bm04-signal-webhook-control
base_branch: develop
created: 2026-07-27
updated: 2026-07-27
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

The package does not resolve a secret provider, serialize a secret, log a secret, call an exchange or Freqtrade, submit a BM-03 command, place/cancel an order, mutate runtime/position state, activate PI-08 or authorize live capital. `execution_performed` is structurally fixed to false.

## Validation

- `python -m compileall ai_platform/portal/signal_control tests/ai_platform/portal/signal_control` — pass in the isolated focused workspace.
- `pytest -q tests/ai_platform/portal/signal_control` — 39 passed in the isolated focused workspace.
- Exact-head repository Ruff, formatting, typing, AI Platform CI, Freqtrade CI/final gate and security analysis are pending the PR head.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-27T23:40:00+02:00
head: 88f65cd937c4ae3e44b1db01c979039cc901ae93
branch: feat/portal-bm04-signal-webhook-control
pr: null
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
  - The stale pre-existing BM-04 branch contained only seven incomplete source commits, imported a missing service module and had no tests/task checkpoint.
  - The canonical branch was reset to current develop before the complete bounded implementation was published.
  - Focused compile and 39 focused tests pass in the isolated workspace.
  - The package contains no API route, migration, BFF change, provider implementation or execution adapter call.
derived:
  - Shared API registration and durable database migration remain an integration-owner responsibility.
unknown:
  - Exact-head repository CI and security results.
conflicts: []
first_failure:
  marker: STALE_INCOMPLETE_EXISTING_BRANCH
  evidence: The discovered branch was behind current develop and imported a nonexistent signal_control.service without tests or a task checkpoint; it was safely reset before implementation.
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
  - command: exact-head required repository workflows
    result: NOT_RUN
blockers:
  - Exact-head required repository workflows must pass before squash merge.
next_action: Open the dedicated BM-04 PR, validate the exact head with all required workflows, repair only task-caused failures, then squash-merge it.
```
