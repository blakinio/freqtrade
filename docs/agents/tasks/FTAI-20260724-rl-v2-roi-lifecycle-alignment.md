---
task_id: FTAI-20260724-rl-v2-roi-lifecycle-alignment
status: active
branch: docs/rl-v2-roi-lifecycle-alignment-declaration
base_branch: develop
created: 2026-07-24
updated: 2026-07-24
related_pr: "238"
owned_paths:
  - docs/agents/tasks/FTAI-20260724-rl-v2-roi-lifecycle-alignment.md
  - docs/ai_platform/RL_V2_ROI_LIFECYCLE_ALIGNMENT.md
  - ai_platform/experimental_model_research/rl-v2-roi-lifecycle-alignment-v1.json
  - ai_platform/strategies/AiDesiredPositionRLLifecycleAlignedResearchStrategy.py
  - tests/ai_platform/test_rl_v2_roi_lifecycle_alignment.py
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260724-rl-v2-historical-evidence-diagnosis.md
  - docs/ai_platform/RL_V2_HISTORICAL_EVIDENCE_DIAGNOSIS.md
  - ai_platform/experimental_model_research/rl-v2-historical-evidence-diagnosis-v1.json
  - ai_platform/strategies/AiDesiredPositionRLResearchStrategy.py
  - ai_platform/strategies/AiLongOnlyRLResearchStrategy.py
  - freqtrade/strategy/interface.py
search_first:
  - current develop and open PRs overlapping RL-v2 strategy lifecycle, ROI, reward or evaluation work
---

# RL-v2 ROI Lifecycle Alignment

## Goal

Prospectively isolate and implement exactly one strategy-lifecycle change derived from the completed
historical evidence diagnosis:

`ignore_roi_if_entry_signal = True`

The baseline strategy remains immutable. The experimental variant must be a new versioned subclass.

## Exact selected delta

Add:

`AiDesiredPositionRLLifecycleAlignedResearchStrategy`

as a direct subclass of `AiDesiredPositionRLResearchStrategy`, with only one explicit strategy
override:

```python
ignore_roi_if_entry_signal = True
```

Freqtrade core then skips ROI evaluation when an entry signal is currently active. Hard stop-loss,
target-flat exit signals and ROI without an active entry signal remain available.

## Allowed implementation scope

- Add the versioned subclass.
- Add focused unit tests proving inheritance and the exact core exit behavior.
- Update this task checkpoint and implementation documentation.

## Non-negotiable boundaries

- Do not modify `AiDesiredPositionRLResearchStrategy`.
- Do not change minimal ROI, stop-loss, PPO, policy, reward, features, timeframes, pairs, fee, action
  semantics or thresholds.
- No training, backtest, market-data access or execution workflow in declaration or implementation PRs.
- No use of consumed OOS `20260501-20260630`.
- No access to protected final holdout `20260801-20260930`.
- No strict-OOS, final-validation, ranking, promotion, profitability or superiority claim.
- Phase 6 `selected_model=null` remains unchanged.

## Future execution boundary

A historical paired attribution run is not authorized by this task's declaration or implementation
PRs. It requires a separate execution task after the implementation is merged.

Any such run must reuse immutable baseline artifact `rl-v2-historical-training-execution-218` and be
classified only as `paired_historical_development_attribution`, with profitability explicitly
non-gating.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-24T10:20:00+02:00
head: 6550574cb532a54a29617a1fc0bd1d893ec09705
branch: docs/rl-v2-roi-lifecycle-alignment-declaration
pr: 238
status: ready
context_routes:
  - docs/agents/tasks/FTAI-20260724-rl-v2-historical-evidence-diagnosis.md
  - docs/ai_platform/RL_V2_HISTORICAL_EVIDENCE_DIAGNOSIS.md
  - ai_platform/experimental_model_research/rl-v2-historical-evidence-diagnosis-v1.json
owned_paths:
  - docs/agents/tasks/FTAI-20260724-rl-v2-roi-lifecycle-alignment.md
  - docs/ai_platform/RL_V2_ROI_LIFECYCLE_ALIGNMENT.md
  - ai_platform/experimental_model_research/rl-v2-roi-lifecycle-alignment-v1.json
  - ai_platform/strategies/AiDesiredPositionRLLifecycleAlignedResearchStrategy.py
  - tests/ai_platform/test_rl_v2_roi_lifecycle_alignment.py
proven:
  - PR #237 merged the immutable-artifact diagnosis as 49167cdf9ab6fd126de72613101c35fef6cc07e2 and selected lifecycle churn as the highest-confidence mechanism.
  - The baseline strategy remains AiDesiredPositionRLResearchStrategy with SHA-256 9318a4d13937d9b572c4bcecfb56f999fd82d8309c6f898d0166c0c71dfd5c19.
  - The baseline inherits minimal_roi 0:0.03, 240:0.015 and 720:0.0, hard stoploss -0.05 and use_exit_signal=true.
  - Freqtrade should_exit skips ROI evaluation when enter is true and ignore_roi_if_entry_signal is true.
  - Stop-loss evaluation occurs independently before ROI is appended, so the selected setting does not disable the hard stop-loss.
  - The experimental strategy is prospectively fixed as a new subclass with only ignore_roi_if_entry_signal=true.
  - Declaration and implementation prohibit training, backtest, market-data access and execution workflow changes.
  - Any future paired run must be a separate task and historical-development attribution only.
  - Consumed OOS 20260501-20260630 and protected final holdout 20260801-20260930 remain forbidden.
  - Frozen thresholds remain 0.006/-0.009 and Phase 6 selected_model remains null.
derived:
  - A new subclass preserves exact reproducibility of the original strategy and its completed artifact.
  - The selected flag is narrower than disabling ROI because ROI remains available when no entry signal is active.
  - Lifecycle alignment can be tested without simultaneously changing target-flat policy quality.
unknown:
  - The historical magnitude of churn reduction remains unknown until a separately authorized paired attribution run.
conflicts: []
first_failure:
  marker: inherited_roi_conflicts_with_active_desired_long_signal
  evidence: Baseline evidence recorded 122 ROI exits each followed by same-pair re-entry after one 15-minute candle.
rejected_hypotheses:
  - Mutate the baseline AiDesiredPositionRLResearchStrategy in place.
  - Disable ROI globally.
  - Remove or weaken the hard stop-loss.
  - Add a cooldown together with the selected flag.
  - Tune target-flat behavior, PPO, reward, features or thresholds in this task.
  - Execute on consumed OOS 20260501-20260630.
  - Access protected final holdout 20260801-20260930.
  - Treat future paired development attribution as strict OOS or promotion evidence.
changed_paths:
  - docs/agents/tasks/FTAI-20260724-rl-v2-roi-lifecycle-alignment.md
  - docs/ai_platform/RL_V2_ROI_LIFECYCLE_ALIGNMENT.md
  - ai_platform/experimental_model_research/rl-v2-roi-lifecycle-alignment-v1.json
validation:
  - command: diagnosis-to-declaration traceability inspection
    result: PASS
    evidence: Declaration binds diagnosis merge, immutable artifact digest, baseline strategy identity and the selected single mechanism.
  - command: Freqtrade should_exit source inspection
    result: PASS
    evidence: Core condition is not (enter and ignore_roi_if_entry_signal) before min_roi_reached, while stop-loss and exit-signal checks remain independent.
blockers: []
next_action: Merge declaration PR #238 after CI, then create a separate implementation PR from updated develop that adds only the versioned lifecycle-aligned strategy, focused tests and this checkpoint update; do not train, backtest, access market data or create an execution workflow.
```
