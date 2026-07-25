---
task_id: FTAI-20260724-rl-v2-roi-lifecycle-paired-attribution-execution
status: done
branch: develop
base_branch: develop
created: 2026-07-24
updated: 2026-07-25
related_pr: "272"
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
updated_at: 2026-07-25T09:27:17+02:00
head: 46618f215eba39da682b94f230387666b4799a06
branch: develop
pr: 272
status: done
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
  - PR 248 merged the inert variant-only paired-attribution infrastructure as 746d52d4473f6043a530f79e376215ca8257e946 with zero execution.
  - Immutable baseline artifact rl-v2-historical-training-execution-218 remains bound to run 30022863894 and digest sha256:5d74d87bf4408c7b51779cd9038d815c88d3f5cc193cd229b6757edf32112b55; baseline rerun remained forbidden.
  - Trigger PR 265 failed only at the exact stored stop-boundary representation and was closed without merge before variant execution.
  - PR 269 aligned the verifier with the stored 2026-05-01T00:00:00Z boundary, retained rejection of later data, passed required CI, and merged as ee76c708091c00329b20f044e133072ecbc4ae6b.
  - PR 270 durably synchronized the repaired checkpoint and merged as 46618f215eba39da682b94f230387666b4799a06.
  - PR 271 placed a canonical payload outside the required run-requests path and was closed without merge or dedicated execution.
  - PR 272 added exactly one canonical request file at the required run-requests path on head ce83a3e52ab6bc8676072522e266dcf50bd692e7.
  - AI Platform CI 1154, Freqtrade CI 1347 and zizmor 1277 passed on PR 272.
  - Paired-attribution run 30131273189 passed request validation, both pre-OOS data jobs and exactly one lifecycle-aligned variant training/backtest.
  - Combined coverage spans 2025-08-01T00:00:00Z through exactly 2026-05-01T00:00:00Z for BTC/USDT and ETH/USDT on 15m, 1h and 4h; consumed historical OOS and protected final holdout access are false.
  - Immutable artifact rl-v2-roi-lifecycle-paired-attribution-272 has digest sha256:11e9d9a8e5f8e65474406524445c7b04fe3d9af5afa6d137847c913f8e66ae04 and is bound to run 30131273189 and execution head ce83a3e52ab6bc8676072522e266dcf50bd692e7.
  - Evidence metadata records one executed Freqtrade backtesting command, lifecycle-aligned strategy only, baseline_rerun=false, automatic_ranking=false and automatic_promotion=false.
  - Variant ROI-to-same-pair-15m re-entries are 0 versus baseline 122, and immediate external-exit/re-entry boundaries are 0 versus baseline 131.
  - Variant boundary fees are 0.0 USDT versus baseline 52.582123 USDT; both prospectively frozen directional criteria are met.
  - Variant descriptive metrics are 45 trades, 11.806876 USDT net profit, 18.059698 USDT fees, profit factor 1.251195 and max drawdown 26.728284; profitability remains non-gating.
  - PR 272 was closed without merge after terminal evidence and artifact provenance were recorded.
derived:
  - The sole lifecycle semantic delta removed the prospectively defined immediate ROI-exit/re-entry mechanism in this reused historical-development window.
  - The result supports the frozen directional mechanism hypothesis only and does not establish strict-OOS generalization, final validation, superiority, ranking, promotion, dry-run or live readiness.
unknown: []
conflicts: []
first_failure:
  marker: RESOLVED
  evidence: The stop-boundary representation mismatch was repaired in PR 269; the fresh canonical PR 272 then completed all bounded data and variant execution stages.
rejected_hypotheses:
  - Treat the PR 265 pre-execution validation failure as model behavior evidence.
  - Rerun or merge any trigger request PR.
  - Rerun the immutable baseline.
  - Access consumed historical OOS or the protected final holdout.
  - Change PPO, reward, features, thresholds, geometry, model, strategy or config during attribution execution.
  - Treat the paired historical-development result as profitability, superiority, promotion or final-validation evidence.
changed_paths:
  - ai_platform/scripts/rl_v2_roi_lifecycle_paired_attribution_run_request.py
  - tests/ai_platform/test_rl_v2_roi_lifecycle_paired_attribution.py
  - docs/agents/tasks/FTAI-20260724-rl-v2-roi-lifecycle-paired-attribution-execution.md
validation:
  - command: AI Platform RL-v2 ROI Lifecycle Paired Attribution 30131273189
    result: PASS
    evidence: Request validation, both verified pre-OOS data jobs, exactly one lifecycle-aligned backtest, deterministic evidence extraction and immutable artifact upload succeeded.
  - command: local digest and artifact payload verification
    result: PASS
    evidence: Downloaded artifact digest equals sha256:11e9d9a8e5f8e65474406524445c7b04fe3d9af5afa6d137847c913f8e66ae04; paired-attribution, metadata and coverage payloads reconcile.
  - command: standard PR 272 CI
    result: PASS
    evidence: AI Platform CI 1154, Freqtrade CI 1347 and zizmor 1277 completed successfully.
  - command: close trigger PR 272 without merge
    result: PASS
    evidence: GitHub records PR 272 closed with merged=false after terminal evidence was posted.
blockers: []
next_action: Do not reopen this completed paired-attribution task; declare a separate bounded interpretation or next-experiment task only if it preserves the evidence classification, forbids baseline rerun and OOS or holdout access, and leaves Phase 6 selected_model=null.
```
