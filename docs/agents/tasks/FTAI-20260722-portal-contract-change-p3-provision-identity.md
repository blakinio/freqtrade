---
task_id: FTAI-20260722-portal-contract-change-p3-provision-identity
status: ready
branch: fix/portal-contracts-p3-provision-identity
base_branch: develop
created: 2026-07-22
updated: 2026-07-22
related_pr: "#117"
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

The implementation head `440640ba50e4697d111e672f6ceab6e6721fb7a5` passed AI Platform CI, full Freqtrade CI/CI Gate, repository pre-commit, documentation build and zizmor. The optional Pre-commit Types update workflow was skipped and is not a failure.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-22T14:18:00+02:00
head: 440640ba50e4697d111e672f6ceab6e6721fb7a5
branch: fix/portal-contracts-p3-provision-identity
pr: "#117"
status: ready
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
  - P2 PR #116 was squash-merged to develop as f7beae36e93cc584c521f6225d0eda43fd4b03d3 before this contract change started.
  - ExecutionAdapter.provision_bot previously received BotSpec while RuntimeStatus requires bot_id and P3 requires one BotInstance to one runtime.
  - BotSpec contains tenant_id but no bot_id; BotInstance contains both and remains the canonical tenant-scoped bot resource.
  - ExecutionAdapter.provision_bot now receives BotInstance plus CorrelationContext and all other protocol methods remain unchanged.
  - No serialized BotSpec, BotInstance or RuntimeStatus v1 field shape or contract_version changed.
  - Focused type-hint regression coverage requires explicit BotInstance provisioning identity.
  - No runtime lifecycle, Docker/Freqtrade integration, public port, raw secret, live-capital, holdout evaluation, Phase 6 or selected_model change was introduced.
  - AI Platform CI run 29916726824 passed on implementation head 440640ba50e4697d111e672f6ceab6e6721fb7a5.
  - Freqtrade CI run 29916726795 and zizmor run 29916726858 passed on implementation head 440640ba50e4697d111e672f6ceab6e6721fb7a5; optional types run 29916726903 was skipped.
derived:
  - P3 can now implement deterministic tenant-scoped one-bot-one-runtime provisioning through the canonical ExecutionAdapter without a side channel.
unknown: []
conflicts: []
first_failure:
  marker: p3-provision-identity-gap
  evidence: P3 preflight proved that the previous provision_bot input lacked bot_id required for truthful RuntimeStatus and deterministic runtime identity.
rejected_hypotheses:
  - Derive bot_id from correlation or request identifiers.
  - Derive bot_id from exchange_connection_ref or mutable model/strategy fields.
  - Add a P3-only side-channel provisioning method.
changed_paths:
  - ai_platform/portal/contracts/execution.py
  - tests/ai_platform/portal/test_execution_contracts.py
  - docs/ai_platform/portal/CONTRACTS_AND_SECURITY_FOUNDATION.md
  - docs/agents/tasks/FTAI-20260722-portal-contract-change-p3-provision-identity.md
validation:
  - command: execution contract compatibility analysis
    result: PASS
    evidence: Gap was isolated to the Python Protocol provisioning argument; no serialized schema migration was required.
  - command: focused execution contract regression test
    result: PASS
    evidence: AI Platform CI run 29916726824 passed the added explicit BotInstance type-hint regression test.
  - command: AI Platform CI
    result: PASS
    evidence: Workflow run 29916726824 completed successfully.
  - command: repository pre-commit and documentation build
    result: PASS
    evidence: Freqtrade CI run 29916726795 completed pre-commit and documentation jobs successfully.
  - command: Freqtrade CI and CI Gate
    result: PASS
    evidence: Freqtrade CI run 29916726795 completed successfully.
  - command: zizmor
    result: PASS
    evidence: GitHub Actions Security Analysis run 29916726858 completed successfully.
  - command: Pre-commit Types update
    result: NOT_RUN
    evidence: Optional workflow run 29916726903 was skipped and is not a failure.
blockers: []
next_action: Review and squash-merge PR #117, then reset the P3 Execution Adapter branch to current develop and resume implementation from the updated canonical contract.
```
