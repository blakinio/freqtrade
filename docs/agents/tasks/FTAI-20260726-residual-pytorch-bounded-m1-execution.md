---
task_id: FTAI-20260726-residual-pytorch-bounded-m1-execution
status: active
branch: run/residual-pytorch-bounded-m1-execution-v10
base_branch: develop
created: 2026-07-26
updated: 2026-07-27
related_pr: 517
owned_paths:
  - docs/agents/tasks/FTAI-20260726-residual-pytorch-bounded-m1-execution.md
  - docs/ai_platform/RESIDUAL_PYTORCH_BOUNDED_M1_EXECUTION.md
  - ai_platform/experimental_model_research/residual-pytorch-bounded-m1-execution-contract-v1.json
  - ai_platform/scripts/residual_pytorch_bounded_m1_execution.py
  - ai_platform/scripts/residual_pytorch_bounded_m1_run_request.py
  - ai_platform/scripts/run_experiment.py
  - ai_platform/configs/freqai-residual-pytorch-m1-data-audit.example.json
  - ai_platform/configs/freqai-residual-pytorch-m1-lightgbm.example.json
  - ai_platform/configs/freqai-residual-pytorch-m1-seeded-mlp.example.json
  - ai_platform/configs/freqai-residual-pytorch-m1-residual-mlp.example.json
  - ai_platform/experiments/residual-pytorch-m1-data-audit-v1.json
  - ai_platform/experiments/residual-pytorch-m1-lightgbm-v1.json
  - ai_platform/experiments/residual-pytorch-m1-seeded-mlp-v1.json
  - ai_platform/experiments/residual-pytorch-m1-residual-mlp-v1.json
  - ai_platform/freqaimodels/residual_pytorch_m1_instrumentation.py
  - ai_platform/freqaimodels/ResidualPyTorchM1DataAuditRegressor.py
  - ai_platform/freqaimodels/M1LightGBMRegressor.py
  - ai_platform/freqaimodels/M1SeededPyTorchMLPRegressor.py
  - ai_platform/freqaimodels/M1ResidualPyTorchRegressor.py
  - ai_platform/experimental_model_research/run-requests/residual-pytorch-bounded-m1-execution-v1.json
  - tests/ai_platform/test_run_experiment.py
  - tests/ai_platform/test_residual_pytorch_bounded_m1_execution.py
  - tests/ai_platform/test_residual_pytorch_bounded_m1_failure_artifact.py
  - .github/workflows/residual-pytorch-bounded-m1-execution.yml
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260726-residual-pytorch-data-target-audit.md
  - docs/ai_platform/EXPERIMENTAL_MODEL_RESEARCH.md
  - docs/ai_platform/RESIDUAL_PYTORCH_RESEARCH_ARCHITECTURE.md
  - docs/ai_platform/RESIDUAL_PYTORCH_DATA_TARGET_AUDIT.md
  - docs/ai_platform/EXPERIMENTAL_MODEL_HISTORICAL_EXECUTION_PREFLIGHT.md
  - docs/ai_platform/EXPERIMENTAL_MODEL_HISTORICAL_BACKTEST_EXECUTION.md
search_first:
  - current develop and open ownership on residual PyTorch P3
  - existing guarded historical execution and market-data cache contracts
context_routes:
  - ai_platform/configs/freqai-residual-pytorch-research.example.json
  - ai_platform/experiments/residual-pytorch-research-v1.json
  - ai_platform/strategies/AiFrozenCandidateStrategy.py
  - ai_platform/scripts/run_experiment.py
---

# Residual PyTorch P3 bounded M1 execution

## Goal

Build and use one fail-closed, one-shot historical-development execution path that compares `LightGBMRegressor`, `SeededPyTorchMLPRegressor` and `ResidualPyTorchRegressor` on exactly the same frozen feature, target, strategy, pair, timeframe, fee, training and evaluation geometry.

## Authorization and boundaries

The user explicitly authorized autonomous continuation into P3 on 2026-07-26. This authorization is limited to the bounded research package below.

The package must:

- use Kraken spot `BTC/USDT` and `ETH/USDT` at `15m`, `1h` and `4h`;
- use `AiFrozenCandidateStrategy`, target `&-future_return`, future offsets `t+1` through `t+12`, entry threshold `0.006`, exit threshold `-0.009` and fee ratio `0.002` unchanged;
- use one frozen 90-day training window ending before March 2026;
- use historical-development prediction/evaluation coverage `20260301-20260430`, encoded as Freqtrade timerange `1772323200-1777593599` so its inclusive stop is exactly `2026-04-30T23:59:59Z`;
- use download coverage `1754006400-1777593599`, ending one second before the exclusive `2026-05-01T00:00:00Z` boundary, and never read consumed May-June historical OOS;
- use seed `42` for every stochastic model or library setting that exposes a seed;
- execute at most once per declared model after a separate exact-one-file run-request PR;
- measure the exact FreqAI-expanded feature count plus historical feature NaN, outlier and label distributions before model execution and fail closed if this evidence is absent or non-finite;
- label all outputs historical development evidence only.

The package must not:

- access consumed historical OOS `20260501-20260630` or the protected final holdout `20260801-20260930`;
- change features, targets, strategy thresholds, pair universe, timeframes, fees or temporal geometry between models;
- tune from execution outcomes, run Hyperopt, add liquidation features or alter model architecture defaults;
- change completed Phase 6 candidates, policy, evidence or `selected_model = null`;
- select or promote a winner, deploy, trade live, or claim profitability, superiority or production readiness.

The infrastructure PR must not contain the canonical run-request file and must not execute market-data acquisition, training or backtesting. Real execution requires a later pull request adding exactly the canonical request path and must be closed without merge after terminal evidence collection.

## Required evidence

Before any model fit, the workflow must persist exact matrix dimensions, per-column finite/NaN coverage, declared outlier diagnostics and target distribution/edge-null counts for the authorized pre-May data only. Each model execution must persist hashes, config, manifest, strategy/model identity, runtime provenance, prediction diagnostics and trading-level development metrics. Cross-model presentation may be descriptive but must contain no winner-selection rule.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-27T20:47:33Z
head: d88cf99ea2453b00d4314d804a73ff0eb04bad3d
branch: run/residual-pytorch-bounded-m1-execution-v10
pr: 517
status: blocked
context_routes:
  - docs/agents/CONTEXT_HANDOFF.md
  - ai_platform/strategies/AiFrozenCandidateStrategy.py
  - ai_platform/experimental_model_research/residual-pytorch-bounded-m1-execution-contract-v1.json
  - .github/workflows/residual-pytorch-bounded-m1-execution.yml
owned_paths:
  - docs/agents/tasks/FTAI-20260726-residual-pytorch-bounded-m1-execution.md
proven:
  - Evidence-order correction PR 512 passed exact-head AI Platform CI 30298314438, Freqtrade CI 30298314378 and zizmor 30298314579, then squash-merged as c47679f75c2853ad8b145185afe9d2f9afcd5ce9.
  - Exact-one-file PR 517 used head d88cf99ea2453b00d4314d804a73ff0eb04bad3d and passed trigger-scope, active-checkpoint, canonical-request and frozen-infrastructure validation.
  - Guarded run 30299203871 completed both BTC/USDT and ETH/USDT pre-May Kraken acquisition, exact pair coverage verification and the combined pre-fit coverage check successfully.
  - Audit artifact residual-pytorch-bounded-m1-audit-517, artifact id 8667673779 and digest sha256:f02fa4e18350c4feb745ca80c105be1c4245f6a79af18d9a6359b8c0bf346575, preserved runtime/backtest.log before workflow validation.
  - The first BTC/USDT training attempt raised ValueError with message Expanded feature %-volume-change_gen_BTC/USDT_15m contains infinity.
  - The ETH/USDT training attempt independently raised ValueError with message Expanded feature %-volume-change_gen_ETH/USDT_15m contains infinity.
  - The matrix audit failed closed, all three frozen comparator executions were skipped, no consumed May-June historical OOS or protected holdout was used, and PR 517 was closed without merge.
derived:
  - The frozen strategy defines %-volume-change as dataframe["volume"].pct_change(); infinity is consistent with a zero prior-volume denominator, but the exact offending timestamps and counts were not persisted.
  - Contract v1 explicitly sets feature_changes_allowed to false, so sanitizing or replacing this feature cannot be performed under the existing authorization.
  - A repeat of the unchanged v1 request would reproduce the same fail-closed condition and would not be an authorized remediation.
unknown:
  - The exact expanded feature count and complete per-column NaN, non-finite, outlier and target distributions because the audit aborted on the first invalid expanded feature.
  - The exact rows, signs and frequencies of the infinite volume-change values for each pair.
  - Whether a separately authorized versioned remediation would pass the full matrix audit and allow the three comparator executions.
conflicts:
  - The Freqtrade subprocess returned exit code 0 and run-summary status success while the workflow audit job failed; runtime evidence reconciles this because FreqAI caught both pair-level training ValueErrors, skipped training and emitted no valid raw matrix audit.
first_failure:
  marker: EXPANDED_VOLUME_CHANGE_INFINITY
  evidence: runtime/backtest.log in artifact 8667673779 records the first caught training exception for BTC/USDT at build_raw_matrix_audit, followed by the same feature-class failure for ETH/USDT.
rejected_hypotheses:
  - The canonical request or frozen infrastructure drifted; request validation passed.
  - Pre-May market-data coverage was incomplete; both pair jobs and the combined pre-fit verification passed.
  - The training exception remained unavailable; the reordered durable runtime exposed it exactly.
  - Any comparator model produced a result or failed independently; all three comparator executions were skipped before fit.
changed_paths:
  - docs/agents/tasks/FTAI-20260726-residual-pytorch-bounded-m1-execution.md
validation:
  - command: Residual PyTorch Bounded M1 Execution run 30299203871
    result: FAIL_CLOSED_AS_DESIGNED
    evidence: Request and data validation passed; exact expanded-matrix audit failed before comparator execution.
  - command: Inspect residual-pytorch-bounded-m1-audit-517 artifact 8667673779
    result: PASS
    evidence: Durable runtime contains both exact volume-change infinity exceptions, empty audit stderr, audit subprocess exit code 0 and no raw valid matrix-audit files.
  - command: Close PR 517 without merge
    result: PASS
    evidence: PR 517 is closed, merged false.
blockers:
  - Frozen contract v1 forbids the feature-definition change required to remediate the confirmed non-finite volume-change feature.
next_action: Create a separate bounded remediation task that explicitly decides whether to retire v1 or authorizes a versioned v2 strategy and contract with finite %-volume-change semantics plus regression tests; do not modify or rerun v1.
```
