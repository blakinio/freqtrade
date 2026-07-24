---
task_id: FTAI-20260724-rl-v2-roi-lifecycle-alignment
status: done
branch: develop
base_branch: develop
created: 2026-07-24
updated: 2026-07-24
related_pr: "240"
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

The baseline strategy remains immutable. The experimental variant is a new versioned subclass.

## Exact selected delta

`AiDesiredPositionRLLifecycleAlignedResearchStrategy` is a direct subclass of
`AiDesiredPositionRLResearchStrategy` with only one explicit strategy override:

```python
ignore_roi_if_entry_signal = True
```

Freqtrade core then skips ROI evaluation when an entry signal is currently active. Hard stop-loss,
target-flat exit signals and ROI without an active entry signal remain available.

## Completed implementation

The implementation is merged and hash-bound. It has not been trained or backtested.

Focused tests prove:

- exact direct inheritance and the single public override;
- ROI suppression while `target_long` remains active;
- normal ROI behavior when no entry signal remains active;
- unchanged hard stop-loss behavior;
- unchanged `target_flat` exit-signal behavior;
- unchanged ROI schedule, timeframe, long-only mode and baseline strategy identity.

## Non-negotiable boundaries

- Do not modify `AiDesiredPositionRLResearchStrategy`.
- Do not change minimal ROI, stop-loss, PPO, policy, reward, features, timeframes, pairs, fee, action
  semantics or thresholds.
- No training, backtest, market-data access or execution workflow occurred in declaration or
  implementation work.
- No use of consumed OOS `20260501-20260630`.
- No access to protected final holdout `20260801-20260930`.
- No strict-OOS, final-validation, ranking, promotion, profitability or superiority claim.
- Phase 6 `selected_model=null` remains unchanged.

## Future execution boundary

A historical paired attribution run is not authorized by this completed implementation task. It
requires a separate prospectively bounded execution task.

Any such run must reuse immutable baseline artifact `rl-v2-historical-training-execution-218` and be
classified only as `paired_historical_development_attribution`, with profitability explicitly
non-gating.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-24T11:00:00+02:00
head: 09044f824ea102955147900f3d6d5e8f83929c0a
branch: develop
pr: 240
status: done
context_routes:
  - docs/agents/tasks/FTAI-20260724-rl-v2-historical-evidence-diagnosis.md
  - docs/ai_platform/RL_V2_HISTORICAL_EVIDENCE_DIAGNOSIS.md
  - ai_platform/experimental_model_research/rl-v2-historical-evidence-diagnosis-v1.json
  - docs/ai_platform/RL_V2_ROI_LIFECYCLE_ALIGNMENT.md
owned_paths:
  - docs/agents/tasks/FTAI-20260724-rl-v2-roi-lifecycle-alignment.md
  - docs/ai_platform/RL_V2_ROI_LIFECYCLE_ALIGNMENT.md
  - ai_platform/experimental_model_research/rl-v2-roi-lifecycle-alignment-v1.json
  - ai_platform/strategies/AiDesiredPositionRLLifecycleAlignedResearchStrategy.py
  - tests/ai_platform/test_rl_v2_roi_lifecycle_alignment.py
proven:
  - PR #237 merged immutable-artifact diagnosis 49167cdf9ab6fd126de72613101c35fef6cc07e2 and selected lifecycle churn as the highest-confidence mechanism.
  - Declaration PR #238 prospectively fixed ignore_roi_if_entry_signal=true as the only variant delta and merged as 9d5cc48db3aaa72995b10214642be6064ad5e00e.
  - Implementation PR #240 added a new direct subclass without mutating AiDesiredPositionRLResearchStrategy and squash-merged as 09044f824ea102955147900f3d6d5e8f83929c0a.
  - The versioned strategy declares only ignore_roi_if_entry_signal=true and is bound by SHA-256 366785129798d1332ce593f919c54aa23eefb2b15b2d850ab32d5c5cbdf0d5b7.
  - The baseline strategy hash remains 9318a4d13937d9b572c4bcecfb56f999fd82d8309c6f898d0166c0c71dfd5c19.
  - Minimal ROI 0:0.03, 240:0.015 and 720:0.0, hard stoploss -0.05, use_exit_signal=true, timeframe and long-only behavior remain inherited unchanged.
  - Static tests prove exact source inheritance, one allowed assignment and frozen implementation hash in lightweight validation.
  - Full-runtime tests prove active target_long suppresses ROI only, ROI remains without entry, hard stop-loss remains active and target-flat exits remain active.
  - Exact final head fec290b741e1d02d12a8de1f5582f65254ddab6b passed AI Platform CI, zizmor, pre-commit, documentation build and all Freqtrade core jobs on macOS, Windows and Ubuntu Python 3.11 through 3.14.
  - The implementation descriptor is marked implemented_not_executed and remains bound to the diagnosis artifact and strategy hash.
  - No training, backtest, market-data access, execution workflow, retuning, ranking or promotion occurred in declaration or implementation work.
  - Consumed OOS 20260501-20260630 and protected final holdout 20260801-20260930 remain unused; thresholds stay 0.006/-0.009 and Phase 6 selected_model remains null.
derived:
  - The new subclass preserves exact reproducibility of the original strategy and completed baseline artifact.
  - The selected flag is narrower than globally disabling ROI because ROI remains available when no active entry signal exists.
  - Lifecycle alignment can now be attributed separately from target-flat policy quality in a future bounded run.
unknown:
  - The historical magnitude of churn reduction remains unknown until a separately authorized paired attribution run.
conflicts: []
first_failure:
  marker: resolved_inherited_roi_conflict_with_active_desired_long_signal
  evidence: Baseline evidence recorded 122 ROI exits followed by same-pair re-entry after one 15-minute candle; the merged variant now uses the prospectively selected core flag while preserving every other frozen input.
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
validation:
  - command: PR #240 AI Platform CI
    result: PASS
    evidence: Compile, 489 lightweight tests with only full-runtime cases skipped, Ruff, Ruff format, codespell and JSON checks passed on final head.
  - command: PR #240 Freqtrade CI
    result: PASS
    evidence: Pre-commit, scope, documentation and core tests passed on macOS, Windows and Ubuntu Python 3.11 through 3.14; Ubuntu 3.12 coverage also passed.
  - command: PR #240 security workflow
    result: PASS
    evidence: zizmor completed successfully on exact final head fec290b741e1d02d12a8de1f5582f65254ddab6b.
blockers: []
next_action: Declare a separate prospectively bounded paired historical-development attribution execution task before any training, backtest or market-data access; reuse immutable baseline artifact rl-v2-historical-training-execution-218, keep profitability non-gating, and do not access consumed OOS or the protected final holdout.
```
