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
five-seed aggregate decision. Infrastructure review executed no model, backtest, market-data operation or
cache restore because the canonical request file remained absent.

## Frozen identities and execution geometry

- immutable anchor seed `42`, run `30131273189`, artifact
  `rl-v2-roi-lifecycle-paired-attribution-272`, never rerun;
- new seeds `300538280`, `1710810709`, `1950377252`, `1146911492`;
- exactly four future lifecycle-aligned variant backtests and zero baseline backtests;
- only `freqai.model_training_parameters.seed` may vary behaviorally;
- one canonical exact-one-file trigger PR is required after a separately merged execution checkpoint;
- every trigger PR must be closed without merge after terminal evidence.

## Non-negotiable boundaries

- No request file, training, backtest, data download, cache restore or exchange access occurred in this task.
- Seed `42` and the immutable baseline were not rerun.
- Consumed historical OOS `20260501-20260630` and protected final holdout `20260801-20260930` remain forbidden.
- No profitability, statistical-proof, superiority, ranking, promotion, dry-run or live claim is authorized.
- Phase 6 remains complete with authoritative `selected_model=null`.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-25T19:56:00+02:00
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
  - PR 280 merged an exact seven-path infrastructure package and never added the canonical run request.
  - The execution contract freezes anchor seed 42, four new seeds, zero baseline executions, exact runtime hashes, pre-OOS geometry, validity gates and deterministic aggregate decisions.
  - The request guard permits only the four declared new seeds, rejects anchor seed 42 and unknown seeds, keeps data-split random_state 42 with shuffle false, and materializes only the declared seed delta.
  - Per-seed extraction reconciles the embedded effective runtime config, strategy, model identifier, seed, frozen data split, accounting, pair coverage, minimum trade count, target-flat activity and timeout counters.
  - Invalid or zero-trade seed evidence remains visible and forces an inconclusive aggregate; seed replacement is forbidden.
  - The workflow contains one four-seed matrix backtesting command, no seed-42 command and no baseline command, and aggregates only same-run per-seed artifacts with the immutable anchor.
  - AI Platform CI 1194 / run 30167836599 passed compile, targeted tests, Ruff, Ruff format, codespell and JSON validation on final head f87b7d0b72f73e7c150f88992de3c5692083942f.
  - Freqtrade CI 1394 / run 30167836591 passed pre-commit, scope classification, documentation build and the required cross-platform core-test matrix on final head f87b7d0b72f73e7c150f88992de3c5692083942f.
  - GitHub Actions Security Analysis 1324 / run 30167836585 passed on final head f87b7d0b72f73e7c150f88992de3c5692083942f.
  - PR 280 was squash-merged to develop as 71b16023bbf44d8f092487fea296640b521c39de.
derived:
  - A later valid trigger can produce the declared five-seed evidence set with exactly four new executions because seed 42 is reused immutably.
  - Runtime-config reconciliation prevents changed seed, split, strategy, identifier or materialization semantics from entering the aggregate.
  - This infrastructure enables bounded historical-development robustness evidence only; it cannot create strict-OOS, protected-final, profitability, ranking or promotion evidence.
unknown: []
conflicts: []
first_failure:
  marker: AI Platform CI 1163 / run 30158653922 / Ruff
  evidence: Initial compile and tests passed, while import order, three intentional fail-closed complexity points and formatter drift failed; local C901 annotations, deterministic import formatting and exact Ruff formatting resolved the failure without behavioral changes.
rejected_hypotheses:
  - Add or generate the canonical request during infrastructure review.
  - Execute any seed, baseline, data or cache operation before a separate execution checkpoint and trigger PR.
  - Rerun anchor seed 42 or the immutable baseline.
  - Replace invalid or unfavorable seeds.
  - Trust copied hashes without validating the effective per-seed runtime config.
  - Gate on profitability or access consumed OOS or the protected holdout.
changed_paths:
  - docs/agents/tasks/FTAI-20260725-rl-v2-lifecycle-seed-robustness-infrastructure.md
  - docs/ai_platform/RL_V2_LIFECYCLE_SEED_ROBUSTNESS_INFRASTRUCTURE.md
  - ai_platform/experimental_model_research/rl-v2-lifecycle-seed-robustness-execution-contract-v1.json
  - ai_platform/scripts/rl_v2_lifecycle_seed_robustness_run_request.py
  - ai_platform/scripts/rl_v2_lifecycle_seed_robustness_evidence.py
  - tests/ai_platform/test_rl_v2_lifecycle_seed_robustness.py
  - .github/workflows/ai-platform-rl-v2-lifecycle-seed-robustness.yml
validation:
  - command: final PR 280 scope and canonical-request absence
    result: PASS
    evidence: Final source head contains exactly the seven owned paths, no temporary workflow and no canonical run request.
  - command: AI Platform CI 30167836599 / run 1194
    result: PASS
    evidence: Compile, dependency-light tests, lint, formatting, spelling and JSON validation passed.
  - command: Freqtrade CI 30167836591 / run 1394
    result: PASS
    evidence: Pre-commit, scope, documentation and required core-test matrix passed.
  - command: GitHub Actions Security Analysis 30167836585 / run 1324
    result: PASS
    evidence: Required zizmor workflow-security analysis passed.
  - command: squash merge PR 280
    result: PASS
    evidence: GitHub merged final head f87b7d0b72f73e7c150f88992de3c5692083942f to develop as 71b16023bbf44d8f092487fea296640b521c39de.
blockers: []
next_action: Do not reopen this completed infrastructure task; declare and merge the separate documentation-only execution task at docs/agents/tasks/FTAI-20260725-rl-v2-lifecycle-seed-robustness-execution.md before creating any exact-one-file canonical trigger PR, while preserving zero anchor and baseline reruns, all OOS and holdout prohibitions, historical-development classification, Phase 6 selected_model=null and no-promotion boundaries.
```
