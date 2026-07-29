---
task_id: FTAI-20260728-ase-00-ai-strategy-engine-foundation
status: ready_for_review
branch: agent/ase-00-ai-strategy-engine-foundation
base_branch: develop
created: 2026-07-28
updated: 2026-07-29
required_reads:
  - ai_strategy_engine/docs/IMPLEMENTATION_CHECKPOINT.md
search_first:
  - ai_strategy_engine/docs/validation-report.md
  - tests/ai_platform_integration/test_ase00_vertical_slice.py
  - .github/workflows/ai-strategy-engine.yml
optional_reads:
  - ai_strategy_engine/ARCHITECTURE.md
  - ai_strategy_engine/TASKS.md
owned_paths:
  - ai_strategy_engine/
  - ai_platform/research/strategy_engine/
  - tests/ai_platform_integration/test_ase00_vertical_slice.py
  - tests/ai_platform_integration/conftest.py
  - .github/workflows/ai-strategy-engine.yml
  - pyproject.toml
  - docs/agents/tasks/FTAI-20260728-ase-00-ai-strategy-engine-foundation.md
---

# ASE-00 AI Strategy Engine foundation

## Goal

Deliver the research-only AI Strategy Engine foundation and one deterministic synthetic shadow vertical slice without introducing a live-order path or bypassing deterministic risk controls.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-29T09:09:00+02:00
validated_head: e1031065844c4238b3b03033b891698303e5a1c2
checkpoint_carrier: self
branch: agent/ase-00-ai-strategy-engine-foundation
base_head: 8a9a1fc0ebc8e71ff85a21bae47e7e0e8146c03b
pr: 584
status: ready_for_review
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - ai_strategy_engine/ARCHITECTURE.md
  - ai_strategy_engine/docs/IMPLEMENTATION_CHECKPOINT.md
  - ai_strategy_engine/docs/validation-report.md
  - docs/ai_platform/ROADMAP.md
owned_paths:
  - ai_strategy_engine/
  - ai_platform/research/strategy_engine/
  - tests/ai_platform_integration/test_ase00_vertical_slice.py
  - tests/ai_platform_integration/conftest.py
  - .github/workflows/ai-strategy-engine.yml
  - pyproject.toml
  - docs/agents/tasks/FTAI-20260728-ase-00-ai-strategy-engine-foundation.md
proven:
  - PR 584 is open, unmerged and mergeable.
  - Current develop 8a9a1fc0ebc8e71ff85a21bae47e7e0e8146c03b was merged normally into the task branch through synchronization PR 668; no force-push or branch-protection bypass was used.
  - The synchronization changed four unrelated portal governance documents and did not alter ASE runtime behavior.
  - Exact validated head e1031065844c4238b3b03033b891698303e5a1c2 passed every required workflow.
  - Freqtrade CI run 30429457265 passed the complete configured matrix, including Core tests Ubuntu 24.04 Python 3.12 coverage job 90503266663.
  - The earlier Freqtrade CI run 30399932018 failed only in Python 3.12 coverage job 90412240770; its log endpoint returned BlobNotFound and exposed no concrete test failure.
  - The earlier failure did not reproduce on the synchronized exact head, so no speculative code correction was made.
  - Canonical contracts, Feature Registry, Strategy DSL, Leakage Guard, research adapter and the deterministic twelve-case shadow vertical slice are present.
  - No live-order path, Browser-to-Freqtrade path, exchange credential path or nondeterministic Risk Core bypass is introduced.
derived:
  - The earlier Python 3.12 result was an interrupted or otherwise non-reproducible workflow failure, not a demonstrated ASE-00 regression.
  - ASE-00 is implementation-complete and may be merged only after the required human approval.
unknown:
  - The exact internal cause of run 30399932018 because GitHub no longer exposes a usable job log.
  - Human review outcome and merge timing for PR 584.
conflicts: []
first_failure:
  marker: FREQTRADE_CI_PY312_COVERAGE_NON_REPRODUCIBLE
  evidence: Run 30399932018 job 90412240770 ended failure with unavailable logs; exact-head run 30429457265 job 90503266663 completed the same coverage step successfully.
rejected_hypotheses:
  - Modify ASE code without a reproducible failing test.
  - Treat a previously green head as evidence for a different current head.
  - Bypass required checks or owner approval.
  - Expose Browser directly to private Freqtrade.
  - Enable live execution as part of ASE-00.
changed_paths:
  - ai_strategy_engine/
  - ai_platform/research/strategy_engine/ase00_adapter.py
  - tests/ai_platform_integration/test_ase00_vertical_slice.py
  - tests/ai_platform_integration/conftest.py
  - pyproject.toml
  - .github/workflows/ai-strategy-engine.yml
  - docs/agents/tasks/FTAI-20260728-ase-00-ai-strategy-engine-foundation.md
validation:
  - command: AI Strategy Engine exact-head workflow
    result: PASS
    evidence: Run 30429457180 completed successfully on e1031065844c4238b3b03033b891698303e5a1c2.
  - command: AI Platform CI exact-head workflow
    result: PASS
    evidence: Run 30429457184 completed successfully on e1031065844c4238b3b03033b891698303e5a1c2.
  - command: Freqtrade CI exact-head workflow
    result: PASS
    evidence: Run 30429457265 completed successfully on e1031065844c4238b3b03033b891698303e5a1c2; Python 3.12 coverage job 90503266663 passed.
  - command: GitHub Actions Security Analysis exact-head workflow
    result: PASS
    evidence: Run 30429457202 completed successfully on e1031065844c4238b3b03033b891698303e5a1c2.
  - command: Experimental Model Runtime Smoke exact-head workflow
    result: PASS
    evidence: Run 30429457486 completed successfully on e1031065844c4238b3b03033b891698303e5a1c2.
  - command: Residual PyTorch Runtime Smoke exact-head workflow
    result: PASS
    evidence: Run 30429457374 completed successfully on e1031065844c4238b3b03033b891698303e5a1c2.
known_limitations:
  - ASE-00 remains research and shadow only.
  - The protected final holdout remains unavailable for iterative work.
  - No TradingView strategy laboratory, experiment backtest API or laboratory UI is delivered by ASE-00.
missing_functions:
  - FTAI-20260729-ase-01-tradingview-strategy-lab has not started because its required base is develop after approved ASE-00 merge.
blockers:
  - A human owner must review and approve PR 584 before merge under the repository process.
next_action: Human-review and approve PR 584; merge it normally into develop after exact-head required checks remain green, then create FTAI-20260729-ase-01-tradingview-strategy-lab from that exact develop head.
```
