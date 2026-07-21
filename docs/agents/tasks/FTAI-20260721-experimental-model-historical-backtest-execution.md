---
task_id: FTAI-20260721-experimental-model-historical-backtest-execution
status: done
branch: docs/experimental-model-historical-backtest-evidence
base_branch: develop
created: 2026-07-21
updated: 2026-07-21
related_pr: "95"
owned_paths:
  - docs/agents/tasks/FTAI-20260721-experimental-model-historical-backtest-execution.md
  - docs/ai_platform/EXPERIMENTAL_MODEL_HISTORICAL_BACKTEST_EXECUTION.md
  - docs/ai_platform/EXPERIMENTAL_MODEL_HISTORICAL_BACKTEST_EVIDENCE.md
  - ai_platform/experimental_model_research/evidence/pytorch-research-v1-historical-oos-v1.json
  - ai_platform/experimental_model_research/evidence/rl-research-v1-historical-oos-v1.json
  - ai_platform/experimental_model_research/historical-backtest-execution-contract-v1.json
  - ai_platform/experimental_model_research/run-requests/historical-backtest-execution-v1.json
  - ai_platform/scripts/experimental_model_historical_backtest_run_request.py
  - tests/ai_platform/test_experimental_model_historical_backtest_run_request.py
  - .github/workflows/experimental-model-historical-backtest-execution.yml
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/EXPERIMENTAL_MODEL_HISTORICAL_BACKTEST_EXECUTION.md
  - docs/ai_platform/EXPERIMENTAL_MODEL_HISTORICAL_BACKTEST_EVIDENCE.md
search_first:
  - merged PR #95 and current develop before any follow-up experimental-model task
  - closed execution-carrier PR #94
  - workflow run 29844351936 and artifacts 8503203347 / 8503197359
---

# Experimental Model Historical Backtest Execution v1

## Goal

Create and use a fail-closed, one-shot historical execution path for exactly the two already-canonical isolated research tracks: `pytorch-research-v1` and `rl-research-v1`. Execute at most one frozen historical backtest per track, extract strict historical-OOS evidence, and persist immutable independent evidence without retuning, promotion, profitability claims, Phase 6 modification, cross-track selection, or protected-final-holdout access.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-21T22:06:00Z
head: 5b5557587d1990ed7bfff016337468f40a7792e0
branch: docs/experimental-model-historical-backtest-evidence
pr: 95
status: done
context_routes:
  - docs/ai_platform/EXPERIMENTAL_MODEL_HISTORICAL_BACKTEST_EXECUTION.md
  - docs/ai_platform/EXPERIMENTAL_MODEL_HISTORICAL_BACKTEST_EVIDENCE.md
  - ai_platform/experimental_model_research/evidence/pytorch-research-v1-historical-oos-v1.json
  - ai_platform/experimental_model_research/evidence/rl-research-v1-historical-oos-v1.json
owned_paths:
  - docs/agents/tasks/FTAI-20260721-experimental-model-historical-backtest-execution.md
  - docs/ai_platform/EXPERIMENTAL_MODEL_HISTORICAL_BACKTEST_EVIDENCE.md
  - ai_platform/experimental_model_research/evidence/pytorch-research-v1-historical-oos-v1.json
  - ai_platform/experimental_model_research/evidence/rl-research-v1-historical-oos-v1.json
proven:
  - Infrastructure PR #86 was squash-merged as 891ee62aa134b98bec9449155db9bd0b245e547b after AI Platform CI, zizmor, full Freqtrade CI and pre-commit passed.
  - Checkpoint compactness fix PR #93 was merged as 8451420b5bd932e81896bb4f4f997730c4eb7f82 after the first trigger PR #92 failed closed before runtime or market-data access.
  - Fresh one-shot trigger PR #94 used exact execution head af9e27c48c9f2bf4e7277d09fe5eaec2ee020af3 and added only the canonical request file.
  - Workflow run 29844351936 completed successfully, including request validation, boundary-correct Kraken history verification, exactly one PyTorch backtest, exactly one RL backtest, strict OOS extraction, and independent artifact upload.
  - PyTorch artifact 8503203347 digest sha256:5092ef0d5b44de9812a822299b1af88c69d10c8c4f1ccc6b55c30359b3bf864d matched the independently downloaded ZIP SHA-256.
  - PyTorch strict OOS 20260501-20260630 contains 20 trades, profit -0.001927824937, drawdown 0.0022277419634928177, stability 0.0, with negative May and June fold profits.
  - RL artifact 8503197359 digest sha256:66bef9f73ea898e81707ad2088693d93e86f13fdae59f3782075fb456cb9f9d4 matched the independently downloaded ZIP SHA-256.
  - RL strict OOS 20260501-20260630 contains zero trades, profit 0.0, drawdown 0.0, and stability 0.0; zero profit/drawdown is an inactive zero-trade outcome, not profitability evidence.
  - Trigger PR #94 was closed without merge after evidence collection as required by the one-shot contract.
  - PR #95 durably preserves independent PyTorch and RL evidence records plus the interpretation boundary without adding execution logic or cross-track selection.
  - PyTorch and RL remain outside completed Phase 6; authoritative Phase 6 selected_model null, frozen thresholds 0.006/-0.009, and protected final holdout 20260801-20260930 remain unchanged.
  - PR #95 pre-close gates passed: AI Platform CI 29872470567, zizmor 29872470568, and Freqtrade CI 29872470616 including pre-commit, documentation build, and CI Gate.
derived:
  - The bounded historical execution and durable evidence objective is complete.
  - No cross-track ranking or winner-selection policy may be invented retrospectively from these observations.
  - Any follow-up model, feature, reward, or experimental execution research requires a new prospectively declared bounded task.
unknown: []
conflicts: []
first_failure:
  marker: none
  evidence: The fresh one-shot execution and durable evidence preservation completed without an unresolved runtime, integrity, or repository-gate failure.
rejected_hypotheses:
  - Merge trigger PR #94 into develop.
  - Treat RL zero trades as profitability evidence.
  - Select a winner between PyTorch and RL from this evidence-only work package.
  - Retune thresholds, features, model parameters, or RL reward design using consumed historical OOS.
  - Access protected final holdout 20260801-20260930.
  - Add either track retroactively to completed Phase 6 or change selected_model null.
changed_paths:
  - ai_platform/experimental_model_research/evidence/pytorch-research-v1-historical-oos-v1.json
  - ai_platform/experimental_model_research/evidence/rl-research-v1-historical-oos-v1.json
  - docs/ai_platform/EXPERIMENTAL_MODEL_HISTORICAL_BACKTEST_EVIDENCE.md
  - docs/agents/tasks/FTAI-20260721-experimental-model-historical-backtest-execution.md
validation:
  - command: Experimental Model Historical Backtest Execution workflow run 29844351936
    result: PASS
    evidence: Request validation, BTC/ETH history preparation, PyTorch execution and RL execution jobs all completed successfully.
  - command: independent artifact digest verification
    result: PASS
    evidence: Downloaded PyTorch and RL artifact ZIP SHA-256 values exactly matched GitHub Actions digests for artifacts 8503203347 and 8503197359.
  - command: PR #95 repository gates before task-close commit
    result: PASS
    evidence: AI Platform CI 29872470567, zizmor 29872470568, and Freqtrade CI 29872470616 completed successfully; pre-commit, documentation build and CI Gate passed.
blockers: []
next_action: none. This task is complete. Any follow-up experimental-model research must start as a new bounded work package from current develop and must preserve Phase 6 isolation, frozen thresholds, consumed historical-OOS non-retuning, and protected-final-holdout isolation.
```
