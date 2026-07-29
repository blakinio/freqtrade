---
task_id: FTAI-20260729-ase-03-paper-shadow-integration
status: implementing
branch: agent/ase-03-paper-shadow-integration
base_branch: develop
created: 2026-07-29
updated: 2026-07-29
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - ai_strategy_engine/ARCHITECTURE.md
  - ai_strategy_engine/TASKS.md
  - docs/ai_platform/ASE_03_PAPER_SHADOW_INTEGRATION.md
search_first:
  - ai_platform/research/strategy_engine/ase03_integration.py
  - ai_platform/research/strategy_engine/ase00_adapter.py
  - ai_platform/portal/risk/service.py
  - ai_platform/portal/execution/adapter.py
  - tests/ai_platform_integration/test_ase03_paper_shadow_integration.py
owned_paths:
  - ai_platform/research/strategy_engine/ase03_integration.py
  - tests/ai_platform_integration/test_ase03_paper_shadow_integration.py
  - docs/ai_platform/ASE_03_PAPER_SHADOW_INTEGRATION.md
  - docs/agents/tasks/FTAI-20260729-ase-03-paper-shadow-integration.md
  - ai_strategy_engine/TASKS.md
---

# ASE-03 paper/shadow integration

## Goal

Integrate deterministic simulator/shadow parity, the existing Portal Risk Core, and the private
Freqtrade dry-run adapter behind append-only admission/rollback evidence without implementing
order submission or live-capital authority.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-29T22:05:00+02:00
checkpoint_carrier: self
branch: agent/ase-03-paper-shadow-integration
base_head: e6ff45aa810b3982f79b7167450ec38a50b1b4f4
pr: null
status: implementing
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - ai_strategy_engine/ARCHITECTURE.md
  - docs/ai_platform/ASE_03_PAPER_SHADOW_INTEGRATION.md
proven:
  - The merged ASE-00 shadow engine already uses the canonical Portal Risk Core and produces no-order evidence.
  - The merged P3 FreqtradeExecutionAdapter accepts only DRY_RUN, forces private safe configuration and leaves submit_approved_intent fail-closed.
  - The new ASE-03 controller compares simulator and shadow identity, inputs, feature records, signal, risk outcome and no-order boundary before runtime admission.
  - Shadow admission never calls the execution adapter.
  - Paper admission is restricted to TEST or STAGING DRY_RUN bots and calls only provision, start and health operations.
  - Append-only evidence and admission/rollback records use canonical hashes and idempotency conflict detection.
  - Rollback stops the dry-run runtime or records an audited shadow no-op; submission is never invoked.
derived:
  - This package completes the safe integration contract but does not authorize PI-08, production environment, exchange credentials or live capital.
unknown:
  - Exact-head package, AI Platform, Freqtrade and security workflow conclusions.
conflicts: []
first_failure: null
rejected_hypotheses:
  - Implement a second execution gateway or Risk Core.
  - Call submit_approved_intent or add private order transport.
  - Allow production environment, live mode or browser-to-Freqtrade access.
changed_paths:
  - ai_platform/research/strategy_engine/ase03_integration.py
  - tests/ai_platform_integration/test_ase03_paper_shadow_integration.py
  - docs/ai_platform/ASE_03_PAPER_SHADOW_INTEGRATION.md
  - docs/agents/tasks/FTAI-20260729-ase-03-paper-shadow-integration.md
validation:
  - command: Exact-head workflow suite
    result: REQUIRED
    evidence: Open PR after backlog update, synchronize with develop and fix only evidenced failures.
known_limitations:
  - Paper means private Freqtrade DRY_RUN lifecycle only; no signal/order submission transport is added.
  - Audit storage is local append-only filesystem evidence for this bounded package, not a production event-store migration.
blockers: []
next_action: Update ASE-03 backlog state, open the PR, synchronize with current develop and inspect exact-head CI for deterministic failures.
```
