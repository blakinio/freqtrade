---
task_id: FTAI-20260725-rl-v2-lifecycle-seed-robustness-infrastructure
status: active
branch: feat/rl-v2-lifecycle-seed-robustness-infrastructure
base_branch: develop
created: 2026-07-25
updated: 2026-07-25
related_pr: ""
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
updated_at: 2026-07-25T10:31:35+02:00
head: 2ea44b33423d199f5ab020e07031b14642806303
branch: feat/rl-v2-lifecycle-seed-robustness-infrastructure
pr: 0
status: implementing
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
  - Develop head 2ea44b33423d199f5ab020e07031b14642806303 contains the completed deterministic seed declaration and closure records.
  - No open PR overlaps RL-v2 seed robustness infrastructure ownership.
  - Existing paired-attribution verifier provides fail-closed temporal and pre-OOS data coverage validation.
  - Existing paired evidence helpers reconcile raw trades and frozen mechanism metrics.
  - actions/download-artifact v8 resolves to official commit 3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c.
derived:
  - The new workflow can remain inert until an exact canonical request is added in a later separate PR.
  - Four isolated seed jobs plus one aggregate job implement the declared evidence geometry without rerunning anchor seed 42.
unknown:
  - Whether the complete infrastructure implementation passes repository CI without contract drift.
conflicts: []
first_failure:
  marker: NONE
  evidence: Fresh live-state preflight found no overlapping infrastructure PR or changed develop head.
rejected_hypotheses:
  - Add or generate the canonical request during infrastructure review.
  - Execute any seed, baseline, data or cache operation before a later trigger PR.
  - Rerun anchor seed 42 to simplify aggregation.
  - Permit invalid seed replacement or discretionary evidence removal.
  - Gate on profitability or access OOS or protected holdout data.
changed_paths:
  - docs/agents/tasks/FTAI-20260725-rl-v2-lifecycle-seed-robustness-infrastructure.md
validation:
  - command: live-state overlap and develop preflight
    result: PASS
    evidence: Develop remains 2ea44b33423d199f5ab020e07031b14642806303 and no open seed-robustness infrastructure PR exists.
blockers: []
next_action: Implement the frozen contract, canonical validator, per-seed and aggregate evidence extraction, inert request-triggered workflow and dependency-light regression tests without adding the request file or executing model/data paths.
```
