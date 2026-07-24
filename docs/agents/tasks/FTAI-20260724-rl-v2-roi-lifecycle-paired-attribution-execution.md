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
updated_at: 2026-07-24T17:43:57+02:00
head: fce3b60be82843a0411825486f3e61a24d1138eb
branch: feat/rl-v2-roi-lifecycle-paired-attribution-infrastructure
pr: 248
status: validating
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
  - The workflow remains inert until a future exact-one-file trigger and contains exactly one variant backtesting command with no baseline execution command.
  - Guarded Ruff repair produced ce492702825b4fa68347a675768a4fda6b07d3dc after exact Ruff 0.15.21 check and format passed.
  - Pre-commit diagnostic run 30102235674 identified mypy no-redef in _collect_keys; guarded repair run 30102941491 renamed only the list accumulator to list_keys and passed full pre-commit.
  - Owner-authored checkpoint head aa68b358537735977b74f717e90f9f70f9abc6b4 passed AI Platform CI, Portal Web CI, Portal Universal E2E, zizmor, pre-commit, documentation, coverage, Ubuntu 3.11/3.12/3.13/3.14, and macOS 3.13 jobs.
  - Windows 2025/Python 3.13 failed twice on the same aa68b358537735977b74f717e90f9f70f9abc6b4 merge ref, so the failure was not treated as a runner flake.
  - Read-only diagnostic run 30105449519 reproduced exactly five owned tests failing because Windows checkout converted the immutable JSON config from LF to CRLF, changing the working-tree byte hash from expected 5adc805deadcfe6dc3c52d0745f62546952a96b38b3bd06bc28ac9987063f6de to 4e436cdd8a09ca5e268372e982d042a999ca757d643cb2625bfb7348dfb991ea.
  - Diagnostic artifact rl-v2-windows-test-diagnostic-248 had digest sha256:d39e36bc77071e8670ac101dacc80ff20a62123aed5784312f318dafea914a00 and contained 4979 passing tests, 24 skips, and only the five cross-platform hash failures.
  - Guarded repair run 30106178646 normalized only CRLF to canonical LF before hashing text inputs, added a regression test proving LF/CRLF equivalence and substantive-content distinction, passed targeted Windows tests, targeted Linux tests, full pre-commit, bounded staged-scope verification, and pushed fce3b60be82843a0411825486f3e61a24d1138eb.
  - The Windows hash repair preserves all frozen expected digests and contract identities; it changes checkout portability only, not config, model, strategy, geometry, attribution, authorization, or experiment semantics.
  - All temporary diagnostic and repair workflows are absent from repaired head fce3b60be82843a0411825486f3e61a24d1138eb.
  - Current develop ee6c8c36272e5b565515692ddb1c834c4ff6a88c is the merge base of repaired head fce3b60be82843a0411825486f3e61a24d1138eb; compare reports behind_by=0 and exactly the seven owned infrastructure paths.
  - No current open PR other than #248 overlaps RL-v2 execution, lifecycle attribution, model, strategy, config, or experimental-research ownership.
  - Standard workflows create normal runs and jobs rather than action_required runs with zero jobs.
  - No canonical request, training, backtest, cache restore, market-data access, consumed OOS access, or protected final-holdout access occurred during diagnosis, repair, or integration.
  - Frozen thresholds remain 0.006/-0.009 and Phase 6 selected_model remains null.
derived:
  - The original action_required, behind-develop, Ruff, pre-commit mypy, and Windows checkout-EOL hash blockers are resolved.
  - Canonical LF hashing is invariant to Git checkout EOL conversion while remaining sensitive to substantive text changes.
  - The current-develop integration preserves the seven-path infrastructure scope and frozen semantics.
  - No variant trigger may be created until the infrastructure PR is fully validated and merged.
unknown:
  - Whether every standard CI job passes on the owner-authored checkpoint head after the Windows portability repair.
  - Whether the later one-shot variant run reduces both frozen primary lifecycle metrics.
conflicts: []
first_failure:
  marker: pr248_final_standard_ci_pending_after_windows_hash_repair
  evidence: Guarded repair run 30106178646 passed Windows targeted tests and full pre-commit, but standard PR CI has not yet reached terminal green on the owner-authored checkpoint head.
rejected_hypotheses:
  - Merge PR #248 without terminal green standard CI.
  - Treat the repeated Windows failure as a transient runner flake.
  - Change the frozen config content or expected SHA-256 digest.
  - Add a repository-wide JSON EOL policy outside the seven owned paths.
  - Treat the earlier action_required state as a code or test failure.
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
  - command: pytest --random-order --durations 20 -n auto on Windows 2025/Python 3.13 before repair
    result: FAIL
    evidence: Diagnostic run 30105449519 produced five owned failures, all caused by config working-tree CRLF hash drift; 4979 tests passed and 24 skipped.
  - command: targeted paired-attribution tests on Windows 2025/Python 3.13 after canonical text hash repair
    result: PASS
    evidence: validate-windows-repair job in guarded run 30106178646 completed successfully.
  - command: targeted paired-attribution tests plus pre-commit run --all-files --show-diff-on-failure --verbose
    result: PASS
    evidence: commit-repair job in guarded run 30106178646 completed successfully before bounded commit and push.
  - command: compare current develop with repaired PR #248 head
    result: PASS
    evidence: develop ee6c8c36272e5b565515692ddb1c834c4ff6a88c is the merge base, branch behind_by=0, and the compare contains exactly seven owned paths.
  - command: verify temporary diagnostic and repair workflow removal
    result: PASS
    evidence: Net compare contains no temporary workflow path and only the seven owned infrastructure paths.
blockers:
  - Full standard CI on the owner-authored checkpoint head is not yet terminal green.
next_action: Validate the checkpoint and full standard CI on the new checkpoint head; if every required check is green and the compare still contains exactly the seven owned infrastructure paths, merge PR #248 without adding a run request or executing any model or data path; otherwise repair only the first bounded infrastructure failure.
```
