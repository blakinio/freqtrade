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
updated_at: 2026-07-29T09:38:00+02:00
checkpoint_carrier: self
validated_parent_head: c3f6e3a5ae4f78fc7cc8daf3efcdcdb98d3e9e7f
branch: agent/ase-00-ai-strategy-engine-foundation
base_head: 530f61caf9d5d4644068a93baa0b7a09298f24c6
pr: 584
status: ready_for_review
exact_head_resolution: Resolve checkpoint_carrier from the current PR 584 head; required GitHub checks attached to that commit are authoritative.
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
  - Develop 530f61caf9d5d4644068a93baa0b7a09298f24c6 was synchronized normally through PR 671; no force-push or branch-protection bypass was used.
  - The incoming PI-08 package is private dry-run only and changes Portal execution-submission paths, not ASE Strategy Engine runtime paths.
  - The immediately preceding exact head e9a2a0f379a66b9b8f683c1297dd0f5c5e710b9d passed all required workflows, including Freqtrade CI run 30430720720 and Python 3.12 coverage job 90507285130.
  - The synchronized parent c3f6e3a5ae4f78fc7cc8daf3efcdcdb98d3e9e7f passed AI Strategy Engine run 30432022192, AI Platform CI run 30432021188, zizmor run 30432020624 and both runtime smoke workflows before this final checkpoint commit superseded its queued Freqtrade run.
  - The earlier Freqtrade CI run 30399932018 failed only in Python 3.12 coverage job 90412240770; its log endpoint returned BlobNotFound and exposed no concrete test failure.
  - That failure was not reproduced on later exact heads, so no speculative code correction was made.
  - Canonical contracts, Feature Registry, Strategy DSL, Leakage Guard, research adapter and the deterministic twelve-case shadow vertical slice are present.
  - No live-order path, Browser-to-Freqtrade path, exchange credential path or nondeterministic Risk Core bypass is introduced by ASE-00.
derived:
  - The earlier Python 3.12 result was interrupted or otherwise non-reproducible rather than a demonstrated ASE-00 regression.
  - ASE-00 is implementation-complete and may be merged only after required human approval and green checks on checkpoint_carrier.
unknown:
  - The exact internal cause of run 30399932018 because GitHub no longer exposes a usable job log.
  - Human review outcome and merge timing for PR 584.
conflicts: []
first_failure:
  marker: FREQTRADE_CI_PY312_COVERAGE_NON_REPRODUCIBLE
  evidence: Run 30399932018 job 90412240770 ended failure with unavailable logs; later exact-head Python 3.12 coverage jobs 90503266663 and 90507285130 passed.
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
  - command: Previous exact-head required workflow suite
    result: PASS
    evidence: Head e9a2a0f379a66b9b8f683c1297dd0f5c5e710b9d passed AI Strategy Engine 30430720730, AI Platform CI 30430720686, Freqtrade CI 30430720720, zizmor 30430720728, Experimental Model Runtime Smoke 30430721195 and Residual PyTorch Runtime Smoke 30430720689.
  - command: Current synchronized parent non-Freqtrade workflows
    result: PASS
    evidence: Head c3f6e3a5ae4f78fc7cc8daf3efcdcdb98d3e9e7f passed runs 30432022192, 30432021188, 30432020624, 30432020119 and 30432019969.
  - command: Final checkpoint-carrier workflow suite
    result: REQUIRED
    evidence: All required GitHub checks attached to the current PR head must be green before merge; their exact run IDs are recorded in the PR body without creating another commit.
known_limitations:
  - ASE-00 remains research and shadow only.
  - The protected final holdout remains unavailable for iterative work.
  - No TradingView strategy laboratory, experiment backtest API or laboratory UI is delivered by ASE-00.
missing_functions:
  - FTAI-20260729-ase-01-tradingview-strategy-lab has not started because its required base is develop after approved ASE-00 merge.
blockers:
  - A human owner must review and approve PR 584 before merge under the repository process.
next_action: Human-review and approve PR 584 after checkpoint-carrier checks are green; merge it normally into develop, then create FTAI-20260729-ase-01-tradingview-strategy-lab from that exact develop head.
```
