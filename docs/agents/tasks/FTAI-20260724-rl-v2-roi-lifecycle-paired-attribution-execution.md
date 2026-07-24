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
updated_at: 2026-07-24T19:09:44+02:00
head: 746d52d4473f6043a530f79e376215ca8257e946
branch: develop
pr: 263
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
  - PR #218 produced immutable baseline artifact rl-v2-historical-training-execution-218 with digest sha256:5d74d87bf4408c7b51779cd9038d815c88d3f5cc193cd229b6757edf32112b55; baseline rerun remains forbidden.
  - PR #240 implemented the sole semantic delta ignore_roi_if_entry_signal=True and merged as 09044f824ea102955147900f3d6d5e8f83929c0a.
  - PR #246 declared the variant-only paired attribution task and merged as d26f2221107bb2c0a95753cb2d8ea4bacf3a65f9.
  - PR #248 merged the seven-path inert infrastructure as 746d52d4473f6043a530f79e376215ca8257e946 with no canonical request or execution.
  - Final PR #248 AI Platform CI 30106646592, Freqtrade CI 30106646728, zizmor 30106646266, Portal Web CI 30106646431, and Portal Universal E2E 30106646632 passed.
  - The merged workflow accepts only an opened exact-one-file request PR, executes exactly one variant backtest, and contains zero baseline execution commands.
  - Canonical text hashing normalizes checkout CRLF to LF while remaining sensitive to substantive content changes; Windows and Linux regression validation passed.
  - The merged contract freezes baseline identity, model/config/strategy hashes, geometry, attribution, isolation, authorization, and baseline_executions=0.
  - Merged code generated the canonical request in AI Platform CI run 30111506773; artifact digest is sha256:11cd3b2401045537c5dc02031f0510ceac472f24ec5b6175c4a7bbee5665f680.
  - Temporary generator PR #262 changed only CI generation plumbing, performed no model or data execution, and closed without merge.
  - Trigger PR #263 added exactly the canonical request file; its exact-one-file scope validation passed.
  - Trigger run 30111679825 stopped at checkpoint validation before Python setup, request validation, cache restore, market-data access, training, or backtest.
  - Data preparation and variant backtest jobs in run 30111679825 were skipped, so baseline executions remained zero and no OOS or holdout was accessed.
  - Trigger PR #263 closed without merge after the safe pre-runtime failure.
  - Current develop is exactly infrastructure merge 746d52d4473f6043a530f79e376215ca8257e946.
  - Frozen thresholds remain 0.006/-0.009 and Phase 6 selected_model remains null.
derived:
  - The failed trigger was caused by stale durable state: the merged checkpoint still described PR #248 as awaiting final CI and exceeded the proven compactness limit of 16 items.
  - The canonical request remains valid after this task-document-only checkpoint repair because the task path is not one of the request hash inputs.
  - A fresh PR-opened event is required after checkpoint repair; rerunning or synchronizing closed PR #263 cannot authorize execution.
unknown:
  - Whether verified pre-OOS caches are available and complete for both declared pairs and all three timeframes.
  - Whether the one-shot lifecycle variant execution completes successfully.
  - Whether the variant reduces both frozen primary lifecycle metrics.
conflicts: []
first_failure:
  marker: pr263_checkpoint_validation_before_runtime
  evidence: Run 30111679825 passed exact-one-file scope but failed tools/agents/checkpoint.py on the stale merged checkpoint; Python setup, data, cache, training, and backtest never ran.
rejected_hypotheses:
  - Rerun failed PR #263 without repairing the merged checkpoint.
  - Add checkpoint changes to an exact-one-file trigger PR.
  - Merge any trigger request into develop.
  - Rerun baseline training or backtest.
  - Use consumed historical OOS or protected final holdout.
  - Change PPO, reward, features, thresholds, geometry, model, strategy, or config.
changed_paths:
  - docs/agents/tasks/FTAI-20260724-rl-v2-roi-lifecycle-paired-attribution-execution.md
validation:
  - command: final standard CI on PR #248 head 329226dbcabac98e63a7e172810e9dc33b19d8d2
    result: PASS
    evidence: All required standard workflows reached terminal success before merge.
  - command: compare develop with merge commit 746d52d4473f6043a530f79e376215ca8257e946
    result: PASS
    evidence: Compare was identical after PR #248 merged.
  - command: generate canonical request with merged validator --print-canonical
    result: PASS
    evidence: AI Platform CI run 30111506773 uploaded canonical request artifact digest sha256:11cd3b2401045537c5dc02031f0510ceac472f24ec5b6175c4a7bbee5665f680.
  - command: compare PR #263 trigger branch with develop
    result: PASS
    evidence: The branch was one commit ahead, zero behind, and added exactly the canonical request file.
  - command: trigger run 30111679825 checkpoint validation
    result: FAIL
    evidence: Exact-one-file scope passed, then the stale checkpoint failed before any runtime or data step.
blockers: []
next_action: Merge this task-document-only checkpoint repair, then open a fresh exact-one-file canonical request PR against the repaired develop and close it without merge after terminal paired-attribution evidence is collected.
```
