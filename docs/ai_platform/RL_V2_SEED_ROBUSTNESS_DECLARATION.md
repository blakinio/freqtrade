# RL-v2 Prospective Seed Robustness Declaration

## Scope

This declaration freezes the next legal RL-v2 research gate after the completed lifecycle paired
attribution and interpretation.

It performs **no execution**. A separate reviewed task is required before any seed is trained or
backtested.

## Source boundary

The declaration is bound to:

- paired-attribution run `30131273189`;
- artifact `rl-v2-roi-lifecycle-paired-attribution-272`;
- artifact digest `sha256:11e9d9a8e5f8e65474406524445c7b04fe3d9af5afa6d137847c913f8e66ae04`;
- immutable anchor seed `42`;
- lifecycle-aligned strategy `AiDesiredPositionRLLifecycleAlignedResearchStrategy`;
- classification `paired_historical_development_attribution`;
- `strict_oos=false` and `protected_final_validation=false`.

The anchor seed and immutable baseline are reference evidence only. Neither may be rerun.

## Deterministic seed selection

To prevent cherry-picking, the new seeds are derived before execution from namespace:

`rl-v2-lifecycle-seed-robustness-v1`

SHA-256:

`c70f5612edf1f2748eea6abafa2160af15a796bffe9c1df9ba59eed7c955d333`

Derivation:

1. compute SHA-256 of the UTF-8 namespace;
2. read the first five non-overlapping four-byte chunks in order;
3. interpret each chunk as an unsigned big-endian integer;
4. apply `value & 0x7fffffff`.

Frozen seeds:

| Order | Seed |
|---:|---:|
| 1 | `1192187410` |
| 2 | `1844572788` |
| 3 | `250243770` |
| 4 | `2049007791` |
| 5 | `363304639` |

Seed `42` is deliberately excluded. Seeds cannot be replaced, reordered or dropped after results are
observed.

## Frozen execution geometry

A future execution task must keep all declared inputs unchanged:

- model: `DesiredPositionReinforcementLearner`;
- strategy: `AiDesiredPositionRLLifecycleAlignedResearchStrategy`;
- pairs: `BTC/USDT`, `ETH/USDT`;
- timeframes: `15m`, `1h`, `4h`;
- download range: `20250801-20260501`;
- execution range: `20260301-20260501`;
- semantic evidence window: `20260301-20260430`;
- fee: `0.002`;
- train period: `90` days;
- backtest period: `61` days;
- reward, features, thresholds, PPO parameters and action semantics unchanged.

Only these per-seed operational values may differ:

1. `freqai.model_training_parameters.seed`;
2. a deterministic seed suffix on the FreqAI identifier to prevent cache/model collision.

Exactly five new variant training/backtest executions are permitted by a future execution contract.
This declaration itself authorizes zero.

## Why the evidence must include signal state

The lifecycle flag suppresses ROI only while the entry signal remains active. Therefore the robust
mechanism metric cannot be merely “ROI exit followed by a 15-minute re-entry.”

A future evidence extractor must record for every external exit:

- pair and exit reason;
- exit timestamp;
- whether the entry signal was active at the exit;
- next same-pair entry timestamp;
- re-entry gap in minutes.

This distinguishes:

- a true lifecycle conflict: ROI closes while long intent remains active;
- a legitimate transition: entry intent is inactive at exit and becomes active again later.

## Prospectively frozen criteria

### Execution integrity

All five declared seeds must complete with exact frozen hashes. Missing, failed or substituted seeds are
not discarded; they make the overall result `inconclusive`.

### Primary mechanism consistency

For every eligible seed:

- `roi_exit_while_entry_signal_active_count == 0`;
- `roi_exit_while_entry_signal_active_followed_by_same_pair_15m_reentry_count == 0`.

All five seeds must pass. Any eligible seed with an active-entry ROI lifecycle conflict classifies the
mechanism as `mechanism_not_seed_robust`.

Raw ROI-to-15-minute re-entry events with the entry signal inactive at exit remain reportable secondary
observations, not automatic primary failures.

### Non-degeneracy

Each seed must have:

- at least one completed trade for each declared pair;
- at least one non-force exit in total.

A seed failing either guard is `inconclusive`, not a robustness pass.

### Dispersion reporting

For trade count, fees, net PnL, profit factor, maximum drawdown, pair exposure and exit counts, report:

- minimum;
- maximum;
- median;
- interquartile range.

These values are descriptive. Profit is not a gate and cannot select, rank or replace seeds.

## Result vocabulary

- `mechanism_seed_robust`: all five seeds satisfy integrity, primary mechanism and non-degeneracy criteria.
- `mechanism_not_seed_robust`: at least one eligible seed records an active-entry ROI lifecycle conflict.
- `inconclusive`: any seed is missing, fails frozen-input integrity or fails non-degeneracy.

None of these classifications establishes strict OOS generalization, protected final validation,
profitability, superiority, promotion or deployment readiness.

## Forbidden actions

- No seed `42` rerun.
- No baseline rerun.
- No consumed historical OOS access.
- No protected final holdout access.
- No seed substitution after result inspection.
- No PPO, reward, feature, threshold, strategy or geometry change.
- No same-package retuning after a mixed or failed result.
- No change to Phase 6 `selected_model=null`.

## Next legal work package

A separate **inert seed-robustness infrastructure task** may implement:

- deterministic per-seed config generation;
- exact hash validation;
- signal-state-aware exit evidence;
- aggregate dispersion reporting;
- a canonical run-request contract.

Infrastructure merge must execute no model. Execution requires another explicit canonical request task.
