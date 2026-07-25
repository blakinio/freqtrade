# RL-v2 Paired Attribution Interpretation

## Scope and classification

This report interprets the immutable lifecycle paired-attribution evidence produced by workflow run
`30131273189` and trigger PR `#272`.

The source artifact is:

- `rl-v2-roi-lifecycle-paired-attribution-272`;
- digest `sha256:11e9d9a8e5f8e65474406524445c7b04fe3d9af5afa6d137847c913f8e66ae04`;
- execution head `ce83a3e52ab6bc8676072522e266dcf50bd692e7`.

The evidence remains classified as `paired_historical_development_attribution` with
`strict_oos=false`, `protected_final_validation=false`, and profitability explicitly non-gating.
This interpretation performs no model training, backtest, data download, cache restore, baseline rerun,
retuning, ranking or promotion.

## Frozen comparison

The immutable baseline is artifact `rl-v2-historical-training-execution-218`, digest
`sha256:5d74d87bf4408c7b51779cd9038d815c88d3f5cc193cd229b6757edf32112b55`.
The paired variant changed only `ignore_roi_if_entry_signal=True` in
`AiDesiredPositionRLLifecycleAlignedResearchStrategy`.

| Measure | Baseline | Variant | Delta | Interpretation |
|---|---:|---:|---:|---|
| ROI exit followed by same-pair 15m re-entry | `122` | `0` | `-122` | primary frozen criterion met |
| Immediate external-exit/re-entry boundaries | `131` | `0` | `-131` | diagnosed churn mechanism absent |
| Boundary close-plus-reopen fees | `52.582123 USDT` | `0.0 USDT` | `-52.582123 USDT` | primary frozen criterion met |
| ROI exits | `122` | `2` | `-120` | descriptive lifecycle change |
| Trades | `174` | `45` | `-129` | exposure path changed materially |
| Total fees | `69.643465 USDT` | `18.059698 USDT` | `-51.583767 USDT` | descriptive, path-dependent |
| Gross price PnL | `21.791297 USDT` | `29.866574 USDT` | `+8.075277 USDT` | descriptive, path-dependent |
| Net PnL | `-47.852168 USDT` | `+11.806876 USDT` | `+59.659044 USDT` | non-gating and not causal proof |

Both prospectively frozen directional criteria passed. The selected lifecycle hypothesis is therefore
supported on this reused historical-development path: inherited ROI exits no longer created the defined
immediate close-and-reopen cycle while the policy still requested a long position.

## What the result proves

The evidence supports one narrow mechanistic statement:

> With all declared model, reward, feature, threshold, pair, timeframe, fee, stop-loss and geometry inputs
> frozen, enabling `ignore_roi_if_entry_signal` removed the prospectively defined immediate ROI-exit and
> same-pair re-entry mechanism in the March-April historical-development execution.

This statement is supported because:

1. the strategy change was isolated to one lifecycle flag;
2. the primary metrics and thresholds were frozen before execution;
3. the baseline was immutable and not rerun;
4. the variant execution produced zero qualifying re-entry boundaries and zero associated boundary fees.

## What the result does not prove

The result does not establish that the variant is profitable, superior, robust or ready for promotion.
The changed lifecycle altered trade duration, exposure and future decision paths. Consequently, the
`+59.659044 USDT` net-PnL difference cannot be decomposed into a causal boundary-fee saving plus an
independent trading edge.

The evidence also does not establish:

- strict out-of-sample generalization;
- protected final-holdout performance;
- PPO convergence or stability;
- robustness across random seeds;
- robustness across market regimes or time windows;
- superiority over PyTorch, LightGBM, XGBoost or any Phase 6 candidate;
- authorization for dry-run, shadow, live-small or live operation.

Phase 6 remains complete with authoritative `selected_model=null`.

## Secondary raw-trade observation

A deterministic decomposition of the variant raw backtest archive gives:

| Exit reason | Trades | Gross price PnL | Fees | Net PnL | Net wins | Median duration |
|---|---:|---:|---:|---:|---:|---:|
| `freqai_rl_v2_target_flat` | `40` | `+30.781068` | `16.061529` | `+14.719539` | `11` | `577.5 min` |
| `roi` | `2` | `+6.124014` | `0.812247` | `+5.311767` | `2` | `6412.5 min` |
| `stop_loss` | `1` | `-4.999637` | `0.390001` | `-5.389638` | `0` | `4665 min` |
| `force_exit` | `2` | `-2.038871` | `0.795921` | `-2.834793` | `1` | `9307.5 min` |

The baseline diagnosis had identified strongly negative target-flat exits. That pattern did not recur in
aggregate in this particular variant path. This does not isolate or resolve target-flat quality because
the lifecycle change materially changed the states, exposure and timing presented to the policy.
No target-flat, reward or action-semantics change is authorized from this observation.

## Research decision

The lifecycle-aligned strategy remains an experiment. The paired evidence should be retained as a
successful mechanism attribution, not converted into a candidate or promotion record.

Before considering another policy-semantic change, the next research package should be a separately
prospective **seed-robustness declaration** for the unchanged lifecycle-aligned variant. That declaration
must freeze:

- a finite seed set before execution;
- identical model, strategy, reward, features, thresholds, pairs, timeframes, fees and geometry;
- the same `paired_historical_development_attribution` classification for reused data;
- mechanism-consistency and dispersion criteria before results are observed;
- the immutable baseline without rerunning it;
- a prohibition on consumed historical OOS and protected final-holdout access;
- no profitability, ranking, superiority, promotion or deployment conclusion.

This report does not authorize that execution. It defines only the next legal declaration boundary.
