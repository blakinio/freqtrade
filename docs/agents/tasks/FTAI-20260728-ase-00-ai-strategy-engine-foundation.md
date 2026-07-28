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
updated_at: 2026-07-28T22:04:00+02:00
head: ab81b3476157e1f2c6f4b8e83490f5ae9a462d86
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
  - Exact-head validation succeeded on ab81b3476157e1f2c6f4b8e83490f5ae9a462d86.
  - AI Strategy Engine run 30392791167 completed successfully.
  - AI Platform CI run 30392791126 completed successfully.
  - Freqtrade CI run 30392791151 completed successfully across the configured matrix.
  - Zizmor run 30392791332 completed successfully.
  - Experimental Model Runtime Smoke run 30392791181 completed successfully.
  - Residual PyTorch Runtime Smoke run 30392791096 completed successfully.
  - The repository adapter, deterministic 12-case vertical slice and permanent read-only workflow are present.
  - The standalone ASE package requires Python 3.12+ while root Freqtrade Python 3.11 collection remains valid.
  - No live-order path, browser-to-Freqtrade path or nondeterministic Risk Core bypass was introduced.
derived:
  - Later develop movement observed after validation was outside the ASE package, adapter and ASE integration-test paths.
  - A future merge-preparation pass must refresh develop and rerun required checks because the base can move.
unknown:
  - Human review outcome and merge timing for PR 584.
conflicts: []
first_failure:
  marker: ROOT_PYTEST_IMPORT_AND_PYTHON_BOUNDARY
  evidence: Root CI originally failed because local ASE modules were not on pytest pythonpath and Python 3.11 collected a Python 3.12-only test surface; both boundaries were corrected and exact-head CI passed.
rejected_hypotheses:
  - Treat repeated root CI failures as transient without reading the shared traceback.
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
  - command: AI Strategy Engine run 30392791167
    result: PASS
    evidence: Exact-head package tests, Ruff, formatting, mypy, compile, schema, materialization and boundary scans succeeded.
  - command: AI Platform CI run 30392791126
    result: PASS
    evidence: Exact-head platform validation succeeded.
  - command: Freqtrade CI run 30392791151
    result: PASS
    evidence: Pre-commit, documentation, online/live compatibility, core and configured compatibility matrices succeeded.
  - command: GitHub Actions Security Analysis run 30392791332
    result: PASS
    evidence: Exact-head zizmor workflow succeeded.
  - command: Experimental Model Runtime Smoke run 30392791181
    result: PASS
    evidence: Exact-head runtime smoke succeeded.
  - command: Residual PyTorch Runtime Smoke run 30392791096
    result: PASS
    evidence: Exact-head residual runtime smoke succeeded.
blockers: []
next_action: Leave PR 584 draft and unmerged; only after an explicit review or merge-preparation instruction, merge latest develop normally and rerun required checks before changing review state.
```
