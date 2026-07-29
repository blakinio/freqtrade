---
task_id: FTAI-20260728-ase-00-ai-strategy-engine-foundation
status: ready_for_merge
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
updated_at: 2026-07-29T11:36:00+02:00
checkpoint_carrier: self
validated_parent_head: c01924ca7d027020adc0f196e2f6ae32d2ba3b76
branch: agent/ase-00-ai-strategy-engine-foundation
base_head: 7f4f99506e3b240b250808ac930b200054b23eb0
pr: 584
status: ready_for_merge
exact_head_resolution: Resolve checkpoint_carrier from the current PR 584 head; required GitHub checks and the PR body attached to that commit are authoritative.
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
  - PR 584 is open, ready for review and unmerged.
  - Develop 7f4f99506e3b240b250808ac930b200054b23eb0 was synchronized normally through PR 677 as merge commit c01924ca7d027020adc0f196e2f6ae32d2ba3b76; no force-push or branch-protection bypass was used.
  - The incoming BM-09 closure changed Portal E2E, workflow and documentation paths only; it did not modify ai_strategy_engine, the ASE research adapter, ASE integration tests or the ASE workflow.
  - Exact head b09fd4720b095c319b708c8f2dec882ec1e197c4 passed all required workflows, including Freqtrade CI run 30436797976 and Python 3.12 coverage job 90527141714.
  - The earlier Freqtrade CI run 30399932018 failed only in Python 3.12 coverage job 90412240770; its log endpoint returned BlobNotFound and exposed no concrete test failure.
  - The historical Python 3.12 failure repeatedly did not reproduce, so no speculative code correction was made.
  - Canonical contracts, Feature Registry, Strategy DSL, Leakage Guard, research adapter and the deterministic twelve-case shadow vertical slice are present.
  - No live-order path, Browser-to-Freqtrade path, exchange credential path or nondeterministic Risk Core bypass is introduced by ASE-00.
  - Owner authorization for autonomous completion and a normal merge after green exact-head checks is recorded on PR 584.
derived:
  - The earlier Python 3.12 result was interrupted or otherwise non-reproducible rather than a demonstrated ASE-00 regression.
  - ASE-00 is implementation-complete and ready for normal merge when checkpoint_carrier checks are green.
unknown:
  - The exact internal cause of run 30399932018 because GitHub no longer exposes a usable job log.
  - The final merge commit SHA until PR 584 is merged.
conflicts: []
first_failure:
  marker: FREQTRADE_CI_PY312_COVERAGE_NON_REPRODUCIBLE
  evidence: Run 30399932018 job 90412240770 ended failure with unavailable logs; exact-head run 30436797976 job 90527141714 completed Tests with coverage successfully.
rejected_hypotheses:
  - Modify ASE code without a reproducible failing test.
  - Treat a previously green head as evidence for a different current head.
  - Bypass required checks or branch protections.
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
    evidence: Head b09fd4720b095c319b708c8f2dec882ec1e197c4 passed AI Strategy Engine 30436797929, AI Platform CI 30436797970, Freqtrade CI 30436797976, zizmor 30436797926, Experimental Model Runtime Smoke 30436798009 and Residual PyTorch Runtime Smoke 30436797912; Python 3.12 coverage job 90527141714 passed.
  - command: Compare develop to synchronized parent
    result: PASS
    evidence: Develop 7f4f99506e3b240b250808ac930b200054b23eb0 was merged normally into synchronized parent c01924ca7d027020adc0f196e2f6ae32d2ba3b76 through PR 677; behind_by 0 before checkpoint update.
  - command: Final checkpoint-carrier workflow suite
    result: REQUIRED
    evidence: All required GitHub checks attached to the current PR head must be green before normal merge; exact run IDs belong in the PR body without another repository commit.
known_limitations:
  - ASE-00 remains research and shadow only.
  - The protected final holdout remains unavailable for iterative work.
  - No TradingView strategy laboratory, experiment backtest API or laboratory UI is delivered by ASE-00.
missing_functions:
  - FTAI-20260729-ase-01-tradingview-strategy-lab starts only from the exact develop head produced by the approved ASE-00 merge.
blockers:
  - Current checkpoint-carrier required checks must pass before PR 584 is merged.
next_action: After checkpoint-carrier checks pass, merge PR 584 normally into develop; from the resulting exact develop head create branch agent/ase-01-tradingview-strategy-lab and task checkpoint docs/agents/tasks/FTAI-20260729-ase-01-tradingview-strategy-lab.md.
```
