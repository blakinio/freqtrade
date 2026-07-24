---
task_id: FTAI-20260724-rl-v2-roi-lifecycle-paired-attribution-execution
status: active
branch: develop
base_branch: develop
created: 2026-07-24
updated: 2026-07-25
related_pr: "269"
owned_paths:
  - docs/agents/tasks/FTAI-20260724-rl-v2-roi-lifecycle-paired-attribution-execution.md
  - docs/ai_platform/RL_V2_ROI_LIFECYCLE_PAIRED_ATTRIBUTION_EXECUTION.md
  - ai_platform/experimental_model_research/rl-v2-roi-lifecycle-paired-attribution-execution-contract-v1.json
  - ai_platform/scripts/rl_v2_roi_lifecycle_paired_attribution_run_request.py
  - ai_platform/scripts/rl_v2_roi_lifecycle_paired_attribution_evidence.py
  - tests/ai_platform/test_rl_v2_roi_lifecycle_paired_attribution.py
  - .github/workflows/ai-platform-rl-v2-roi-lifecycle-paired-attribution.yml
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260724-rl-v2-historical-evidence-diagnosis.md
  - docs/ai_platform/RL_V2_HISTORICAL_EVIDENCE_DIAGNOSIS.md
  - ai_platform/experimental_model_research/rl-v2-historical-evidence-diagnosis-v1.json
  - docs/agents/tasks/FTAI-20260724-rl-v2-roi-lifecycle-alignment.md
  - docs/ai_platform/RL_V2_ROI_LIFECYCLE_ALIGNMENT.md
  - ai_platform/experimental_model_research/rl-v2-roi-lifecycle-alignment-v1.json
  - docs/agents/tasks/FTAI-20260723-rl-v2-historical-training-execution.md
  - docs/ai_platform/RL_V2_HISTORICAL_TRAINING_EXECUTION.md
search_first:
  - current develop and open PRs overlapping RL-v2 execution, lifecycle attribution, model, strategy, config or experimental-research ownership
optional_reads:
  - ai_platform/scripts/rl_v2_historical_training_execution_run_request.py
  - .github/workflows/ai-platform-rl-v2-historical-training-execution.yml
  - tests/ai_platform/test_rl_v2_historical_training_execution.py
---

# RL-v2 ROI Lifecycle Paired Attribution Execution

## Goal

Build a separately bounded, one-shot historical-development attribution path that executes only the
merged lifecycle-aligned RL-v2 variant and compares prospectively frozen lifecycle metrics against
immutable committed baseline evidence.

The baseline model/backtest must not be rerun. Infrastructure review must remain inert: no canonical
request, training, backtest, market-data access, or cache restore is allowed before a later separate
exact-one-file trigger PR.

## Frozen identities

Baseline:

- run `30022863894`, trigger PR `#218`, artifact
  `rl-v2-historical-training-execution-218`;
- artifact digest
  `sha256:5d74d87bf4408c7b51779cd9038d815c88d3f5cc193cd229b6757edf32112b55`;
- committed diagnosis
  `ai_platform/experimental_model_research/rl-v2-historical-evidence-diagnosis-v1.json`;
- strategy `AiDesiredPositionRLResearchStrategy`, SHA-256
  `9318a4d13937d9b572c4bcecfb56f999fd82d8309c6f898d0166c0c71dfd5c19`.

Variant:

- strategy `AiDesiredPositionRLLifecycleAlignedResearchStrategy`, SHA-256
  `366785129798d1332ce593f919c54aa23eefb2b15b2d850ab32d5c5cbdf0d5b7`;
- only semantic delta `ignore_roi_if_entry_signal=True`;
- model `DesiredPositionReinforcementLearner`, SHA-256
  `3cec25cc7b43e3214a8e22d153107307a7a7bfbfd48b6bf313ecb4624cb79d46`;
- config SHA-256
  `5adc805deadcfe6dc3c52d0745f62546952a96b38b3bd06bc28ac9987063f6de`;
- isolated identifier `rl-v2-roi-lifecycle-paired-attribution-v1`.

## Frozen geometry and attribution

- download `20250801-20260501`, end-exclusive;
- execution `20260301-20260501`, end-exclusive;
- semantic evidence `20260301-20260430`;
- train/backtest periods `90/61` days;
- `BTC/USDT`, `ETH/USDT`; `15m`, `1h`, `4h`;
- Kraken spot, fee `0.002`; PPO / `MlpPolicy`, seed `42`.

The window was already used to select the hypothesis. Any output is
`paired_historical_development_attribution`, `strict_oos=false`,
`protected_final_validation=false`, with profitability non-gating.

Immutable baseline primary values:

- ROI exits: `122`;
- ROI-to-same-pair-15m re-entries: `122`;
- immediate ROI/stop-loss boundaries: `131`;
- close-plus-reopen boundary fees: `52.582123 USDT`.

Directional support requires both fewer than `122` ROI-to-15m re-entries and boundary fees below
`52.582123 USDT`. Net PnL, profit factor, drawdown, trades, target-flat exits, and stop-loss exits are
descriptive only.

## Guarded infrastructure

PR #248 adds:

- an immutable contract;
- canonical request generator/validator with exact SHA-256 input binding;
- temporary config materialization changing only variant strategy, isolated identifier, and 90/61-day
  geometry;
- fail-closed pre-OOS coverage verification;
- an inert request-triggered workflow with exactly one variant backtest and no baseline command;
- deterministic raw-trade evidence extraction using the frozen baseline metric definitions;
- immutable artifact upload, tests, and documentation.

## Non-negotiable boundaries

- No baseline rerun or reuse of trigger #218.
- No run request, model execution, backtest, market-data access, or cache restore in PR #248.
- No PPO, reward, feature, pair, timeframe, fee, ROI, stop-loss, target-flat, cooldown, action-semantic,
  or threshold change.
- No consumed OOS `20260501-20260630`.
- No protected final holdout `20260801-20260930`.
- No strict-OOS, final-validation, ranking, promotion, profitability, superiority, dry-run, or live claim.
- Thresholds `0.006/-0.009` and Phase 6 `selected_model=null` remain unchanged.
- A later trigger must add exactly one canonical request file and be closed without merge.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-25T00:23:00+02:00
head: ee76c708091c00329b20f044e133072ecbc4ae6b
branch: develop
pr: 269
status: ready
context_routes:
  - docs/agents/tasks/FTAI-20260724-rl-v2-historical-evidence-diagnosis.md
  - docs/agents/tasks/FTAI-20260724-rl-v2-roi-lifecycle-alignment.md
  - docs/agents/tasks/FTAI-20260723-rl-v2-historical-training-execution.md
owned_paths:
  - docs/agents/tasks/FTAI-20260724-rl-v2-roi-lifecycle-paired-attribution-execution.md
  - docs/ai_platform/RL_V2_ROI_LIFECYCLE_PAIRED_ATTRIBUTION_EXECUTION.md
  - ai_platform/experimental_model_research/rl-v2-roi-lifecycle-paired-attribution-execution-contract-v1.json
  - ai_platform/scripts/rl_v2_roi_lifecycle_paired_attribution_run_request.py
  - ai_platform/scripts/rl_v2_roi_lifecycle_paired_attribution_evidence.py
  - tests/ai_platform/test_rl_v2_roi_lifecycle_paired_attribution.py
  - .github/workflows/ai-platform-rl-v2-roi-lifecycle-paired-attribution.yml
proven:
  - PR 248 merged the inert variant-only paired-attribution infrastructure as 746d52d4473f6043a530f79e376215ca8257e946 with all required CI green and zero execution.
  - Immutable baseline artifact rl-v2-historical-training-execution-218 remains bound to run 30022863894 and digest sha256:5d74d87bf4408c7b51779cd9038d815c88d3f5cc193cd229b6757edf32112b55; baseline rerun remains forbidden.
  - Trigger PR 265 added exactly the canonical request file and canonical request plus checkpoint validation passed in run 30112291721.
  - Both BTC/USDT and ETH/USDT data jobs in run 30112291721 failed at pre-OOS coverage verification and the lifecycle variant backtest job was skipped.
  - Baseline run 30022863894 data artifacts record first timestamp 2025-08-01T00:00:00Z and last timestamp exactly 2026-05-01T00:00:00Z for every declared pair and timeframe.
  - The paired verifier rejected last_date greater than or equal to stopdt while the completed baseline verifier accepted that exact stored boundary representation.
  - No baseline execution, variant backtest, consumed historical OOS access or protected final holdout access occurred in PR 265.
  - PR 265 was closed without merge after terminal failure evidence was recorded.
  - PR 269 accepts exactly the stored 2026-05-01T00:00:00Z boundary while continuing to reject any later timestamp.
  - PR 269 adds a dependency-light exact-boundary regression and permits a present trigger request only when it equals the generated canonical payload.
  - PR 269 changed no model, PPO, reward, feature, strategy, config, geometry, pair, timeframe, fee, threshold or evidence criterion.
  - Temporary patch, formatter, diagnostic and checkpoint workflows were removed from the PR 269 candidate.
  - AI Platform CI 1151, Freqtrade CI 1342 and zizmor 1272 passed on final PR 269 head bbf75230d292f1f95c540b61ab261cc2fdf54b73.
  - PR 269 was squash-merged to develop as ee76c708091c00329b20f044e133072ecbc4ae6b.
  - Two accidental placeholder-only commits created and immediately deleted the same noop file before PR 269; the resulting develop tree was restored before the repair branch was created.
derived:
  - The PR 265 failure was a timestamp-representation validation mismatch, not incomplete declared data coverage or model behavior evidence.
  - A fresh pull-request-opened event is required after the merged repair; PR 265 cannot be rerun or merged as an execution switch.
unknown:
  - Whether a fresh exact-one-file trigger completes the lifecycle variant execution.
  - Whether the variant reduces both frozen primary lifecycle metrics.
conflicts: []
first_failure:
  marker: RESOLVED
  evidence: PR 265 rejected the exact stored stop boundary before backtest; PR 269 aligned the verifier, added regression coverage and merged after terminal green CI.
rejected_hypotheses:
  - Treat the PR 265 data failure as model or strategy evidence.
  - Rerun or merge PR 265.
  - Rerun the immutable baseline.
  - Broaden the repair into PPO, reward, feature, strategy, pair, timeframe, fee, threshold or geometry changes.
  - Access consumed historical OOS or the protected final holdout.
  - Treat future paired development attribution as strict OOS, profitability, superiority or promotion evidence.
changed_paths:
  - ai_platform/scripts/rl_v2_roi_lifecycle_paired_attribution_run_request.py
  - tests/ai_platform/test_rl_v2_roi_lifecycle_paired_attribution.py
  - docs/agents/tasks/FTAI-20260724-rl-v2-roi-lifecycle-paired-attribution-execution.md
validation:
  - command: AI Platform RL-v2 ROI Lifecycle Paired Attribution 30112291721
    result: FAIL
    evidence: Request validation passed; both data jobs failed at exact-stop coverage validation and the backtest was skipped.
  - command: immutable baseline data artifact inspection
    result: PASS
    evidence: BTC and ETH coverage artifacts from run 30022863894 record complete declared coverage with the exact May 1 boundary timestamp and no later data.
  - command: AI Platform CI 30129827779 / run 1151
    result: PASS
    evidence: AI tests, compile, Ruff, formatter, codespell and JSON validations passed on the clean repair candidate.
  - command: Freqtrade CI 30129827803 / run 1342
    result: PASS
    evidence: Pre-commit and the full multi-platform core matrix, including coverage, smoke checks, Ruff, formatter and mypy, passed.
  - command: GitHub Actions Security Analysis 30129827776 / run 1272
    result: PASS
    evidence: Required zizmor workflow security analysis passed on the clean repair candidate.
  - command: squash merge PR 269
    result: PASS
    evidence: GitHub merged the reviewed repair head to develop as ee76c708091c00329b20f044e133072ecbc4ae6b.
blockers: []
next_action: Generate the canonical request from repaired develop, open a fresh exact-one-file trigger PR, and close it without merge after terminal paired-attribution evidence is collected and recorded.
```
