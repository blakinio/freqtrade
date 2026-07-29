---
task_id: FTAI-20260728-ase-00-ai-strategy-engine-foundation
status: validating
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
updated_at: 2026-07-29T08:46:00+02:00
head: a3640503cd8c46ee5093488fc933237a6a4afe19
branch: agent/ase-00-ai-strategy-engine-foundation
pr: 584
status: validating
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - ai_strategy_engine/docs/IMPLEMENTATION_CHECKPOINT.md
  - ai_strategy_engine/docs/validation-report.md
  - ai_strategy_engine/ARCHITECTURE.md
owned_paths:
  - ai_strategy_engine/
  - ai_platform/research/strategy_engine/
  - tests/ai_platform_integration/test_ase00_vertical_slice.py
  - tests/ai_platform_integration/conftest.py
  - .github/workflows/ai-strategy-engine.yml
  - pyproject.toml
  - docs/agents/tasks/FTAI-20260728-ase-00-ai-strategy-engine-foundation.md
proven:
  - PR 584 is open, draft, unmerged and mergeable at head a3640503cd8c46ee5093488fc933237a6a4afe19.
  - The branch is current with develop 8a9a1fc0ebc8e71ff85a21bae47e7e0e8146c03b with behind_by 0 and ahead_by 259.
  - AI Strategy Engine run 30399931956, AI Platform CI run 30399931877, zizmor run 30399931944 and both runtime smoke runs passed on the current head.
  - Freqtrade CI run 30399932018 failed only in Core tests Python 3.12; pre-commit, documentation, online/live, Python 3.13, Python 3.14 and compatibility jobs passed.
  - Job 90412240770 is recorded completed/failure while Tests with coverage remains in_progress and later steps remain pending; its log endpoint returns BlobNotFound.
  - Previously validated head 18041af549cc0ad9f35deb2f5cd6489fcf7c1ec5 passed all required workflows including Freqtrade CI run 30398395603.
  - Canonical contracts, Feature Registry, Strategy DSL, Leakage Guard, research adapter and the deterministic 12-case shadow vertical slice are present.
  - No live-order path, Browser-to-Freqtrade path or nondeterministic Risk Core bypass is introduced.
derived:
  - The current Freqtrade failure is more consistent with an interrupted or inconsistent Python 3.12 coverage job than a proven code regression.
  - PR 584 cannot return to ready-for-review state until exact-current-head Freqtrade CI passes.
unknown:
  - The exact Python 3.12 coverage failure cause because the completed job exposes no usable logs.
  - Human review outcome and final merge timing for PR 584.
conflicts:
  - The PR body records complete validation on head 18041af549cc0ad9f35deb2f5cd6489fcf7c1ec5, but the current head is a3640503cd8c46ee5093488fc933237a6a4afe19 and its Freqtrade CI is red.
first_failure:
  marker: FREQTRADE_CI_PY312_COVERAGE_INCOMPLETE
  evidence: Run 30399932018 job 90412240770 ended failure while Tests with coverage remains in_progress and later steps pending; log retrieval returns BlobNotFound.
rejected_hypotheses:
  - Treat the green workflow set on head 18041af549cc0ad9f35deb2f5cd6489fcf7c1ec5 as exact-head evidence for a3640503cd8c46ee5093488fc933237a6a4afe19.
  - Mark PR 584 ready while current-head Freqtrade CI is red.
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
  - command: Compare develop to task branch
    result: PASS
    evidence: develop 8a9a1fc0ebc8e71ff85a21bae47e7e0e8146c03b; behind_by 0; ahead_by 259.
  - command: PR 584 live state
    result: PASS
    evidence: Open, draft, unmerged, mergeable; current head a3640503cd8c46ee5093488fc933237a6a4afe19.
  - command: AI Strategy Engine current-head workflow
    result: PASS
    evidence: Run 30399931956 completed successfully.
  - command: AI Platform CI current-head workflow
    result: PASS
    evidence: Run 30399931877 completed successfully.
  - command: GitHub Actions Security Analysis current-head workflow
    result: PASS
    evidence: Run 30399931944 completed successfully.
  - command: Experimental Model Runtime Smoke current-head workflow
    result: PASS
    evidence: Run 30399931940 completed successfully.
  - command: Residual PyTorch Runtime Smoke current-head workflow
    result: PASS
    evidence: Run 30399931822 completed successfully.
  - command: Freqtrade CI current-head workflow
    result: FAIL
    evidence: Run 30399932018 failed in Python 3.12 coverage job 90412240770 with incomplete step state and unavailable logs.
  - command: Previous exact-head required workflow suite
    result: PASS
    evidence: Head 18041af549cc0ad9f35deb2f5cd6489fcf7c1ec5 passed runs 30398395610, 30398395477, 30398395603, 30398395537, 30398395429 and 30398395436.
blockers:
  - Current-head Freqtrade CI must pass before PR 584 is ready for human review.
next_action: Re-run failed jobs for Freqtrade CI run 30399932018 on head a3640503cd8c46ee5093488fc933237a6a4afe19 and inspect only the Python 3.12 coverage job result.
```
