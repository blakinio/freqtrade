---
task_id: FTAI-20260728-ase-00-ai-strategy-engine-foundation
status: ready
branch: agent/ase-00-ai-strategy-engine-foundation
base_branch: develop
created: 2026-07-28
updated: 2026-07-28
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
updated_at: 2026-07-28T22:55:00+02:00
head: b1d58d8eeadafa5ce92762812c3f16401e1c17d2
branch: agent/ase-00-ai-strategy-engine-foundation
pr: 584
status: ready
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
  - PR 584 is open, draft, unmerged and mergeable at the completion check.
  - Develop be47cdfd4692ea28281e0a1158cab6c98db38608 was merged normally without force-push and the branch is behind_by 0.
  - Exact-head post-merge validation succeeded on b1d58d8eeadafa5ce92762812c3f16401e1c17d2.
  - AI Strategy Engine run 30397161360 completed successfully.
  - AI Platform CI run 30397161038 completed successfully.
  - Freqtrade CI run 30397162300 completed successfully across the configured matrix.
  - Zizmor run 30397162077 completed successfully.
  - Experimental Model Runtime Smoke run 30397161097 completed successfully.
  - Residual PyTorch Runtime Smoke run 30397162273 completed successfully.
  - The one-shot merge workflow removed itself and is absent from the final PR diff.
  - All PR review threads are resolved and outdated; no human approval or change request is present.
  - The repository adapter, deterministic 12-case vertical slice and permanent read-only workflow are present.
  - The standalone ASE package requires Python 3.12+ while root Freqtrade Python 3.11 collection remains valid.
  - No live-order path, browser-to-Freqtrade path or nondeterministic Risk Core bypass was introduced.
derived:
  - ASE-00 is implementation-complete, synchronized with develop, fully validated and ready for human review.
  - Further Strategy Engine functionality belongs in a separate bounded work package using the canonical contracts delivered here.
unknown:
  - Human review outcome and final merge timing for PR 584.
conflicts: []
first_failure:
  marker: ROOT_PYTEST_IMPORT_AND_PYTHON_BOUNDARY
  evidence: Root CI originally failed because local ASE modules were not on pytest pythonpath and Python 3.11 collected a Python 3.12-only test surface; both boundaries were corrected and exact-head CI passed.
rejected_hypotheses:
  - Treat action_required records from the GITHUB_TOKEN merge push as executed test failures.
  - Downgrade the standalone ASE package from its declared Python 3.12+ boundary.
  - Expose Browser directly to private Freqtrade.
  - Enable live execution as part of ASE-00.
changed_paths:
  - ai_strategy_engine/
  - ai_platform/research/strategy_engine/ase00_adapter.py
  - ai_platform/research/strategy_engine/__init__.py
  - ai_platform/research/__init__.py
  - tests/ai_platform_integration/test_ase00_vertical_slice.py
  - tests/ai_platform_integration/conftest.py
  - pyproject.toml
  - .github/workflows/ai-strategy-engine.yml
  - docs/agents/tasks/FTAI-20260728-ase-00-ai-strategy-engine-foundation.md
validation:
  - command: AI Strategy Engine run 30397161360
    result: PASS
    evidence: Post-merge package tests, Ruff, formatting, mypy, compile, schema, materialization and boundary scans succeeded.
  - command: AI Platform CI run 30397161038
    result: PASS
    evidence: Post-merge platform validation succeeded.
  - command: Freqtrade CI run 30397162300
    result: PASS
    evidence: Post-merge pre-commit, documentation, online/live compatibility, core and configured compatibility matrices succeeded.
  - command: GitHub Actions Security Analysis run 30397162077
    result: PASS
    evidence: Post-merge zizmor workflow succeeded.
  - command: Experimental Model Runtime Smoke run 30397161097
    result: PASS
    evidence: Post-merge experimental runtime smoke succeeded.
  - command: Residual PyTorch Runtime Smoke run 30397162273
    result: PASS
    evidence: Post-merge residual runtime smoke succeeded.
blockers: []
next_action: Human-review PR 584; after approval, merge it normally into develop without bypassing required checks.
```
