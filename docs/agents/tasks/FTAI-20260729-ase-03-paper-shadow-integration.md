---
task_id: FTAI-20260729-ase-03-paper-shadow-integration
status: validating
branch: agent/ase-03-paper-shadow-integration
base_branch: develop
created: 2026-07-29
updated: 2026-07-29
related_pr: 748
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
updated_at: 2026-07-29T22:20:00+02:00
checkpoint_carrier: self
branch: agent/ase-03-paper-shadow-integration
base_head: ff1fe4944149aad9bb8643be69052f935829ed94
implementation_head: c15bfae799bdfa246d76c277ba2aa2c26a03f832
pr: 748
status: validating
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - ai_strategy_engine/ARCHITECTURE.md
  - ai_strategy_engine/TASKS.md
  - docs/ai_platform/ASE_03_PAPER_SHADOW_INTEGRATION.md
owned_paths:
  - ai_platform/research/strategy_engine/ase03_integration.py
  - tests/ai_platform_integration/test_ase03_paper_shadow_integration.py
  - docs/ai_platform/ASE_03_PAPER_SHADOW_INTEGRATION.md
  - docs/agents/tasks/FTAI-20260729-ase-03-paper-shadow-integration.md
  - ai_strategy_engine/TASKS.md
proven:
  - The merged ASE-00 shadow engine already uses the canonical Portal Risk Core and produces no-order evidence.
  - The merged P3 FreqtradeExecutionAdapter accepts only DRY_RUN, forces private safe configuration and leaves submit_approved_intent fail-closed.
  - ASE-03 compares simulator and shadow identity, data/config/code hashes, feature records, signal, risk outcome and no-order boundary before admission.
  - Simulator, shadow and parity evidence are persisted immutably with canonical hashes; audit records are append-only and reject idempotency conflicts.
  - Shadow admission never calls the execution adapter.
  - Paper admission is restricted to TEST or STAGING DRY_RUN bots and calls only provision, start and health operations.
  - Paper rollback stops the private dry-run runtime and verifies observed state; shadow rollback records an audited no-runtime operation.
  - submit_approved_intent, PI-08 order transport, production, live mode, exchange credentials and browser-to-Freqtrade access remain absent.
  - Implementation head c15bfae799bdfa246d76c277ba2aa2c26a03f832 passed AI Platform CI 30487876423 and AI Strategy Engine 30487876429, including tests, Ruff, mypy, compile, deterministic E2E, schema checks and architecture-boundary scan.
  - Workflow-security run 30487876697 passed on the implementation head.
  - The dependency backlog marks all four bounded ASE-03 acceptance bullets complete.
derived:
  - The package is a thin admission and rollback layer over existing simulator/shadow evidence, Risk Core and private dry-run lifecycle contracts rather than a second execution gateway.
  - Successful paper admission proves only private DRY_RUN lifecycle readiness; it is not order submission, production deployment, strategy promotion or live-capital authority.
unknown:
  - Terminal exact-head Freqtrade CI and all final workflow conclusions after the checkpoint/backlog update.
  - Whether current develop advances before final merge and requires another normal synchronization.
conflicts: []
first_failure:
  marker: ASE03_RUFF_IMPORT_LAYOUT
  evidence: Initial validation found an unused canonical_sha256 import, a long error line and then exact Ruff I001 grouping/blank-line requirements; tests remained green and the mechanical layout was repaired without changing admission semantics.
rejected_hypotheses:
  - Implement a second execution gateway, simulator or Risk Core.
  - Call submit_approved_intent or add private order transport.
  - Allow production environment, live mode, exchange credentials or browser-to-Freqtrade access.
  - Treat paper/shadow admission as deployment, promotion, execution or live-capital approval.
changed_paths:
  - ai_platform/research/strategy_engine/ase03_integration.py
  - tests/ai_platform_integration/test_ase03_paper_shadow_integration.py
  - docs/ai_platform/ASE_03_PAPER_SHADOW_INTEGRATION.md
  - docs/agents/tasks/FTAI-20260729-ase-03-paper-shadow-integration.md
  - ai_strategy_engine/TASKS.md
validation:
  - command: AI Platform CI 30487876423 on c15bfae799bdfa246d76c277ba2aa2c26a03f832
    result: PASS
    evidence: AI Platform tests, compile, Ruff, format, codespell and JSON validations succeeded.
  - command: AI Strategy Engine 30487876429 on c15bfae799bdfa246d76c277ba2aa2c26a03f832
    result: PASS
    evidence: Package and Portal tests, Ruff, mypy, compile, deterministic E2E, schema/materialization checks and prohibited-boundary scan succeeded.
  - command: GitHub Actions Security Analysis 30487876697 on c15bfae799bdfa246d76c277ba2aa2c26a03f832
    result: PASS
    evidence: Workflow-security analysis succeeded.
  - command: Final exact-head workflow suite after checkpoint and backlog update
    result: REQUIRED
    evidence: Validate all required workflows on the final head, synchronize normally if develop moved, confirm zero review threads and merge with expected-head protection.
known_limitations:
  - Paper means private Freqtrade DRY_RUN lifecycle only; no signal/order submission transport is added.
  - Audit storage is local append-only filesystem evidence for this bounded package, not a production event-store migration.
blockers: []
next_action: Complete all required exact-head workflows on the final checkpoint/backlog head, synchronize normally with current develop if needed, confirm zero unresolved review threads, merge PR 748 with expected-head protection, then record the terminal merge checkpoint and select the next task from authoritative ai_strategy_engine/TASKS.md without enabling live capital.
```
