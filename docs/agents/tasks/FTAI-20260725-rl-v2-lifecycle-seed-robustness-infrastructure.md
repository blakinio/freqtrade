---
task_id: FTAI-20260725-rl-v2-lifecycle-seed-robustness-infrastructure
status: done
branch: develop
base_branch: develop
created: 2026-07-25
updated: 2026-07-25
related_pr: "280"
owned_paths:
  - docs/agents/tasks/FTAI-20260725-rl-v2-lifecycle-seed-robustness-infrastructure.md
  - docs/ai_platform/RL_V2_LIFECYCLE_SEED_ROBUSTNESS_INFRASTRUCTURE.md
  - ai_platform/experimental_model_research/rl-v2-lifecycle-seed-robustness-execution-contract-v1.json
  - ai_platform/scripts/rl_v2_lifecycle_seed_robustness_run_request.py
  - ai_platform/scripts/rl_v2_lifecycle_seed_robustness_evidence.py
  - tests/ai_platform/test_rl_v2_lifecycle_seed_robustness.py
  - .github/workflows/ai-platform-rl-v2-lifecycle-seed-robustness.yml
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260725-rl-v2-lifecycle-seed-robustness-declaration.md
  - docs/ai_platform/RL_V2_LIFECYCLE_SEED_ROBUSTNESS_DECLARATION.md
  - ai_platform/experimental_model_research/rl-v2-lifecycle-seed-robustness-declaration-v1.json
  - ai_platform/experimental_model_research/rl-v2-roi-lifecycle-paired-attribution-execution-contract-v1.json
  - ai_platform/scripts/rl_v2_roi_lifecycle_paired_attribution_run_request.py
  - ai_platform/scripts/rl_v2_roi_lifecycle_paired_attribution_evidence.py
  - .github/workflows/ai-platform-rl-v2-roi-lifecycle-paired-attribution.yml
search_first:
  - current develop and open PRs overlapping RL-v2 seeds, lifecycle strategy, PPO configuration, run requests, workflows, evidence or model-selection ownership
optional_reads:
  - tests/ai_platform/test_rl_v2_roi_lifecycle_paired_attribution.py
---

# RL-v2 Lifecycle Seed Robustness Infrastructure

## Goal

Implement a fail-closed and inert request-triggered path for the frozen four-new-seed execution matrix and
five-seed aggregate decision. Infrastructure review must execute no model, backtest, market-data operation
or cache restore because the canonical request file is intentionally absent.

## Frozen identities and execution geometry

- immutable anchor seed `42`, run `30131273189`, artifact
  `rl-v2-roi-lifecycle-paired-attribution-272`, never rerun;
- new seeds `300538280`, `1710810709`, `1950377252`, `1146911492`;
- exactly four future lifecycle-aligned variant backtests and zero baseline backtests;
- only `freqai.model_training_parameters.seed` may vary behaviorally;
- one canonical exact-one-file trigger PR is required after this infrastructure merges;
- every trigger PR must be closed without merge after terminal evidence.

## Non-negotiable boundaries

- No request file in this infrastructure branch or PR.
- No training, backtest, data download, cache restore or exchange access during review.
- No seed `42` rerun and no baseline rerun.
- No consumed historical OOS `20260501-20260630`.
- No protected final holdout `20260801-20260930`.
- No model, strategy, PPO parameter other than seed, reward, feature, threshold, pair, timeframe, fee,
  geometry or policy-semantic change.
- No profitability, statistical-proof, superiority, ranking, promotion, dry-run or live claim.
- Phase 6 remains complete with authoritative `selected_model=null`.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-25T19:58:00+02:00
head: 71b16023bbf44d8f092487fea296640b521c39de
branch: develop
pr: 280
status: ready
context_routes:
  - docs/agents/tasks/FTAI-20260725-rl-v2-lifecycle-seed-robustness-declaration.md
  - docs/ai_platform/RL_V2_LIFECYCLE_SEED_ROBUSTNESS_DECLARATION.md
  - ai_platform/experimental_model_research/rl-v2-lifecycle-seed-robustness-declaration-v1.json
owned_paths:
  - docs/agents/tasks/FTAI-20260725-rl-v2-lifecycle-seed-robustness-infrastructure.md
  - docs/ai_platform/RL_V2_LIFECYCLE_SEED_ROBUSTNESS_INFRASTRUCTURE.md
  - ai_platform/experimental_model_research/rl-v2-lifecycle-seed-robustness-execution-contract-v1.json
  - ai_platform/scripts/rl_v2_lifecycle_seed_robustness_run_request.py
  - ai_platform/scripts/rl_v2_lifecycle_seed_robustness_evidence.py
  - tests/ai_platform/test_rl_v2_lifecycle_seed_robustness.py
  - .github/workflows/ai-platform-rl-v2-lifecycle-seed-robustness.yml
proven:
  - PR 280 introduced exactly the seven declared infrastructure paths and no canonical request file.
  - The execution contract freezes anchor seed 42, four outcome-independent new seeds, zero baseline executions, runtime hashes, data geometry, validity gates and deterministic aggregate decisions.
  - The request-triggered workflow contains four new-seed jobs, no seed-42 command and no baseline command, and remains inert while the canonical request path is absent.
  - Per-seed extraction reconciles the embedded effective runtime config with the expected seed-only materialization before accepting evidence.
  - Dependency-light tests cover materialization, anchor rejection, aggregate decisions, invalid-seed handling, evidence tamper rejection, runtime-config drift rejection and workflow inertness.
  - Final source head f87b7d0b72f73e7c150f88992de3c5692083942f passed AI Platform CI 1194, Freqtrade CI 1394 and zizmor 1324.
  - PR 280 was squash-merged to develop as 71b16023bbf44d8f092487fea296640b521c39de.
  - Infrastructure review performed no model execution, backtest, market-data access, cache restore, baseline rerun, anchor rerun, consumed-OOS access or protected-holdout access.
  - The package preserves paired historical-development classification, strict_oos=false, protected_final_validation=false, profitability non-gating and Phase 6 selected_model=null.
derived:
  - A later valid five-seed study requires only the four declared new executions because seed 42 remains an immutable anchor.
  - Any later aggregate can assess stochastic mechanism consistency on reused development data but cannot establish strict OOS, profitability, statistical proof, ranking, promotion or deployment readiness.
unknown: []
conflicts: []
first_failure:
  marker: NONE
  evidence: Initial Ruff import, complexity and formatting findings were repaired locally; all final required CI completed successfully before merge.
rejected_hypotheses:
  - Add or generate the canonical request during infrastructure review.
  - Execute any seed, baseline, market-data or cache operation before a separate authorized trigger task.
  - Rerun anchor seed 42 or the immutable baseline.
  - Permit outcome-based seed replacement or discretionary evidence removal.
  - Trust copied runtime hashes without reconciling the effective runtime config.
  - Add persistent repository-wide or per-file Ruff exemptions instead of fixing owned files.
  - Gate on profitability or access consumed OOS or protected holdout data.
changed_paths:
  - docs/agents/tasks/FTAI-20260725-rl-v2-lifecycle-seed-robustness-infrastructure.md
  - docs/ai_platform/RL_V2_LIFECYCLE_SEED_ROBUSTNESS_INFRASTRUCTURE.md
  - ai_platform/experimental_model_research/rl-v2-lifecycle-seed-robustness-execution-contract-v1.json
  - ai_platform/scripts/rl_v2_lifecycle_seed_robustness_run_request.py
  - ai_platform/scripts/rl_v2_lifecycle_seed_robustness_evidence.py
  - tests/ai_platform/test_rl_v2_lifecycle_seed_robustness.py
  - .github/workflows/ai-platform-rl-v2-lifecycle-seed-robustness.yml
validation:
  - command: compare develop to final PR 280 source head
    result: PASS
    evidence: Final PR scope was exactly seven declared paths with zero divergence, no request file and no temporary workflow.
  - command: canonical request absence check
    result: PASS
    evidence: The exact trigger path was absent throughout infrastructure review, so the dedicated workflow executed no seed or data operation.
  - command: AI Platform CI 30167836599 / run 1194
    result: PASS
    evidence: Compile, AI platform tests, Ruff, Ruff format, codespell and JSON validation passed on final head f87b7d0b72f73e7c150f88992de3c5692083942f.
  - command: Freqtrade CI 30167836591 / run 1394
    result: PASS
    evidence: Scope, pre-commit, documentation and all required core test matrices passed on the final source head.
  - command: GitHub Actions Security Analysis 30167836585 / run 1324
    result: PASS
    evidence: Required zizmor workflow-security analysis passed on the final source head.
  - command: squash merge PR 280
    result: PASS
    evidence: GitHub merged final source head f87b7d0b72f73e7c150f88992de3c5692083942f to develop as 71b16023bbf44d8f092487fea296640b521c39de.
  - command: python tools/agents/checkpoint.py docs/agents/tasks/FTAI-20260725-rl-v2-lifecycle-seed-robustness-infrastructure.md --require-checkpoint
    result: PASS
    evidence: The completed checkpoint satisfies the shared governance contract and compactness limits.
blockers: []
next_action: Do not reopen this completed infrastructure task; declare a separate bounded seed-robustness execution task and exact-one-file trigger PR only if they reuse anchor seed 42 without rerun, execute exactly the four frozen new seeds with zero baseline runs, preserve all OOS, holdout, Phase 6 and no-promotion boundaries, and close the trigger PR without merge after terminal evidence.
```
