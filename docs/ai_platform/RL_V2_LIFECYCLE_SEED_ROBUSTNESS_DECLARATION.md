# RL-v2 Lifecycle Seed Robustness Declaration

## Purpose

The lifecycle-aligned paired attribution showed that the prospectively defined immediate ROI exit and
same-pair re-entry mechanism was absent for PPO seed `42` on the reused March-April historical-development
path. That evidence supports the mechanism for one stochastic training realization only.

This declaration freezes a bounded five-seed robustness study before any additional execution. It changes
no model behavior and authorizes no execution by itself.

## Evidence classification

Any future output under this declaration remains:

- `paired_historical_development_seed_robustness`;
- `strict_oos=false`;
- `protected_final_validation=false`;
- profitability non-gating;
- ineligible for automatic ranking, promotion, dry-run or live use.

The same data window has already influenced the lifecycle hypothesis. Repeating training with additional
seeds can assess stochastic path consistency, but it cannot restore out-of-sample status or establish
market generalization.

## Immutable anchor

The five-seed evidence set contains one existing anchor and four future executions:

| Role | Seed | Execution policy |
|---|---:|---|
| immutable anchor | `42` | reuse run `30131273189`; do not rerun |
| derived seed 1 | `300538280` | one future lifecycle-aligned variant execution |
| derived seed 2 | `1710810709` | one future lifecycle-aligned variant execution |
| derived seed 3 | `1950377252` | one future lifecycle-aligned variant execution |
| derived seed 4 | `1146911492` | one future lifecycle-aligned variant execution |

The four new values are not manually selected. Remove the `sha256:` prefix from the immutable anchor
artifact digest
`11e9d9a8e5f8e65474406524445c7b04fe3d9af5afa6d137847c913f8e66ae04`, split the digest into 32-bit
big-endian words, take the first four words, and reduce each modulo `2147483647`.

This produces a deterministic, outcome-independent seed set while retaining seed `42` as the direct link
to the completed paired attribution.

## Frozen behavioral inputs

A future execution may change only:

```text
freqai.model_training_parameters.seed
```

The following remain fixed at the paired-attribution identities and values:

- model `DesiredPositionReinforcementLearner`;
- strategy `AiDesiredPositionRLLifecycleAlignedResearchStrategy`;
- only lifecycle semantic delta `ignore_roi_if_entry_signal=True`;
- PPO / `MlpPolicy`;
- `n_steps=128`, `batch_size=64`, `train_cycles=1`;
- reward reference and all reward constants;
- desired-position action space and transition semantics;
- entry threshold `0.006`, exit threshold `-0.009`;
- `data_split_parameters.random_state=42`, `shuffle=false`;
- BTC/USDT and ETH/USDT;
- 15m, 1h and 4h timeframes;
- Kraken spot and fee `0.002`;
- download `20250801-20260501`, execution `20260301-20260501`, semantic window
  `20260301-20260430`;
- train/backtest geometry `90/61` days.

A per-seed FreqAI identifier, artifact name and temporary output path may differ only to prevent collisions
and bind provenance. They are not behavioral degrees of freedom.

## Execution geometry for a later task

This declaration permits a later, separately reviewed infrastructure and trigger sequence to propose:

- four new variant training/backtest executions, one for each derived seed;
- zero execution for seed `42`;
- zero baseline execution;
- reuse of the immutable seed-42 evidence;
- reuse or bounded preparation of only the already declared pre-OOS market data;
- one immutable evidence artifact per new seed plus one aggregate five-seed record.

No workflow, request file, cache access, market-data download, training or backtest is introduced here.

## Per-seed validity gate

Each new seed is valid only when all conditions hold:

1. exactly one lifecycle-aligned backtest archive is produced;
2. the execution contains only the frozen model, strategy, pairs, timeframes, fee and geometry;
3. both BTC/USDT and ETH/USDT produce at least one completed trade;
4. total trade count is at least `20`;
5. at least one `freqai_rl_v2_target_flat` exit is present;
6. rejected signals, timed-out entry orders and timed-out exit orders are all zero;
7. consumed historical OOS and protected final-holdout access are both false;
8. accounting, request hashes, runtime configuration and raw-trade evidence reconcile.

The trade-count and pair/path requirements are non-degeneracy checks only. They are not profitability or
selection thresholds. Any invalid seed makes the aggregate result `inconclusive`; it must not be silently
removed or replaced with a different seed.

## Frozen mechanism criteria

The immutable baseline values remain:

- ROI exit followed by same-pair 15-minute re-entry: `122`;
- immediate external exit/re-entry boundary count: `131`;
- associated boundary fees: `52.582123 USDT`.

For each of the five seeds, the original paired directional criteria remain mandatory:

- ROI-to-15m re-entry count `< 122`;
- external boundary fees `< 52.582123 USDT`.

To distinguish repeatable strong reduction from a marginal pass, the aggregate robustness gate also
requires at least four of five seeds to meet both stronger criteria:

- ROI-to-15m re-entry count `<= 30`, representing at least a 75% reduction from baseline;
- external boundary fees `<= 13.145531 USDT`, representing at least a 75% reduction from baseline.

The anchor seed `42` contributes its immutable values `0` and `0.0 USDT`; it is not recomputed.

## Decision rule

The aggregate classification is determined without discretion after results are available:

- **supported** — all five seeds are valid, every seed meets both original directional criteria, and at
  least four seeds meet both strong-reduction criteria;
- **not supported** — all five seeds are valid but either directional consistency requirement fails;
- **inconclusive** — any seed fails execution, provenance, accounting or non-degeneracy validation.

A failed or inconclusive seed cannot be replaced. A second seed set would require a new declaration and
would not erase this result.

## Descriptive-only outputs

The following must be reported for every seed and in aggregate, but cannot change the decision:

- trades, exposure, exit-reason counts and duration distribution;
- gross price PnL, fees and net PnL;
- profit factor and maximum drawdown;
- pair and realized-month decomposition;
- win rate, median trade and p-value;
- target-flat and stop-loss observations.

Positive returns, a favorable median, statistical significance or lower drawdown do not authorize
profitability, superiority, ranking or promotion claims. Five seeds are an exploratory robustness set, not
statistical proof.

## Isolation and next boundary

The immutable baseline must not be rerun. The consumed historical OOS window `20260501-20260630` and the
protected final holdout `20260801-20260930` remain forbidden. Phase 6 remains complete with authoritative
`selected_model=null`.

After this declaration merges, any implementation must be a separate inert infrastructure task. Any
actual four-seed execution must then require a fresh canonical exact-scope trigger and must be closed
without merge after terminal evidence is captured. This declaration does not authorize either step.
