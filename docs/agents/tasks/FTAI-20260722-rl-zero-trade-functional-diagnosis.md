---
task_id: FTAI-20260722-rl-zero-trade-functional-diagnosis
status: active
branch: docs/rl-zero-trade-functional-diagnosis-task
base_branch: develop
created: 2026-07-22
updated: 2026-07-22
related_pr: "pending"
owned_paths:
  - docs/agents/tasks/FTAI-20260722-rl-zero-trade-functional-diagnosis.md
  - docs/ai_platform/RL_ZERO_TRADE_FUNCTIONAL_DIAGNOSIS.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/EXPERIMENTAL_MODEL_HISTORICAL_BACKTEST_EVIDENCE.md
  - ai_platform/experimental_model_research/evidence/rl-research-v1-historical-oos-v1.json
  - ai_platform/experiments/rl-research-v1.json
  - ai_platform/configs/freqai-rl-research.example.json
  - ai_platform/strategies/AiLongOnlyRLResearchStrategy.py
  - ai_platform/freqaimodels/LongOnlyReinforcementLearner.py
search_first:
  - merged PR #95 and current develop before diagnosis work
  - closed execution-carrier PR #94 and workflow run 29844351936
  - open PRs or active tasks overlapping RL research ownership
optional_reads:
  - workflow artifacts 8503197359 and 8503203347
  - .github/workflows/experimental-model-historical-backtest-execution.yml
---

# RL zero-trade functional diagnosis

## Goal

Determine, without any new model execution or tuning, why the completed frozen `rl-research-v1` historical execution produced zero trades. Distinguish an expected learned no-trade policy from strategy/action gating, action-space integration drift, model/runtime failure, configuration mismatch, or evidence-extraction error. Produce a durable functional root-cause assessment and a bounded recommendation for any later work package.

## Non-negotiable boundaries

- Diagnosis only: no training, backtest rerun, OOS rerun, Hyperopt, reward search, feature search, model-parameter change, threshold change, or strategy behavior change.
- Do not reuse consumed strict historical OOS `20260501-20260630` for tuning or post-fix validation.
- Do not access protected final holdout `20260801-20260930`.
- Do not rank PyTorch versus RL or invent a retrospective cross-track selection policy.
- Do not change completed Phase 6, its frozen candidates, selection policy, or authoritative `selected_model = null` conclusion.
- Any runtime/model fix or fresh evaluation must be a separate prospectively declared bounded task after this diagnosis is complete.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-22T00:00:00+02:00
head: 55a70d6e6f548390939d34af7c07618e4379be03
branch: docs/rl-zero-trade-functional-diagnosis-task
pr: pending task declaration PR
status: active
context_routes:
  - docs/ai_platform/EXPERIMENTAL_MODEL_HISTORICAL_BACKTEST_EVIDENCE.md
  - ai_platform/experimental_model_research/evidence/rl-research-v1-historical-oos-v1.json
  - ai_platform/strategies/AiLongOnlyRLResearchStrategy.py
  - ai_platform/freqaimodels/LongOnlyReinforcementLearner.py
owned_paths:
  - docs/agents/tasks/FTAI-20260722-rl-zero-trade-functional-diagnosis.md
  - docs/ai_platform/RL_ZERO_TRADE_FUNCTIONAL_DIAGNOSIS.md
proven:
  - Experimental historical execution task FTAI-20260721-experimental-model-historical-backtest-execution is complete on develop after PR #95.
  - Workflow run 29844351936 executed exactly one frozen RL historical backtest and uploaded independent RL artifact 8503197359.
  - Durable RL strict OOS evidence records zero trades, profit 0.0, drawdown 0.0 and stability 0.0 for 20260501-20260630.
  - The durable evidence explicitly treats the zero-profit result as an inactive zero-trade outcome, not profitability evidence.
  - Frozen entry and exit thresholds remain 0.006 and -0.009.
  - Protected final holdout 20260801-20260930 remains unused and forbidden.
  - PyTorch/RL remain isolated from completed Phase 6 and no cross-track winner was selected.
derived:
  - Zero trades alone does not prove that the RL integration is broken; functional diagnosis must separate valid policy inactivity from execution-path defects.
  - Existing source, run metadata, logs and artifacts may be inspected without authorizing a new historical execution.
unknown:
  - Whether the trained policy emitted only hold/no-entry actions during the scored interval.
  - Whether valid RL actions were blocked or mistranslated by deterministic strategy gating or action-space integration.
  - Whether configuration, model loading, runtime provenance, or result extraction masked an otherwise active policy.
conflicts: []
first_failure:
  marker: rl-zero-trade-cause-unclassified
  evidence: The completed RL execution produced zero trades, but the durable evidence does not classify the functional cause of inactivity.
rejected_hypotheses:
  - Retune reward, features, thresholds or model parameters from the consumed historical OOS result.
  - Rerun the same consumed historical OOS after making a model or strategy change.
  - Treat zero trades as proof of profitability, robustness, or superiority.
  - Compare or rank RL against PyTorch inside this diagnosis-only task.
  - Use protected final holdout data to diagnose or validate the RL track.
changed_paths:
  - docs/agents/tasks/FTAI-20260722-rl-zero-trade-functional-diagnosis.md
validation:
  - command: live repository and PR preflight
    result: PASS
    evidence: develop is 55a70d6e6f548390939d34af7c07618e4379be03, PR #95 is merged, PR #94 is closed without merge, and no open PR overlaps this diagnosis scope.
blockers: []
next_action: Merge this bounded task declaration, then inspect the preserved RL evidence/artifact and canonical RL model-strategy-config execution path to classify the zero-trade cause without modifying runtime behavior or running a new backtest.
```
