---
task_id: FTAI-20260724-rl-v2-roi-lifecycle-paired-attribution-execution
status: active
branch: feat/rl-v2-roi-lifecycle-paired-attribution-infrastructure
base_branch: develop
created: 2026-07-24
updated: 2026-07-24
related_pr: "248"
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
updated_at: 2026-07-24T11:40:00+02:00
head: f0e08db42550155b43f9a95dc2c1f7a022d61b85
branch: feat/rl-v2-roi-lifecycle-paired-attribution-infrastructure
pr: 248
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
  - PR #218 produced immutable baseline artifact rl-v2-historical-training-execution-218 and was closed without merge.
  - PR #237 bound baseline accounting and lifecycle metrics to artifact digest sha256:5d74d87bf4408c7b51779cd9038d815c88d3f5cc193cd229b6757edf32112b55.
  - PR #240 implemented the sole lifecycle delta and merged as 09044f824ea102955147900f3d6d5e8f83929c0a after full repository CI.
  - PR #246 declared this variant-only paired attribution task and merged as d26f2221107bb2c0a95753cb2d8ea4bacf3a65f9.
  - Contract v1 freezes immutable baseline identity, exact variant/model/config hashes, geometry, attribution definitions, isolation, and authorization.
  - The canonical request binds contract, diagnosis, variant declaration, config, model, variant strategy, validator, evidence extractor, and workflow hashes.
  - Runtime materialization replaces only strategy and FreqAI identifier and adds only train_period_days=90 and backtest_period_days=61.
  - The workflow is path-triggered by a future request, enforces an exact-one-file PR, and contains exactly one variant backtesting command with no baseline execution.
  - Data handling reuses only the exact verified pre-OOS cache namespace and re-verifies pair and combined coverage before execution.
  - The extractor validates strategy identity, isolated identifier, lifecycle flag, ROI schedule, hard stop-loss, long-only mode, timerange, and trade accounting.
  - Primary evidence definitions match the committed diagnosis: ROI-to-15m re-entry count and immediate external-boundary fees; profitability remains non-gating.
  - No canonical request exists and PR #248 has not trained, backtested, restored caches, or accessed market data.
  - Consumed OOS and final holdout remain forbidden; thresholds stay 0.006/-0.009 and Phase 6 selected_model remains null.
derived:
  - A variant-only run plus immutable committed baseline values permits mechanistic attribution without rerunning baseline.
  - The isolated identifier prevents model-artifact collision while preserving all model semantics.
  - Churn attribution and profitability remain separate conclusions.
unknown:
  - Whether PR #248 passes targeted tests, Ruff, workflow lint, zizmor, and full repository CI without repair.
  - Whether the later variant run reduces both frozen primary metrics.
conflicts: []
first_failure:
  marker: unresolved_paired_lifecycle_attribution
  evidence: The variant is implemented but has not been executed; its paired mechanistic effect remains unknown.
rejected_hypotheses:
  - Rerun baseline training or backtest.
  - Reuse completed trigger #218.
  - Add a request file or execute infrastructure during PR #248.
  - Combine lifecycle alignment with any other tuning.
  - Use PnL as the primary criterion.
  - Use consumed OOS or protected final holdout.
  - Label paired development evidence strict OOS, final validation, or promotion evidence.
changed_paths:
  - docs/agents/tasks/FTAI-20260724-rl-v2-roi-lifecycle-paired-attribution-execution.md
  - docs/ai_platform/RL_V2_ROI_LIFECYCLE_PAIRED_ATTRIBUTION_EXECUTION.md
  - ai_platform/experimental_model_research/rl-v2-roi-lifecycle-paired-attribution-execution-contract-v1.json
  - ai_platform/scripts/rl_v2_roi_lifecycle_paired_attribution_run_request.py
  - ai_platform/scripts/rl_v2_roi_lifecycle_paired_attribution_evidence.py
  - tests/ai_platform/test_rl_v2_roi_lifecycle_paired_attribution.py
  - .github/workflows/ai-platform-rl-v2-roi-lifecycle-paired-attribution.yml
validation:
  - command: PR #248 static infrastructure source inspection
    result: PASS
    evidence: Exact owned paths are used, the request path is absent, the workflow contains one variant backtest and no baseline command, and frozen identities are contract-bound.
  - command: synthetic evidence fixture accounting review
    result: PASS
    evidence: Test trades reconcile gross price movement less entry and exit fees to profit_abs and exercise both frozen primary mechanisms.
blockers: []
next_action: Run targeted tests, Ruff/format, checkpoint validation, actionlint, zizmor and repository CI on PR #248; repair only bounded infrastructure defects, then merge without adding a request or executing model/data paths.
```
