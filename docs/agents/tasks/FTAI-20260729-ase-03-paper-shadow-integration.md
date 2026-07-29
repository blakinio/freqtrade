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
  - ai_strategy_engine/src/strategy_engine/dsl/evaluator.py
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
updated_at: 2026-07-29T23:24:00+02:00
checkpoint_carrier: self
branch: agent/ase-03-paper-shadow-integration
base_head: ff1fe4944149aad9bb8643be69052f935829ed94
implementation_head: f3db100887a75ec46f210739dbd3553acc2127e3
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
  - ai_strategy_engine/src/strategy_engine/dsl/evaluator.py
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
  - Final checkpoint/backlog head 68e2f2c25329ea5843de39a733f8e87b48666493 was behind develop by zero commits and had zero unresolved review threads.
  - AI Platform CI 30488203854, AI Strategy Engine 30488203895 and workflow-security 30488203814 passed on 68e2f2c25329ea5843de39a733f8e87b48666493.
  - Freqtrade CI 30488204274 failed only because Python 3.11 could not parse the PEP 695 type-alias statement imported by the new ASE-03 integration test; 5787 tests passed before collection terminated.
  - Head f3db100887a75ec46f210739dbd3553acc2127e3 replaces only that alias statement with Python 3.11-compatible equivalent syntax and does not change DSL evaluation semantics.
  - The dependency backlog marks all four bounded ASE-03 acceptance bullets complete.
derived:
  - The package is a thin admission and rollback layer over existing simulator/shadow evidence, Risk Core and private dry-run lifecycle contracts rather than a second execution gateway.
  - Successful paper admission proves only private DRY_RUN lifecycle readiness; it is not order submission, production deployment, strategy promotion or live-capital authority.
  - The Python 3.11 repair is a narrow compatibility dependency required for full repository CI, not a scope expansion of ASE-03.
unknown:
  - Exact-head workflow conclusions on f3db100887a75ec46f210739dbd3553acc2127e3.
  - Whether current develop advances before final merge and requires another normal synchronization.
conflicts: []
first_failure:
  marker: ASE03_VALIDATION_REPAIRS
  evidence: Initial validation required mechanical Ruff import/layout repairs; final Freqtrade CI then exposed a Python 3.11 SyntaxError at the imported PEP 695 SnapshotValue alias. The alias was converted to equivalent assignment syntax without changing DSL or admission behavior.
rejected_hypotheses:
  - Implement a second execution gateway, simulator or Risk Core.
  - Call submit_approved_intent or add private order transport.
  - Allow production environment, live mode, exchange credentials or browser-to-Freqtrade access.
  - Treat paper/shadow admission as deployment, promotion, execution or live-capital approval.
  - Change DSL evaluation behavior to repair a Python-version parsing failure.
changed_paths:
  - ai_platform/research/strategy_engine/ase03_integration.py
  - ai_strategy_engine/src/strategy_engine/dsl/evaluator.py
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
  - command: AI Platform CI 30488203854, AI Strategy Engine 30488203895 and Security Analysis 30488203814 on 68e2f2c25329ea5843de39a733f8e87b48666493
    result: PASS
    evidence: Final checkpoint/backlog head passed all dedicated platform, strategy-engine and workflow-security validation.
  - command: Freqtrade CI 30488204274 on 68e2f2c25329ea5843de39a733f8e87b48666493
    result: FAIL
    evidence: Python 3.11 collection reached the imported DSL evaluator and failed on PEP 695 alias syntax; Python 3.12, 3.13 and 3.14 jobs passed, with 5787 Python 3.11 tests passing before the collection error.
  - command: Python 3.11 compatibility repair f3db100887a75ec46f210739dbd3553acc2127e3
    result: APPLIED
    evidence: SnapshotValue now uses semantically equivalent assignment syntax supported by Python 3.11; exact-head GitHub workflows are authoritative for final validation.
known_limitations:
  - Paper means private Freqtrade DRY_RUN lifecycle only; no signal/order submission transport is added.
  - Audit storage is local append-only filesystem evidence for this bounded package, not a production event-store migration.
blockers: []
next_action: Inspect all exact-head workflows on f3db100887a75ec46f210739dbd3553acc2127e3, fix only evidenced failures, synchronize normally if develop moves, confirm zero unresolved review threads, merge PR 748 with expected-head protection after required checks pass, then record the terminal merge checkpoint without enabling live capital.
```
