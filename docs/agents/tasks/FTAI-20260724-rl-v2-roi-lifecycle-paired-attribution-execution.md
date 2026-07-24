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
updated_at: 2026-07-24T15:45:00+02:00
head: ce492702825b4fa68347a675768a4fda6b07d3dc
branch: feat/rl-v2-roi-lifecycle-paired-attribution-infrastructure
pr: 248
status: blocked
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
  - PR #218 produced immutable baseline artifact rl-v2-historical-training-execution-218 and was closed without merge; baseline rerun remains forbidden.
  - PR #237 bound baseline accounting and lifecycle metrics to artifact digest sha256:5d74d87bf4408c7b51779cd9038d815c88d3f5cc193cd229b6757edf32112b55.
  - PR #240 implemented the sole lifecycle delta ignore_roi_if_entry_signal=True and merged as 09044f824ea102955147900f3d6d5e8f83929c0a.
  - PR #246 declared this variant-only paired attribution task and merged as d26f2221107bb2c0a95753cb2d8ea4bacf3a65f9.
  - PR #248 contains exactly seven owned infrastructure paths and no canonical run-request file.
  - Contract v1 freezes baseline identity, variant/model/config hashes, geometry, attribution definitions, isolation, authorization, and zero baseline executions.
  - The workflow is inert until a future exact-one-file trigger and contains exactly one variant backtesting command with no baseline execution command.
  - Initial PR #248 AI Platform compile and targeted tests passed before Ruff stopped that run.
  - Exact Ruff 0.15.21 diagnosis on original head 6e00a17e8783e978f51fe7efe5823efc27ed3bd9 found centralized _validate_contract C901 plus formatting drift in three new Python files.
  - Diagnostic PR #251 was based on the exact #248 head, performed no model or data execution, and was closed without merge.
  - Guarded repair workflow verified the unchanged #248 head, applied canonical Ruff formatting plus a localized C901 waiver, passed exact Ruff check and format, and pushed ce492702825b4fa68347a675768a4fda6b07d3dc.
  - Standard PR workflows on ce492702825b4fa68347a675768a4fda6b07d3dc concluded action_required and created zero jobs.
  - Current develop is 902fee5e6f5654b2a8989a4861d729a77fe19747; #248 is eight commits ahead and eight commits behind its merge base d26f2221107bb2c0a95753cb2d8ea4bacf3a65f9.
  - No canonical request, training, backtest, cache restore, market-data access, consumed OOS access, or protected final-holdout access occurred in PR #248 or #251.
  - Frozen thresholds remain 0.006/-0.009 and Phase 6 selected_model remains null.
derived:
  - The action_required runs with zero jobs followed a workflow-authored repair push, so an owner-authored rebased or checkpoint commit is required to obtain standard PR CI evidence.
  - The feature branch must be integrated with current develop before merge while preserving the seven-path infrastructure scope and frozen semantics.
  - No variant trigger may be created until the infrastructure PR is current with develop, fully validated, and merged.
unknown:
  - Whether the eight current develop commits conflict with any #248 owned path.
  - Whether all standard CI jobs pass after an owner-authored current-develop integration commit.
  - Whether the later one-shot variant run reduces both frozen primary lifecycle metrics.
conflicts: []
first_failure:
  marker: pr248_checks_action_required_after_automated_repair_push
  evidence: On head ce492702825b4fa68347a675768a4fda6b07d3dc AI Platform CI, Freqtrade CI, zizmor, and Pre-commit Types all ended action_required with no jobs; PR #248 is also eight commits behind current develop.
rejected_hypotheses:
  - Merge PR #248 without terminal green standard CI.
  - Treat action_required as a code or test failure.
  - Add the canonical run request before infrastructure merge.
  - Rerun baseline training or backtest.
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
  - command: PR #248 initial AI Platform compile and targeted tests
    result: PASS
    evidence: Compile and project tests completed successfully before the Ruff step failed on original head 6e00a17e8783e978f51fe7efe5823efc27ed3bd9.
  - command: Ruff 0.15.21 exact diagnostic on original #248 Python paths
    result: FAIL
    evidence: One C901 marker on centralized _validate_contract and canonical formatting drift in the validator, evidence extractor, and targeted test.
  - command: guarded PR #248 Ruff repair workflow
    result: PASS
    evidence: The workflow verified exact target head, applied the bounded repair, and passed Ruff check plus Ruff format before pushing ce492702825b4fa68347a675768a4fda6b07d3dc.
  - command: standard PR workflows on ce492702825b4fa68347a675768a4fda6b07d3dc
    result: BLOCKED
    evidence: AI Platform CI, Freqtrade CI, zizmor, and Pre-commit Types concluded action_required with zero jobs.
  - command: compare current develop with PR #248 branch
    result: PASS
    evidence: develop 902fee5e6f5654b2a8989a4861d729a77fe19747 and #248 are diverged; branch is ahead by eight and behind by eight commits.
blockers:
  - Standard PR CI did not run on the repaired head because every workflow concluded action_required with zero jobs.
  - PR #248 is eight commits behind current develop and must be integrated before merge.
next_action: Rebase or merge current develop 902fee5e6f5654b2a8989a4861d729a77fe19747 into PR #248 with an owner-authored commit, preserve only the seven owned infrastructure paths and frozen semantics, validate the checkpoint and full standard CI, then merge only after every required check is green without adding a run request or executing model/data paths.
```
