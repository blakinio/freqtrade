---
task_id: FTAI-20260728-ase-00-ai-strategy-engine-foundation
status: validating
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
updated_at: 2026-07-28T23:17:00+02:00
head: 5f80351b862638e6e0e9f6f064054db902068dc8
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
  - PR 584 is open, draft, unmerged and mergeable at the post-refresh check.
  - Develop 436b5350e54a33cbf070738a2328b142ffcd5174 was merged normally without force-push into branch commit 5f80351b862638e6e0e9f6f064054db902068dc8.
  - The latest develop movement contains Portal Vault credential-broker and Synology deployment paths outside ASE, its adapter and integration tests.
  - The one-shot merge workflow removed itself and is absent from the PR diff.
  - Exact-head validation succeeded on the preceding review-ready head 18041af549cc0ad9f35deb2f5cd6489fcf7c1ec5.
  - All PR review threads are resolved and outdated; no human approval or change request is present.
  - The repository adapter, deterministic 12-case vertical slice and permanent read-only workflow are present.
  - The standalone ASE package requires Python 3.12+ while root Freqtrade Python 3.11 collection remains valid.
  - No live-order path, browser-to-Freqtrade path or nondeterministic Risk Core bypass was introduced.
derived:
  - The latest develop commit does not alter the delivered ASE behavior but exact-head checks must rerun before restoring ready-for-review state.
  - Further Strategy Engine functionality belongs in a separate bounded work package using the canonical contracts delivered here.
unknown:
  - Human review outcome and final merge timing for PR 584.
conflicts: []
first_failure:
  marker: ROOT_PYTEST_IMPORT_AND_PYTHON_BOUNDARY
  evidence: Root CI originally failed because local ASE modules were not on pytest pythonpath and Python 3.11 collected a Python 3.12-only test surface; both boundaries were corrected and exact-head CI passed.
rejected_hypotheses:
  - Leave the PR ready for review while it is behind develop.
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
  - command: AI Strategy Engine exact-head run
    result: NOT_RUN
    evidence: Triggered by this user-authored post-refresh checkpoint commit.
  - command: AI Platform CI exact-head run
    result: NOT_RUN
    evidence: Triggered by this user-authored post-refresh checkpoint commit.
  - command: Freqtrade CI exact-head run
    result: NOT_RUN
    evidence: Triggered by this user-authored post-refresh checkpoint commit.
  - command: GitHub Actions Security Analysis exact-head run
    result: NOT_RUN
    evidence: Triggered by this user-authored post-refresh checkpoint commit.
  - command: Experimental Model Runtime Smoke exact-head run
    result: NOT_RUN
    evidence: Triggered by this user-authored post-refresh checkpoint commit.
  - command: Residual PyTorch Runtime Smoke exact-head run
    result: NOT_RUN
    evidence: Triggered by this user-authored post-refresh checkpoint commit.
blockers: []
next_action: Wait for all exact-head workflows on the post-refresh checkpoint commit; if they pass and the branch remains current and mergeable, record final evidence and mark PR 584 ready for human review.
```
