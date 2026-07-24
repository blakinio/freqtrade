# RL-v2 ROI Lifecycle Alignment

## Purpose

Declare one isolated RL-v2 strategy-lifecycle hypothesis before implementation or execution.

The historical diagnosis in
`docs/ai_platform/RL_V2_HISTORICAL_EVIDENCE_DIAGNOSIS.md` found that inherited ROI exits frequently
closed a trade while the next accepted desired-position decision returned to `target_long`. The exact
Freqtrade extension point for this mechanism is `ignore_roi_if_entry_signal`.

## Selected single variable

A new versioned research strategy will inherit from
`AiDesiredPositionRLResearchStrategy` and set only:

```python
ignore_roi_if_entry_signal = True
```

The baseline strategy will not be modified.

Freqtrade core evaluates ROI using:

```python
roi_reached = not (enter and self.ignore_roi_if_entry_signal) and self.min_roi_reached(...)
```

Therefore the selected setting suppresses ROI only while the current accepted entry signal remains
active. It does not disable:

- the hard `-0.05` stop-loss;
- policy-driven `target_flat` exit signals;
- the inherited ROI schedule when no entry signal is active.

## Frozen implementation boundaries

The versioned subclass may override no other strategy field or method.

The following remain frozen:

- model: `DesiredPositionReinforcementLearner`;
- PPO / `MlpPolicy`;
- model training parameters;
- reward constants;
- feature set and timeframes;
- desired-position action meanings;
- pairs `BTC/USDT` and `ETH/USDT`;
- Kraken spot;
- fee `0.002`;
- `minimal_roi = {"0": 0.03, "240": 0.015, "720": 0.0}`;
- stop-loss `-0.05`;
- thresholds `0.006/-0.009`;
- Phase 6 `selected_model=null`.

The declaration and implementation PRs may not train, backtest, download data, or add an execution
workflow.

## Required implementation proof

Tests must demonstrate:

1. the new strategy is a subclass of `AiDesiredPositionRLResearchStrategy`;
2. its only declared strategy-lifecycle delta is `ignore_roi_if_entry_signal=True`;
3. the inherited ROI schedule, stop-loss, timeframe, long-only mode and exit-signal behavior are
   unchanged;
4. Freqtrade `should_exit` does not emit ROI when ROI is reached and `enter=True`;
5. ROI remains available when ROI is reached and `enter=False`;
6. stop-loss remains active regardless of the ROI-ignore setting;
7. target-flat exit signals remain active.

## Future paired attribution

Historical execution is not authorized by this declaration.

A later separate execution task may compare one experimental run against immutable baseline artifact
`rl-v2-historical-training-execution-218` on the already known March-April development window.

That comparison must be labeled:

- `paired_historical_development_attribution`;
- `strict_oos=false`;
- `protected_final_validation=false`.

The primary metrics are mechanistic:

- ROI exit count;
- ROI exit followed by same-pair 15-minute re-entry count;
- close-plus-reopen fees at immediate external-exit/re-entry boundaries.

Net profit is secondary and cannot be used as a promotion or profitability criterion.

## Isolation

The following remain forbidden:

- consumed historical OOS `20260501-20260630`;
- protected final holdout `20260801-20260930`;
- simultaneous tuning of target-flat quality, PPO, reward, features, thresholds, stop-loss or action
  semantics;
- PyTorch/RL ranking;
- dry-run or live deployment;
- profitability, superiority or promotion claims.
