---
task_id: FTAI-20260725-rl-v2-lifecycle-seed-robustness-infrastructure
status: active
branch: feat/rl-v2-lifecycle-seed-robustness-infrastructure
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
updated_at: 2026-07-25T14:51:00+02:00
head: d296c321fcdf89bccb675f654a3a1cc199e20121
branch: feat/rl-v2-lifecycle-seed-robustness-infrastructure
pr: 280
status: validating
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
  - PR 280 contains exactly seven declared infrastructure paths and no canonical request file.
  - The canonical request file is absent, so the dedicated seed workflow cannot run during infrastructure review.
  - The execution contract freezes anchor seed 42, four new seeds, zero baseline executions, runtime hashes, data geometry, validity rules and deterministic aggregate decisions.
  - The workflow contains one matrix backtesting command for four new seeds, no seed-42 command and no baseline command.
  - The workflow uses pinned actions/download-artifact commit 3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c only to aggregate same-run per-seed artifacts.
  - Dependency-light tests cover seed-only materialization, anchor rejection, supported aggregation, invalid-seed inconclusive handling, tamper rejection and workflow inertness.
derived:
  - Four isolated seed jobs plus one aggregate job implement the declared five-seed evidence geometry without rerunning anchor seed 42.
  - Invalid or zero-trade evidence must remain visible and force an inconclusive aggregate rather than allowing discretionary replacement.
unknown:
  - Whether final PR 280 HEAD passes all required repository CI and workflow-security checks.
conflicts: []
first_failure:
  marker: NONE
  evidence: The previous GitHub connector routing incident cleared; all seven candidate paths are published and PR 280 is open.
rejected_hypotheses:
  - Add or generate the canonical request during infrastructure review.
  - Execute any seed, baseline, data or cache operation before a later trigger PR.
  - Rerun anchor seed 42 to simplify aggregation.
  - Permit invalid seed replacement or discretionary evidence removal.
  - Gate on profitability or access OOS or protected holdout data.
changed_paths:
  - docs/agents/tasks/FTAI-20260725-rl-v2-lifecycle-seed-robustness-infrastructure.md
  - docs/ai_platform/RL_V2_LIFECYCLE_SEED_ROBUSTNESS_INFRASTRUCTURE.md
  - ai_platform/experimental_model_research/rl-v2-lifecycle-seed-robustness-execution-contract-v1.json
  - ai_platform/scripts/rl_v2_lifecycle_seed_robustness_run_request.py
  - ai_platform/scripts/rl_v2_lifecycle_seed_robustness_evidence.py
  - tests/ai_platform/test_rl_v2_lifecycle_seed_robustness.py
  - .github/workflows/ai-platform-rl-v2-lifecycle-seed-robustness.yml
validation:
  - command: compare develop to PR 280 head
    result: PASS
    evidence: PR scope is exactly the seven declared paths and contains no run request.
  - command: canonical request absence check
    result: PASS
    evidence: The exact run-request path is absent; infrastructure review cannot trigger model or data execution.
blockers: []
next_action: Treat only CI runs for the post-checkpoint PR 280 head as authoritative, fix evidence-backed validation failures, and merge only after AI Platform CI, Freqtrade CI and zizmor are green.
```
