---
task_id: FTAI-20260721-experimental-model-runtime-smoke-hardening
status: implementing
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
updated_at: 2026-07-21T09:10:00Z
head: ada6b1cb74f7ed2aa1b50984a17a4aed5d4be7fe
branch: test/experimental-model-runtime-smoke-hardening-v1
pr: "#68"
status: implementing
context_routes:
  - docs/ai_platform/EXPERIMENTAL_MODEL_RUNTIME_SMOKE.md
  - ai_platform/scripts/experimental_model_runtime_smoke.py
owned_paths:
  - ai_platform/scripts/experimental_model_runtime_smoke.py
  - .github/workflows/experimental-model-runtime-smoke.yml
  - docs/ai_platform/EXPERIMENTAL_MODEL_RUNTIME_SMOKE.md
  - docs/agents/tasks/FTAI-20260721-experimental-model-runtime-smoke-hardening.md
proven:
  - The task was initially branched from develop at 3c9e1aac83b092e7b773821a3946c1eda5c2fa26.
  - Phase 6 workflow PR #63 independently merged into develop as 433d9a70289c901a6ce74f2cbcab071583c47c03 after the first fully green PR #68 validation run; it did not modify any runtime-smoke-hardening owned path.
  - The runtime-smoke-hardening changes were therefore replayed unchanged onto develop 433d9a70289c901a6ce74f2cbcab071583c47c03 before final validation.
  - PR #61 and checkpoint closure #64 established a working synthetic heavy-runtime smoke for canonical PyTorch and RL classes.
  - PR #65 and checkpoint closure #67 corrected the canonical dependency profile to freqtrade[freqai,freqai_rl].
  - Closed unmerged PR #62 had a fully green AI Platform Heavy Runtime Smoke run 29813258498 plus AI Platform CI 29813258636, Freqtrade CI 29813258445, and zizmor 29813258564.
  - The hardened smoke constructs SeededPyTorchMLPRegressor and LongOnlyReinforcementLearner from the tracked canonical configs instead of bypassing constructors with object.__new__.
  - The hardened PyTorch smoke performs two identical seeded fits in one CPU runtime and requires exact equality across all fitted state_dict tensors.
  - The hardened RL smoke verifies PPO resolution, canonical seed and fee from pack_env_dict, the three-action long-only environment contract, explicit enter/neutral/exit actions, set_train_and_eval_environments, and inherited PPO fit completion.
  - The hardened workflow uses the dependency-closed freqai plus freqai_rl profile, validates this task checkpoint before pull-request runtime execution, and watches canonical configs and foundation drift as well as model code.
  - The first PR #68 validation on the pre-#63 base passed Experimental Model Runtime Smoke run 29816941001, AI Platform CI 29816940740, Freqtrade CI 29816940668, and zizmor 29816940724.
  - Open PR #66 owns only historical-execution preflight files and does not overlap this task.
  - Protected final holdout 20260801-20260930 remains forbidden; this smoke uses deterministic synthetic data inside the declared 20251201-20260228 training window only.
derived:
  - Replaying the exact four-file hardening diff onto the current develop base preserves the already-green semantics while ensuring final CI covers the latest Phase 6 infrastructure merge.
unknown:
  - Whether the replayed final PR #68 head remains green against develop 433d9a70289c901a6ce74f2cbcab071583c47c03.
conflicts: []
first_failure:
  marker: pr68-base-advanced
  evidence: PR #68 was fully green but became non-mergeable after independent Phase 6 PR #63 advanced develop; no owned path overlapped, so the hardening diff was replayed unchanged onto the new base.
rejected_hypotheses:
  - Merge PR #68 while GitHub reports it non-mergeable against an outdated base.
  - Reopen or merge PR #62 wholesale despite stale overlapping changes.
  - Use historical OOS or the protected final holdout to harden a runtime-only smoke.
  - Interpret same-runtime reproducibility or PPO completion as trading performance evidence.
changed_paths:
  - ai_platform/scripts/experimental_model_runtime_smoke.py
  - .github/workflows/experimental-model-runtime-smoke.yml
  - docs/ai_platform/EXPERIMENTAL_MODEL_RUNTIME_SMOKE.md
  - docs/agents/tasks/FTAI-20260721-experimental-model-runtime-smoke-hardening.md
validation:
  - command: Experimental Model Runtime Smoke run 29816941001
    result: PASS
    evidence: First PR #68 head passed the combined canonical-config PyTorch reproducibility and RL environment/PPO smoke before develop advanced.
  - command: AI Platform CI run 29816940740
    result: PASS
    evidence: First PR #68 head completed successfully.
  - command: Freqtrade CI run 29816940668
    result: PASS
    evidence: First PR #68 head completed successfully.
  - command: zizmor run 29816940724
    result: PASS
    evidence: First PR #68 head completed successfully.
blockers: []
next_action: Force-update PR #68 head to the replayed commits based on develop 433d9a70289c901a6ce74f2cbcab071583c47c03, then require the dedicated runtime smoke and normal CI gates to pass again before merge.
```
