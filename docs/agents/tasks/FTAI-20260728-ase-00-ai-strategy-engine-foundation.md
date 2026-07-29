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
updated_at: 2026-07-29T10:45:00+02:00
checkpoint_carrier: self
validated_parent_head: ecd53f0a6b13806cfb0d91a3999008febfe106bf
branch: agent/ase-00-ai-strategy-engine-foundation
base_head: ef0550744104f4c82ef3f106181f14442f9b82af
pr: 584
status: ready_for_review
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
  - PR 584 is open, draft and unmerged.
  - Develop ef0550744104f4c82ef3f106181f14442f9b82af was synchronized normally through PR 674 as merge commit ecd53f0a6b13806cfb0d91a3999008febfe106bf; no force-push or branch-protection bypass was used.
  - The incoming BM-07 package changed Portal command-activation paths and did not modify ai_strategy_engine, the ASE research adapter, ASE integration tests or the ASE workflow.
  - Exact head eaf1284ab929456d31c0b6ca4854cf5e274fb68c passed all required workflows, including Freqtrade CI run 30434608732 and Python 3.12 coverage job 90520302620.
  - The earlier Freqtrade CI run 30399932018 failed only in Python 3.12 coverage job 90412240770; its log endpoint returned BlobNotFound and exposed no concrete test failure.
  - The historical Python 3.12 failure has repeatedly not reproduced, so no speculative code correction was made.
  - Canonical contracts, Feature Registry, Strategy DSL, Leakage Guard, research adapter and the deterministic twelve-case shadow vertical slice are present.
  - No live-order path, Browser-to-Freqtrade path, exchange credential path or nondeterministic Risk Core bypass is introduced by ASE-00.
derived:
  - The earlier Python 3.12 result was interrupted or otherwise non-reproducible rather than a demonstrated ASE-00 regression.
  - ASE-00 is implementation-complete and may be merged only after required human approval and green checks on checkpoint_carrier.
unknown:
  - The exact internal cause of run 30399932018 because GitHub no longer exposes a usable job log.
  - Human review outcome and merge timing for PR 584.
conflicts:
  - The PR body records historical validation data; replace it with checkpoint_carrier evidence after exact-head checks finish without creating another repository commit.
first_failure:
  marker: FREQTRADE_CI_PY312_COVERAGE_NON_REPRODUCIBLE
  evidence: Run 30399932018 job 90412240770 ended failure with unavailable logs; exact-head run 30434608732 job 90520302620 completed Tests with coverage successfully.
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
    evidence: Head eaf1284ab929456d31c0b6ca4854cf5e274fb68c passed AI Strategy Engine 30434608634, AI Platform CI 30434608635, Freqtrade CI 30434608732, zizmor 30434608681, Experimental Model Runtime Smoke 30434608692 and Residual PyTorch Runtime Smoke 30434608649; Python 3.12 coverage job 90520302620 passed.
  - command: Compare develop to synchronized parent
    result: PASS
    evidence: Develop ef0550744104f4c82ef3f106181f14442f9b82af was merged normally into synchronized parent ecd53f0a6b13806cfb0d91a3999008febfe106bf through PR 674.
  - command: Final checkpoint-carrier workflow suite
    result: REQUIRED
    evidence: All required GitHub checks attached to the current PR head must be green before human review or merge; exact run IDs belong in the PR body without another repository commit.
known_limitations:
  - ASE-00 remains research and shadow only.
  - The protected final holdout remains unavailable for iterative work.
  - No TradingView strategy laboratory, experiment backtest API or laboratory UI is delivered by ASE-00.
missing_functions:
  - FTAI-20260729-ase-01-tradingview-strategy-lab has not started because its required base is develop after approved ASE-00 merge.
blockers:
  - Current checkpoint-carrier required checks must pass before PR 584 is ready for human review.
  - A human owner must review and approve PR 584 before merge under the repository process.
next_action: Human-review and approve PR 584 after checkpoint-carrier checks are green; merge it normally into develop, then create FTAI-20260729-ase-01-tradingview-strategy-lab from that exact develop head.
```
