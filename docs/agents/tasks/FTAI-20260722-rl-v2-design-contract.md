---
task_id: FTAI-20260722-rl-v2-design-contract
status: done
branch: develop
base_branch: develop
created: 2026-07-22
updated: 2026-07-22
related_pr: "102"
owned_paths:
  - docs/agents/tasks/FTAI-20260722-rl-v2-design-contract.md
  - docs/ai_platform/RL_V2_DESIGN_CONTRACT.md
  - ai_platform/experimental_model_research/rl-v2-design-contract-v1.json
  - ai_platform/scripts/rl_v2_design_contract.py
  - tests/ai_platform/test_rl_v2_design_contract.py
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/RL_ZERO_TRADE_FUNCTIONAL_DIAGNOSIS.md
  - docs/ai_platform/RL_V2_DESIGN_CONTRACT.md
  - ai_platform/experimental_model_research/rl-v2-design-contract-v1.json
search_first:
  - current develop and open PRs before declaring any RL-v2 implementation task
  - active tasks overlapping RL research ownership
optional_reads:
  - ai_platform/experimental_model_research/evidence/rl-research-v1-historical-oos-v1.json
  - ai_platform/configs/freqai-rl-research.example.json
---

# RL-v2 Design Contract

## Goal

Define a machine-readable, fail-closed design contract for a future RL-v2 research track before any RL-v2 model, strategy, training, backtest, or evaluation implementation begins. The contract must address the root causes and observability gaps established by the completed RL zero-trade functional diagnosis without modifying the frozen `rl-research-v1` track.

## Non-negotiable boundaries

- Contract and synthetic/static validation only: no training, backtest, OOS execution, Hyperopt, market-data download, model fitting, or performance evaluation.
- Do not modify `rl-research-v1` model, strategy, config, manifest, historical evidence, or completed execution records.
- Do not reuse consumed strict historical OOS `20260501-20260630` for tuning, redesign validation, or fresh evidence.
- Do not access protected final holdout `20260801-20260930`.
- Do not change frozen thresholds `0.006/-0.009`.
- Do not change completed Phase 6, its candidates, selection policy, or authoritative `selected_model = null` result.
- Do not rank RL against PyTorch, authorize promotion, or make profitability/superiority claims.
- Do not choose or consume a future evaluation window in this task; any fresh evaluation must be declared separately after implementation is frozen.

## Required contract properties

The RL-v2 design contract must fail closed unless all of the following are explicit:

1. **Reward geometry**
   - remaining flat while already neutral has a strictly lower immediate reward than a valid long-entry transition;
   - perpetual neutral inactivity is not an unpenalized zero-reward solution by construction;
   - invalid actions remain penalized;
   - reward inputs are decision-time/state inputs only and must not derive from future candles.
2. **Position-state and inference parity**
   - the design declares either an explicit position-state observation mechanism available consistently during training and historical inference, or action semantics proven not to require hidden position state;
   - a synthetic parity test is required before any later historical execution.
3. **Mandatory observability**
   - deterministic inference action counts by pair and action;
   - `do_predict` accepted/rejected counts;
   - strategy entry/exit signal counts before trade-capacity/order handling;
   - raw backtest trade counts and strict-OOS extraction counts remain separately attributable.
4. **Evaluation isolation**
   - consumed historical OOS and protected final holdout are explicitly forbidden;
   - a future evaluation window must be prospectively declared in a later bounded task;
   - no cross-track selection or Phase 6 consumption is permitted.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-22T01:20:00+02:00
head: c1834ef876e3c64bce89559ad20d93f7b6104f88
branch: develop
pr: 102
status: ready
context_routes:
  - docs/ai_platform/RL_V2_DESIGN_CONTRACT.md
  - ai_platform/experimental_model_research/rl-v2-design-contract-v1.json
  - ai_platform/scripts/rl_v2_design_contract.py
owned_paths:
  - docs/agents/tasks/FTAI-20260722-rl-v2-design-contract.md
  - docs/ai_platform/RL_V2_DESIGN_CONTRACT.md
  - ai_platform/experimental_model_research/rl-v2-design-contract-v1.json
  - ai_platform/scripts/rl_v2_design_contract.py
  - tests/ai_platform/test_rl_v2_design_contract.py
proven:
  - RL zero-trade diagnosis PR #100 was squash-merged as e0f6d3e557a880c49d6146530f806a0826f2d8e6 and closed the diagnosis task.
  - Task declaration PR #101 was squash-merged as e040eb1fcf0761409694856cb36794944d0ca34f before implementation began.
  - Implementation PR #102 was squash-merged as c1834ef876e3c64bce89559ad20d93f7b6104f88 with exactly five owned paths and no RL-v2 runtime/model/strategy/config execution changes.
  - The design contract keeps rl-research-v1 immutable and authorizes no RL-v2 model, strategy, config, training, backtest, data download or performance evaluation.
  - Reward invariants require flat-neutral reward to be strictly below valid long-entry reward, invalid-action penalty, no future-derived reward inputs and synthetic edge-case coverage.
  - Future implementation must choose exactly one position-state design mode and prove training/historical-inference parity synthetically before any historical execution.
  - Mandatory evidence requires action histograms, do_predict counts, pre-trade signal counts, raw backtest counts and strict-OOS counts as separately attributable layers.
  - Consumed historical OOS 20260501-20260630 and protected final holdout 20260801-20260930 remain forbidden; no future evaluation window was selected.
  - Frozen thresholds 0.006/-0.009 and completed Phase 6 selected_model null remain unchanged and RL-v2 cannot be consumed by Phase 6.
  - Final PR #102 gates passed on head 730042f821168d49026f1ca9ce728b4750f7a2f4: AI Platform CI 29875028448, Freqtrade CI 29875028434, and zizmor 29875028428; Pre-commit Types was skipped, not failed.
derived:
  - The contract removes post-hoc ambiguity by making reward geometry, position-state parity and action-level observability prospective requirements for any later RL-v2 implementation task.
  - Numeric reward magnitudes and the concrete position-state/action-semantics architecture remain intentionally deferred and cannot be tuned from consumed historical OOS.
unknown:
  - Which concrete RL-v2 design mode and reward magnitudes a later separately declared implementation task will choose.
conflicts: []
first_failure:
  marker: ruff-format-only-resolved
  evidence: Initial implementation CI failures were limited to Ruff lint/format; exact formatting was applied without semantic changes and all final gates passed.
rejected_hypotheses:
  - Modify or rerun rl-research-v1 to validate the design contract.
  - Select numeric reward magnitudes or a future evaluation window in this task.
  - Tune any design against consumed historical OOS or protected final holdout data.
  - Add RL-v2 to completed Phase 6 or compare it retrospectively with PyTorch.
changed_paths:
  - docs/agents/tasks/FTAI-20260722-rl-v2-design-contract.md
  - docs/ai_platform/RL_V2_DESIGN_CONTRACT.md
  - ai_platform/experimental_model_research/rl-v2-design-contract-v1.json
  - ai_platform/scripts/rl_v2_design_contract.py
  - tests/ai_platform/test_rl_v2_design_contract.py
validation:
  - command: task declaration PR #101
    result: PASS
    evidence: Freqtrade CI 29874237734 and zizmor 29874237741 completed successfully before squash merge e040eb1fcf0761409694856cb36794944d0ca34f.
  - command: AI Platform CI on final implementation head
    result: PASS
    evidence: Run 29875028448 completed successfully, including compile, targeted tests, Ruff lint and Ruff format.
  - command: Freqtrade CI on final implementation head
    result: PASS
    evidence: Run 29875028434 completed successfully, including pre-commit, docs and full required core matrix/CI Gate.
  - command: GitHub Actions Security Analysis with zizmor on final implementation head
    result: PASS
    evidence: Run 29875028428 completed successfully.
  - command: protected-boundary and experiment-isolation review
    result: PASS
    evidence: No training, backtest, data download, consumed-OOS reuse, protected-final-holdout access, Phase 6 change or future evaluation-window selection occurred.
blockers: []
next_action: Declare a separate RL-v2 synthetic implementation task that selects exactly one allowed position-state/action-semantics design mode and implements synthetic-only reward, parity and observability proofs, without training, backtest, consumed historical OOS, protected final holdout access or performance conclusions.
```
