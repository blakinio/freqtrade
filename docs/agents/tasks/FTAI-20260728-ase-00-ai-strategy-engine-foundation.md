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
updated_at: 2026-07-28T22:37:00+02:00
head: 2ff8dafa1a3f00b4aac0420ebfd8d6f2cfaa96c2
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
  - PR 584 is open, draft, unmerged and mergeable at the post-merge check.
  - Develop be47cdfd4692ea28281e0a1158cab6c98db38608 was merged normally without force-push into branch commit 2ff8dafa1a3f00b4aac0420ebfd8d6f2cfaa96c2.
  - The branch is behind_by 0 relative to develop after the merge.
  - The one-shot merge workflow removed itself in the merge commit and is absent from the PR diff.
  - Develop movement merged into the branch is limited to Portal dashboard, WickHunter and unrelated task/documentation paths outside the ASE package, adapter and ASE integration-test paths.
  - Exact-head validation previously succeeded on pre-merge checkpoint head 43d1028973882e6aa34790a09a583eac4e056f60.
  - GitHub marked bot-pushed post-merge workflow records action_required before jobs ran; this is not test-failure evidence.
  - All PR review threads are resolved and outdated; no human approval or change request is present.
  - The repository adapter, deterministic 12-case vertical slice and permanent read-only workflow are present.
  - The standalone ASE package requires Python 3.12+ while root Freqtrade Python 3.11 collection remains valid.
  - No live-order path, browser-to-Freqtrade path or nondeterministic Risk Core bypass was introduced.
derived:
  - A user-authored checkpoint commit is required to trigger normal PR workflows after the GITHUB_TOKEN merge push.
  - Review state may change only after the post-merge required workflows complete successfully.
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
  - command: AI Strategy Engine post-merge run
    result: NOT_RUN
    evidence: Normal PR run will be triggered by this user-authored checkpoint commit.
  - command: AI Platform CI post-merge run
    result: NOT_RUN
    evidence: Normal PR run will be triggered by this user-authored checkpoint commit.
  - command: Freqtrade CI post-merge run
    result: NOT_RUN
    evidence: Normal PR run will be triggered by this user-authored checkpoint commit.
  - command: GitHub Actions Security Analysis post-merge run
    result: NOT_RUN
    evidence: Normal PR run will be triggered by this user-authored checkpoint commit.
  - command: Experimental Model Runtime Smoke post-merge run
    result: NOT_RUN
    evidence: Normal PR run will be triggered by this user-authored checkpoint commit.
  - command: Residual PyTorch Runtime Smoke post-merge run
    result: NOT_RUN
    evidence: Normal PR run will be triggered by this user-authored checkpoint commit.
blockers: []
next_action: Wait for all required workflows on the user-authored post-merge checkpoint commit; if they pass and PR 584 remains mergeable, record the evidence and mark the PR ready for review.
```
