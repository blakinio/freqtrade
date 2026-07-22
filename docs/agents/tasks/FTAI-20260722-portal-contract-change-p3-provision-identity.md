---
task_id: FTAI-20260722-portal-contract-change-p3-provision-identity
status: active
branch: fix/portal-contracts-p3-provision-identity
base_branch: develop
created: 2026-07-22
updated: 2026-07-22
related_pr: null
owned_paths:
  - ai_platform/portal/contracts/execution.py
  - tests/ai_platform/portal/test_execution_contracts.py
  - docs/ai_platform/portal/CONTRACTS_AND_SECURITY_FOUNDATION.md
  - docs/agents/tasks/FTAI-20260722-portal-contract-change-p3-provision-identity.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/portal/AGENT_EXECUTION_PLAN.md
  - docs/ai_platform/portal/CONTRACTS_AND_SECURITY_FOUNDATION.md
  - docs/agents/tasks/FTAI-20260722-portal-p3-execution-adapter.md
search_first:
  - current develop and merged P1/P2 state
  - exact P3 first incompatible requirement
  - open PRs overlapping shared execution contract files
optional_reads:
  - only P1 execution contract implementation and tests
---

# AI Trading Portal contract change — P3 provisioning identity

## Goal

Make the canonical `ExecutionAdapter.provision_bot` input carry explicit BotInstance identity so P3 can satisfy one-bot-one-runtime provisioning and return a truthful tenant-scoped `RuntimeStatus` without deriving bot identity from correlation metadata or mutable spec fields.

## Deliverables

- change only the Python protocol input of `ExecutionAdapter.provision_bot` from `BotSpec` to `BotInstance`;
- focused protocol type-hint regression test;
- minimal contracts foundation documentation update.

## Non-negotiable boundaries

- Do not change serialized BotSpec/BotInstance/RuntimeStatus field shapes or contract_version.
- Do not remove or rename existing execution methods.
- Do not implement runtime lifecycle, Docker integration or Freqtrade calls in this task.
- Do not add direct browser/Freqtrade integration or raw secret fields.
- Do not alter frozen thresholds, protected final holdout, completed Phase 6 or `selected_model = null`.

## Acceptance criteria

1. `ExecutionAdapter.provision_bot` requires a `BotInstance` plus `CorrelationContext`.
2. Tenant_id and bot_id are therefore explicit before runtime provisioning begins.
3. Existing serialized v1 contracts remain unchanged.
4. Other ExecutionAdapter methods and risk-approved submission boundary remain unchanged.
5. Targeted contract tests, AI Platform CI and repository CI pass.

## Validation

Run focused execution contract tests, compile, Ruff lint/format, then required PR CI.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-22T13:45:00+02:00
head: f7beae36e93cc584c521f6225d0eda43fd4b03d3
branch: fix/portal-contracts-p3-provision-identity
pr: null
status: implementing
context_routes:
  - docs/ai_platform/portal/AGENT_EXECUTION_PLAN.md
  - docs/ai_platform/portal/CONTRACTS_AND_SECURITY_FOUNDATION.md
  - docs/agents/tasks/FTAI-20260722-portal-p3-execution-adapter.md
owned_paths:
  - ai_platform/portal/contracts/execution.py
  - tests/ai_platform/portal/test_execution_contracts.py
  - docs/ai_platform/portal/CONTRACTS_AND_SECURITY_FOUNDATION.md
  - docs/agents/tasks/FTAI-20260722-portal-contract-change-p3-provision-identity.md
proven:
  - ExecutionAdapter.provision_bot currently receives BotSpec but RuntimeStatus requires bot_id.
  - BotSpec contains tenant_id but no bot_id, while BotInstance contains both and remains the canonical tenant-scoped bot resource.
  - P3 architecture requires one BotInstance to one isolated runtime.
derived:
  - Replacing the protocol input type with BotInstance is the smallest explicit-identity change and leaves serialized v1 field contracts unchanged.
unknown: []
conflicts: []
first_failure:
  marker: p3-provision-identity-gap
  evidence: P3 cannot implement canonical provisioning without explicit bot_id in provision_bot input.
rejected_hypotheses:
  - Derive bot_id from correlation or request identifiers.
  - Add a P3-only side-channel provisioning method.
changed_paths:
  - docs/agents/tasks/FTAI-20260722-portal-contract-change-p3-provision-identity.md
validation:
  - command: execution contract compatibility analysis
    result: PASS
    evidence: Gap is isolated to the Python Protocol provisioning argument; no serialized schema migration is required.
blockers: []
next_action: Change ExecutionAdapter.provision_bot to BotInstance, add focused regression coverage, validate, and open a dedicated PR to develop.
```
