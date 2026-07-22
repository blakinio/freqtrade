---
task_id: FTAI-20260722-portal-p3-execution-adapter
status: active
branch: feat/portal-p3-execution-adapter
base_branch: develop
created: 2026-07-22
updated: 2026-07-22
related_pr: null
owned_paths:
  - ai_platform/portal/execution/
  - tests/ai_platform/portal/execution/
  - docs/ai_platform/portal/EXECUTION_ADAPTER.md
  - docs/agents/tasks/FTAI-20260722-portal-p3-execution-adapter.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/SYSTEM_ARCHITECTURE.md
  - docs/ai_platform/portal/SECURITY_ARCHITECTURE.md
  - docs/ai_platform/portal/CONTRACTS_AND_SECURITY_FOUNDATION.md
  - docs/ai_platform/portal/AGENT_EXECUTION_PLAN.md
  - ai_platform/portal/contracts/execution.py
search_first:
  - current develop and merged contract-change PR #117
  - open PRs overlapping execution ownership
  - existing Freqtrade Docker/runtime configuration conventions
optional_reads:
  - only execution/runtime implementation-adjacent files
---

# AI Trading Portal P3 — Execution Adapter

## Goal

Implement a dry-run-only private Freqtrade runtime lifecycle behind the canonical `ExecutionAdapter`, with one tenant-scoped BotInstance mapped to one isolated runtime, explicit readiness/health, deterministic failure states and no public runtime port.

## Deliverables

- `FreqtradeExecutionAdapter` under `ai_platform/portal/execution/`;
- deterministic one-bot-one-runtime identity and isolated runtime workspace;
- private Docker runtime driver abstraction with no host port publishing;
- dry-run-only generated runtime configuration and replaceable artifact/config resolvers;
- provision/start/pause/stop/status/health behavior;
- fail-closed unsupported trade submission/query behavior until later risk/terminal integration;
- targeted lifecycle, isolation, configuration and failure tests;
- implementation documentation in `docs/ai_platform/portal/EXECUTION_ADAPTER.md`.

## Non-negotiable boundaries

- Do not modify upstream `freqtrade/` core.
- Do not publish Freqtrade REST or WebSocket ports.
- Do not expose Freqtrade credentials, runtime hostnames or exchange secrets to browser-facing contracts.
- Accept only `dry_run` execution mode in P3; simulator mode belongs to P10a and live capital is forbidden.
- Do not retrieve or persist production exchange credentials in P3.
- One BotInstance maps to one deterministic isolated runtime identity.
- Unsupported trade submission/query behavior must fail closed rather than bypass risk or fabricate evidence.
- Do not change frozen thresholds `0.006/-0.009`, access protected holdout `20260801-20260930`, reopen Phase 6, or change `selected_model = null`.

## Acceptance criteria

1. Provisioning receives explicit tenant_id and bot_id through BotInstance and deterministically maps one bot to one runtime identity.
2. Generated runtime config forces `dry_run: true`, disables API server exposure and contains no raw exchange credentials.
3. Docker runtime creation publishes no host ports and mounts only the bot-specific runtime workspace.
4. Start, pause, stop and status operations are idempotent and tenant-scoped.
5. Health distinguishes healthy/running, paused/stopped and deterministic driver failures.
6. Correlation context is carried into private runtime labels/metadata without exposing secrets.
7. Unsupported order/trade methods fail closed until a risk-approved private transport is implemented.
8. Targeted tests, AI Platform tests, compile, Ruff, pre-commit and required repository CI pass.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-22T14:40:00+02:00
head: d6b0dbe47dc929ff400140d2c492a829b9fb5717
branch: feat/portal-p3-execution-adapter
pr: null
status: implementing
context_routes:
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/SYSTEM_ARCHITECTURE.md
  - docs/ai_platform/portal/SECURITY_ARCHITECTURE.md
  - docs/ai_platform/portal/CONTRACTS_AND_SECURITY_FOUNDATION.md
  - docs/ai_platform/portal/AGENT_EXECUTION_PLAN.md
owned_paths:
  - ai_platform/portal/execution/
  - tests/ai_platform/portal/execution/
  - docs/ai_platform/portal/EXECUTION_ADAPTER.md
  - docs/agents/tasks/FTAI-20260722-portal-p3-execution-adapter.md
proven:
  - PR #117 was squash-merged to develop as d6b0dbe47dc929ff400140d2c492a829b9fb5717 after final-head AI Platform CI, Freqtrade CI and zizmor passed.
  - Current develop is identical to d6b0dbe47dc929ff400140d2c492a829b9fb5717.
  - P3 branch was force-reset to that exact develop commit before implementation resumed.
  - Canonical ExecutionAdapter.provision_bot now receives BotInstance plus CorrelationContext, making tenant_id and bot_id explicit.
derived:
  - P3 can implement one-bot-one-runtime identity without private side channels or deriving identity from correlation metadata.
unknown: []
conflicts: []
first_failure:
  marker: provision-identity-contract-gap
  evidence: Initial P3 preflight found that provision_bot accepted BotSpec without bot_id; dedicated PR #117 fixed this before runtime implementation.
rejected_hypotheses:
  - Derive bot_id from correlation_id or request_id.
  - Expose Freqtrade API directly to browser-facing code.
  - Enable live-capital runtime mode in P3.
changed_paths:
  - docs/agents/tasks/FTAI-20260722-portal-p3-execution-adapter.md
validation:
  - command: resume preflight after PR #117
    result: PASS
    evidence: PR #117 merged and develop reverified identical to d6b0dbe47dc929ff400140d2c492a829b9fb5717 before branch reset.
blockers: []
next_action: Implement the dry-run-only private ExecutionAdapter lifecycle and targeted tests without public ports or secret retrieval.
```
