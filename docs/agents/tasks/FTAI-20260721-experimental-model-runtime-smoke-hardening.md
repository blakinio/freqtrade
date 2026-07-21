---
task_id: FTAI-20260721-experimental-model-runtime-smoke-hardening
status: done
branch: test/experimental-model-runtime-smoke-hardening-v1
base_branch: develop
created: 2026-07-21
updated: 2026-07-21
related_pr: "#68"
owned_paths:
  - ai_platform/scripts/experimental_model_runtime_smoke.py
  - .github/workflows/experimental-model-runtime-smoke.yml
  - docs/ai_platform/EXPERIMENTAL_MODEL_RUNTIME_SMOKE.md
  - docs/agents/tasks/FTAI-20260721-experimental-model-runtime-smoke-hardening.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/EXPERIMENTAL_MODEL_RESEARCH.md
  - docs/ai_platform/EXPERIMENTAL_MODEL_RUNTIME_SMOKE.md
search_first:
  - ai_platform/scripts/experimental_model_runtime_smoke.py
optional_reads:
  - ai_platform/configs/freqai-pytorch-research.example.json
  - ai_platform/configs/freqai-rl-research.example.json
---

# Experimental Model Runtime Smoke Hardening v1

## Goal

Preserve the stronger, already-green runtime-validation semantics from closed PR #62 on current develop without reintroducing its stale overlapping dependency/profile/checkpoint changes: construct both canonical models from tracked configs, prove same-runtime seeded PyTorch reproducibility, and exercise RL through the canonical environment-setup and inherited PPO fit path.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-21T09:25:00Z
head: 219d996f986e1544a4efeb3cc8a2f2b13f5366d4
branch: develop
pr: "#68 merged"
status: done
context_routes:
  - docs/ai_platform/EXPERIMENTAL_MODEL_RUNTIME_SMOKE.md
  - ai_platform/scripts/experimental_model_runtime_smoke.py
owned_paths:
  - ai_platform/scripts/experimental_model_runtime_smoke.py
  - .github/workflows/experimental-model-runtime-smoke.yml
  - docs/ai_platform/EXPERIMENTAL_MODEL_RUNTIME_SMOKE.md
  - docs/agents/tasks/FTAI-20260721-experimental-model-runtime-smoke-hardening.md
proven:
  - PR #68 was squash-merged into develop as 219d996f986e1544a4efeb3cc8a2f2b13f5366d4 after the final head remained mergeable and had no review threads.
  - The task was initially branched from develop at 3c9e1aac83b092e7b773821a3946c1eda5c2fa26.
  - Phase 6 workflow PR #63 and closure PR #69 independently advanced develop without modifying any runtime-smoke-hardening owned path.
  - The runtime-smoke-hardening changes were replayed unchanged onto the newer develop base before final validation.
  - PR #61 and checkpoint closure #64 established the initial synthetic heavy-runtime smoke for canonical PyTorch and RL classes.
  - PR #65 and checkpoint closure #67 corrected the canonical dependency profile to freqtrade[freqai,freqai_rl].
  - Closed unmerged PR #62 had stronger useful validation semantics that were preserved without its stale overlapping changes.
  - The merged hardened smoke constructs SeededPyTorchMLPRegressor and LongOnlyReinforcementLearner from the tracked canonical configs instead of bypassing constructors with object.__new__.
  - The merged PyTorch smoke performs two identical seeded fits in one CPU runtime and requires exact equality across all fitted state_dict tensors.
  - The merged RL smoke verifies PPO resolution, canonical seed and fee from pack_env_dict, the three-action long-only environment contract, explicit enter/neutral/exit actions, set_train_and_eval_environments, and inherited PPO fit completion.
  - Final Experimental Model Runtime Smoke run 29817391948 completed successfully on PR #68 head 9ae5a492e5bdcb8ddf6a81a2a2e43a87dadfe548.
  - Final AI Platform CI run 29817391814, Freqtrade CI run 29817391734, and zizmor run 29817391843 completed successfully on the same final head; Pre-commit Types update was skipped rather than failed.
  - Protected final holdout 20260801-20260930 remained unused; no historical OOS was scored and no Phase 6 membership, retuning, promotion, profitability, or superiority conclusion was produced.
derived:
  - The experimental runtime foundation now has stronger canonical-config and reproducibility evidence suitable as a prerequisite for later bounded historical execution, but it still says nothing about trading quality.
unknown:
  - Historical market-data availability and exact coverage for the canonical experimental execution remain governed by open PR #66 and its dedicated preflight.
conflicts: []
first_failure:
  marker: pr68-base-advanced
  evidence: PR #68 was fully green but became non-mergeable after independent Phase 6 work advanced develop; no owned path overlapped, so the hardening diff was replayed unchanged onto the newer base and all required checks passed again.
rejected_hypotheses:
  - Merge PR #68 while GitHub reported it non-mergeable against an outdated base.
  - Reopen or merge PR #62 wholesale despite stale overlapping changes.
  - Use historical OOS or the protected final holdout to harden a runtime-only smoke.
  - Interpret same-runtime reproducibility or PPO completion as trading performance evidence.
changed_paths:
  - ai_platform/scripts/experimental_model_runtime_smoke.py
  - .github/workflows/experimental-model-runtime-smoke.yml
  - docs/ai_platform/EXPERIMENTAL_MODEL_RUNTIME_SMOKE.md
  - docs/agents/tasks/FTAI-20260721-experimental-model-runtime-smoke-hardening.md
validation:
  - command: Experimental Model Runtime Smoke run 29817391948
    result: PASS
    evidence: Final PR #68 head passed checkpoint validation and the combined canonical-config PyTorch reproducibility plus RL environment/PPO smoke.
  - command: AI Platform CI run 29817391814
    result: PASS
    evidence: Final PR #68 head completed successfully.
  - command: Freqtrade CI run 29817391734
    result: PASS
    evidence: Final PR #68 head completed successfully.
  - command: zizmor run 29817391843
    result: PASS
    evidence: Final PR #68 head completed successfully.
blockers: []
next_action: Continue the independent experimental historical-execution preflight in PR #66; require its dedicated Kraken data-coverage preflight and normal CI gates to succeed, fix only concrete failures, then merge and close its durable checkpoint before creating any real PyTorch or RL historical backtest execution request.
```
