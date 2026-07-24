---
task_id: FTAI-20260724-rl-v2-roi-lifecycle-paired-attribution-execution
status: active
branch: docs/rl-v2-roi-lifecycle-paired-attribution-declaration
base_branch: develop
created: 2026-07-24
updated: 2026-07-24
related_pr: "246"
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
merged lifecycle-aligned RL-v2 variant and compares its mechanistic lifecycle metrics against the
already completed immutable baseline evidence.

The baseline model/backtest must not be rerun. The completed `#218` trigger path must not be reused.
The infrastructure implementation PR must remain inert and may not train, backtest, download market
data, or add a canonical run request.

## Frozen identities

Baseline:

- run `30022863894`, trigger PR `#218`, artifact
  `rl-v2-historical-training-execution-218`;
- artifact digest
  `sha256:5d74d87bf4408c7b51779cd9038d815c88d3f5cc193cd229b6757edf32112b55`;
- committed baseline metrics:
  `ai_platform/experimental_model_research/rl-v2-historical-evidence-diagnosis-v1.json`;
- strategy `AiDesiredPositionRLResearchStrategy`, SHA-256
  `9318a4d13937d9b572c4bcecfb56f999fd82d8309c6f898d0166c0c71dfd5c19`.

Variant:

- strategy `AiDesiredPositionRLLifecycleAlignedResearchStrategy`, SHA-256
  `366785129798d1332ce593f919c54aa23eefb2b15b2d850ab32d5c5cbdf0d5b7`;
- only semantic delta `ignore_roi_if_entry_signal=True`;
- model `DesiredPositionReinforcementLearner`, SHA-256
  `3cec25cc7b43e3214a8e22d153107307a7a7bfbfd48b6bf313ecb4624cb79d46`;
- config `ai_platform/configs/rl_v2_training_research.json`, SHA-256
  `5adc805deadcfe6dc3c52d0745f62546952a96b38b3bd06bc28ac9987063f6de`;
- isolated runtime identifier `rl-v2-roi-lifecycle-paired-attribution-v1`.

## Frozen geometry

- download `20250801-20260501`, end-exclusive;
- train period `90` days;
- execution `20260301-20260501`, end-exclusive;
- semantic evidence window `20260301-20260430`;
- backtest period `61` days;
- `BTC/USDT`, `ETH/USDT`;
- `15m`, `1h`, `4h`;
- Kraken spot, fee `0.002`;
- PPO / `MlpPolicy`, seed `42`.

The March-April window was already used to select the lifecycle hypothesis. The result is therefore
`paired_historical_development_attribution`, never strict OOS, fresh validation, or protected final
validation.

## Frozen attribution semantics

The baseline must be read only from committed diagnosis values bound to the immutable artifact digest.
It must not be retrained or rerun.

Baseline primary values:

- ROI exits: `122`;
- ROI exits followed by same-pair re-entry after exactly 15 minutes: `122`;
- immediate ROI/stop-loss external-exit plus 15-minute re-entry boundaries: `131`;
- close-plus-reopen fees at those boundaries: `52.582123 USDT`.

The lifecycle hypothesis is directionally supported only if the variant produces both:

1. fewer than `122` ROI exits followed by same-pair 15-minute re-entry;
2. less than `52.582123 USDT` immediate external-exit/re-entry boundary fees.

These are mechanistic criteria, not profitability gates. Net PnL, profit factor, trades, drawdown,
target-flat exits and stop-losses are secondary descriptive evidence. Negative, neutral, zero-trade,
or failed execution remains valid evidence.

## Allowed implementation scope

- immutable execution contract;
- canonical request generator and validator;
- inert request-triggered workflow;
- runtime materialization changing only the isolated identifier and frozen 90/61-day geometry;
- exact baseline, model, config, strategy, validator and workflow hash binding;
- fail-closed pre-OOS coverage checks;
- exactly one later variant-only historical training/backtest;
- deterministic raw-trade attribution extraction;
- immutable artifact upload, tests and documentation.

## Non-negotiable boundaries

- No baseline retraining or rerun.
- No run request, training, `.learn()`, backtest, or market-data access in declaration or infrastructure
  implementation PRs.
- No PPO, policy, reward, feature, pair, timeframe, fee, ROI schedule, stop-loss, action semantics,
  threshold, target-flat or cooldown change.
- No consumed OOS `20260501-20260630` access.
- No protected final holdout `20260801-20260930` access.
- No strict-OOS, final-validation, ranking, promotion, profitability, superiority, dry-run or live claim.
- Thresholds `0.006/-0.009` and Phase 6 `selected_model=null` remain unchanged.
- Any later trigger must be a separate exact-one-file PR closed without merge.

## Required proofs

1. Exact variant identity and single semantic delta remain hash-bound.
2. The workflow contains no baseline model/backtest command.
3. Infrastructure remains inert until a later canonical one-file trigger.
4. Evidence is labeled paired historical-development attribution and separates mechanism from profit.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-24T11:20:00+02:00
head: 730c9b0b0981d84c12889ade532fa52324bf39aa
branch: docs/rl-v2-roi-lifecycle-paired-attribution-declaration
pr: 246
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
  - PR #218 produced immutable baseline artifact rl-v2-historical-training-execution-218 from run 30022863894 and was closed without merge.
  - PR #237 merged baseline diagnosis 49167cdf9ab6fd126de72613101c35fef6cc07e2 bound to artifact digest sha256:5d74d87bf4408c7b51779cd9038d815c88d3f5cc193cd229b6757edf32112b55.
  - PR #238 declared the sole lifecycle delta and merged as 9d5cc48db3aaa72995b10214642be6064ad5e00e.
  - PR #240 implemented the variant and merged as 09044f824ea102955147900f3d6d5e8f83929c0a after full repository CI.
  - PR #245 closed implementation as 353e215b1cc694c9b982f1a214b6f5cc96003690 without model or market-data execution.
  - Variant strategy SHA-256 is 366785129798d1332ce593f919c54aa23eefb2b15b2d850ab32d5c5cbdf0d5b7 and baseline remains unchanged.
  - Baseline primary metrics are 122 ROI exits, 122 ROI-to-15m re-entries, 131 immediate ROI/stop-loss boundaries and 52.582123 USDT boundary fees.
  - Geometry remains download 20250801-20260501, execution 20260301-20260501, 90/61 days, BTC/USDT plus ETH/USDT, 15m/1h/4h, Kraken spot and fee 0.002.
  - March-April is development attribution only and cannot become strict OOS or final validation.
  - Consumed OOS and protected final holdout remain forbidden; thresholds stay 0.006/-0.009 and Phase 6 selected_model remains null.
derived:
  - A variant-only run plus immutable committed baseline values enables mechanistic paired attribution without rerunning baseline.
  - A separate runtime identifier prevents model-artifact collision without changing model semantics.
  - Churn attribution and profitability must remain separate conclusions.
unknown:
  - Whether the lifecycle variant reduces both frozen primary churn metrics.
conflicts: []
first_failure:
  marker: unresolved_paired_lifecycle_attribution
  evidence: The variant is implemented but has not been historically executed; its effect relative to the immutable baseline is unknown.
rejected_hypotheses:
  - Rerun baseline training or backtest.
  - Reuse completed trigger #218.
  - Combine lifecycle alignment with any other tuning.
  - Use PnL as the primary success criterion.
  - Use consumed OOS or protected final holdout.
  - Label paired development evidence strict OOS, final validation or promotion evidence.
changed_paths:
  - docs/agents/tasks/FTAI-20260724-rl-v2-roi-lifecycle-paired-attribution-execution.md
validation:
  - command: live develop and open-PR preflight
    result: PASS
    evidence: Current develop contains the complete diagnosis-to-variant chain and no open PR overlaps paired attribution ownership.
  - command: diagnosis-to-variant traceability inspection
    result: PASS
    evidence: Baseline artifact digest, committed metrics, variant strategy hash and sole lifecycle delta are repository-bound.
blockers: []
next_action: Merge declaration PR #246, then implement guarded paired-attribution execution infrastructure in a separate PR without adding a run request or executing training, backtest or market-data access.
```
