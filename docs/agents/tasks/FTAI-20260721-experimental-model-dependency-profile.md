---
task_id: FTAI-20260721-experimental-model-dependency-profile
status: done
branch: fix/experimental-model-dependency-profile-v1
base_branch: develop
created: 2026-07-21
updated: 2026-07-21
related_pr: "#65"
owned_paths:
  - ai_platform/experimental_model_research/foundation-v1.json
  - tests/ai_platform/test_experimental_model_research_contract.py
  - docs/ai_platform/EXPERIMENTAL_MODEL_RESEARCH.md
  - docs/agents/tasks/FTAI-20260721-experimental-model-dependency-profile.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/EXPERIMENTAL_MODEL_RESEARCH.md
  - docs/ai_platform/EXPERIMENTAL_MODEL_RUNTIME_SMOKE.md
search_first: []
optional_reads:
  - ai_platform/experimental_model_research/foundation-v1.json
---

# Experimental Model Dependency Profile Reconciliation

## Goal

Reconcile the canonical experimental-model research dependency contract with the heavy-runtime profile that was actually required and proven by the merged PyTorch/RL runtime smoke, without changing Phase 6, temporal geometry, model parameters, or any evaluation result.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-21T08:50:00Z
head: ea30e3c2ff5df3824ba7312b9b59e9e7f141b947
branch: develop
pr: "#65 merged"
status: done
context_routes:
  - docs/ai_platform/EXPERIMENTAL_MODEL_RESEARCH.md
  - docs/ai_platform/EXPERIMENTAL_MODEL_RUNTIME_SMOKE.md
owned_paths:
  - ai_platform/experimental_model_research/foundation-v1.json
  - tests/ai_platform/test_experimental_model_research_contract.py
  - docs/ai_platform/EXPERIMENTAL_MODEL_RESEARCH.md
  - docs/agents/tasks/FTAI-20260721-experimental-model-dependency-profile.md
proven:
  - PR #65 was squash-merged into develop as ea30e3c2ff5df3824ba7312b9b59e9e7f141b947 after the head remained mergeable and no review comments or review threads were present.
  - The canonical PyTorch and RL tracks now pin the dependency-closed heavy runtime profile freqtrade[freqai,freqai_rl].
  - A lightweight contract test now prevents either canonical research track from drifting back to an incomplete dependency profile.
  - AI Platform CI run 29814651453, Freqtrade CI run 29814651335, and zizmor run 29814651312 completed successfully on PR #65 head 2f519a2233474a77f941204c6e67a9f53db9517e; Pre-commit Types update run 29814651350 was skipped rather than failed.
  - Protected final holdout 20260801-20260930 and frozen thresholds 0.006/-0.009 remained untouched; no Phase 6 membership, promotion, historical-OOS scoring, or profitability conclusion was produced.
  - Open PR #62 overlaps the already-merged heavy-runtime implementation and the dependency-profile correction now merged through PR #65.
  - PR #62 also contains unique stronger runtime validation not present in merged PR #61: canonical config-based model construction, same-runtime PyTorch reproducibility checking, and RL execution through set_train_and_eval_environments before inherited PPO fit.
derived:
  - PR #62 must not be merged wholesale because its overlapping files are stale, but its stronger runtime-validation semantics should be preserved in a clean follow-up based on current develop before PR #62 is closed.
unknown:
  - Whether the stronger canonical-config runtime smoke from PR #62 passes unchanged when reapplied on current develop after merged PRs #61 and #65.
conflicts:
  - PR #62 combines already-merged/stale overlap with still-useful stronger runtime-validation semantics.
first_failure:
  marker: dependency-profile-contract-drift
  evidence: The merged heavy-runtime workflow required both freqai and freqai_rl, while foundation-v1.json still declared only freqtrade[freqai_rl] for both canonical tracks; PR #65 corrected this drift.
rejected_hypotheses:
  - Merge PR #62 wholesale despite overlapping the already-merged PR #61 runtime implementation and checkpoint.
  - Close PR #62 immediately without preserving its unique canonical-config and reproducibility validation.
  - Change Phase 6, model parameters, temporal geometry, or protected-final-holdout rules while correcting dependency metadata.
changed_paths:
  - ai_platform/experimental_model_research/foundation-v1.json
  - tests/ai_platform/test_experimental_model_research_contract.py
  - docs/ai_platform/EXPERIMENTAL_MODEL_RESEARCH.md
  - docs/agents/tasks/FTAI-20260721-experimental-model-dependency-profile.md
validation:
  - command: GitHub Actions AI Platform CI #266
    result: PASS
    evidence: Run 29814651453 completed successfully on PR #65.
  - command: GitHub Actions Freqtrade CI #283
    result: PASS
    evidence: Run 29814651335 completed successfully, including the full Python 3.12 coverage job and repository-wide matrix.
  - command: GitHub Actions Security Analysis with zizmor #262
    result: PASS
    evidence: Run 29814651312 completed successfully on PR #65.
blockers: []
next_action: Create a clean bounded runtime-smoke-hardening task from current develop that preserves only PR #62's unique canonical-config model construction, same-runtime PyTorch reproducibility proof, and RL set_train_and_eval_environments integration path in the existing experimental runtime smoke workflow; validate and merge that follow-up, then close PR #62 as superseded before starting historical experimental execution.
```
