---
task_id: FTAI-20260721-experimental-model-dependency-profile
status: implementing
branch: fix/experimental-model-dependency-profile-v1
base_branch: develop
created: 2026-07-21
updated: 2026-07-21
related_pr: ""
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
updated_at: 2026-07-21T08:35:00Z
head: dde7d7b9e68a50047ea66abcf98835bb65f25402
branch: fix/experimental-model-dependency-profile-v1
pr: none
status: implementing
context_routes:
  - docs/ai_platform/EXPERIMENTAL_MODEL_RESEARCH.md
  - docs/ai_platform/EXPERIMENTAL_MODEL_RUNTIME_SMOKE.md
owned_paths:
  - ai_platform/experimental_model_research/foundation-v1.json
  - tests/ai_platform/test_experimental_model_research_contract.py
  - docs/ai_platform/EXPERIMENTAL_MODEL_RESEARCH.md
  - docs/agents/tasks/FTAI-20260721-experimental-model-dependency-profile.md
proven:
  - develop was verified at dde7d7b9e68a50047ea66abcf98835bb65f25402 before this reconciliation branch was created.
  - PR #61 proved the canonical PyTorch and RL runtime paths using the combined freqai and freqai_rl optional dependency profiles.
  - The canonical foundation still declared freqtrade[freqai_rl] for both tracks, which does not match the dependency-closed profile used by the proven runtime workflow.
  - Open PR #62 independently identified the same dependency-profile mismatch but also overlaps the already-merged heavy-runtime implementation and checkpoint files.
  - Open PR #63 is a separate Phase 6 execution-infrastructure track and is outside this task's owned paths.
  - This reconciliation changes only the experimental dependency profile, its lightweight test, and documentation; protected final holdout 20260801-20260930 and frozen thresholds 0.006/-0.009 remain untouched.
derived:
  - The smallest safe reconciliation is to pin freqtrade[freqai,freqai_rl] in the canonical foundation and tests while leaving the merged runtime implementation as the source of truth.
unknown:
  - CI outcome for the reconciliation branch.
conflicts:
  - PR #62 overlaps the merged heavy-runtime task and should not be merged wholesale after this narrower reconciliation lands.
first_failure:
  marker: dependency-profile-contract-drift
  evidence: The merged heavy-runtime workflow required both freqai and freqai_rl, while foundation-v1.json still declared only freqtrade[freqai_rl] for both canonical tracks.
rejected_hypotheses:
  - Merge PR #62 wholesale despite overlapping the already-merged PR #61 runtime implementation and checkpoint.
  - Change Phase 6, model parameters, temporal geometry, or protected-final-holdout rules while correcting dependency metadata.
changed_paths:
  - ai_platform/experimental_model_research/foundation-v1.json
  - tests/ai_platform/test_experimental_model_research_contract.py
  - docs/ai_platform/EXPERIMENTAL_MODEL_RESEARCH.md
  - docs/agents/tasks/FTAI-20260721-experimental-model-dependency-profile.md
validation:
  - command: GitHub Actions
    result: NOT_RUN
    evidence: Reconciliation pull request has not been opened yet.
blockers: []
next_action: Open the reconciliation pull request against develop, validate AI Platform CI, Freqtrade CI and zizmor, then merge it and close PR #62 as superseded if no unique required change remains.
```
