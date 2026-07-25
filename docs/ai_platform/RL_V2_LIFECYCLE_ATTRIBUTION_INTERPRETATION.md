# RL-v2 Lifecycle Attribution Interpretation

## Scope

This document interprets the immutable paired historical-development artifact produced by workflow run
`30131273189` / trigger PR `#272`.

The task is analysis-only:

- no new model training;
- no new backtest;
- no market-data download or access;
- no baseline rerun;
- no PPO, reward, feature, threshold, pair, timeframe, fee, stop-loss, ROI schedule, or action-semantics change;
- no ranking, promotion, dry-run, live-trading, profitability, or superiority conclusion;
- no access to consumed historical OOS `20260501-20260630`;
- no access to protected final holdout `20260801-20260930`.

The source remains classified as `paired_historical_development_attribution` with `strict_oos=false` and
`protected_final_validation=false`.

## Source identity

- Workflow run: `30131273189`
- Trigger PR: `#272`, closed without merge
- Execution head: `ce83a3e52ab6bc8676072522e266dcf50bd692e7`
- Artifact: `rl-v2-roi-lifecycle-paired-attribution-272`
- Artifact digest: `sha256:11e9d9a8e5f8e65474406524445c7b04fe3d9af5afa6d137847c913f8e66ae04`
- Semantic evidence window: `20260301-20260430`
- Starting balance: `10000 USDT`
- Stake per trade: approximately `100 USDT`
- Fee assumption: `0.002` on entry and `0.002` on exit
- Only declared semantic delta: `ignore_roi_if_entry_signal = True`

The downloaded ZIP digest was recalculated locally and matched the immutable artifact digest. The raw
backtest result, paired-attribution payload, metadata, coverage, runtime config, and raw backtest archive
are individually hash-bound in
`ai_platform/experimental_model_research/rl-v2-lifecycle-attribution-interpretation-v1.json`.

## Accounting reconciliation

The 45 completed variant trades produced:

| Measure | Value |
|---|---:|
| Gross price PnL before fees | `+29.866574 USDT` |
| Entry plus exit fees | `-18.059698 USDT` |
| Net backtest result | `+11.806876 USDT` |
| Gross-positive trades | `16 / 45` |
| Net-positive trades | `14 / 45` |
| Gross-positive trades converted to net losses by fees | `2` |
| Average round-trip fee per trade | `0.401327 USDT` |
| Median net trade | `-0.866404 USDT` |
| Profit factor | `1.251195` |
| Maximum absolute drawdown | `26.728284 USDT` |
| Reported p-value | `0.627831` |

These profitability values are descriptive only. The median trade is negative, the win rate is
`31.11%`, and the three largest winners contributed `30.077937 USDT`, which exceeds the complete net
result before losses are offset.

## Pair decomposition

| Pair | Trades | Gross price PnL | Fees | Net PnL | Net wins | Median duration |
|---|---:|---:|---:|---:|---:|---:|
| `BTC/USDT` | 32 | `+11.559041` | `-12.823084` | `-1.264043` | 9 | `577.5 min` |
| `ETH/USDT` | 13 | `+18.307533` | `-5.236615` | `+13.070919` | 5 | `6255 min` |

The aggregate positive result is not cross-pair consistent. ETH supplied more than the full net result,
while BTC remained slightly negative.

## Realized close-month decomposition

| Realized close month | Trades | Gross price PnL | Fees | Net PnL | Net wins |
|---|---:|---:|---:|---:|---:|
| March 2026 | 28 | `+2.865606` | `-11.205713` | `-8.340107` | 6 |
| April 2026 | 15 | `+29.039840` | `-6.058064` | `+22.981776` | 7 |
| May 1 terminal force exits | 2 | `-2.038871` | `-0.795921` | `-2.834793` | 1 |

March was negative and April carried the result. The May rows are terminal end-of-run force closures,
not a separate May evidence window. Cross-month robustness is not established.

## Exit-reason decomposition

| Exit reason | Trades | Gross price PnL | Fees | Net PnL | Net wins | Median duration |
|---|---:|---:|---:|---:|---:|---:|
| `freqai_rl_v2_target_flat` | 40 | `+30.781068` | `-16.061529` | `+14.719539` | 11 | `577.5 min` |
| `roi` | 2 | `+6.124014` | `-0.812247` | `+5.311767` | 2 | `6412.5 min` |
| `stop_loss` | 1 | `-4.999637` | `-0.390001` | `-5.389638` | 0 | `4665 min` |
| `force_exit` | 2 | `-2.038871` | `-0.795921` | `-2.834793` | 1 | `9307.5 min` |

ROI, hard stop-loss, policy target-flat exits, and terminal force exits all remained operational. The
selected flag did not globally disable ROI or remove deterministic risk exits.

## Primary conclusion: targeted lifecycle mechanism resolved in this window

The prospectively frozen comparison was:

| Primary mechanism measure | Immutable baseline | Lifecycle variant | Delta |
|---|---:|---:|---:|
| ROI exit followed by same-pair 15-minute re-entry | 122 | 0 | -122 |
| Immediate external ROI/stop-loss exit and re-entry boundaries | 131 | 0 | -131 |
| Close-plus-reopen fees at those boundaries | `52.582123 USDT` | `0.0 USDT` | `-52.582123 USDT` |

Both variant ROI exits were followed by the next same-pair entry after 45 minutes, and the one stop-loss
exit was followed after 135 minutes. None reproduced the targeted one-candle external-exit/re-entry
boundary.

This supports, with high confidence for this mechanism only, the original diagnosis that inherited ROI
handling conflicted with an active desired-long policy state. It does not prove future profitability,
PPO quality, strict-OOS generalization, or promotion readiness.

## Non-degeneracy checks

The zero targeted-churn result is not explained by a zero-trade strategy or by disabling exits:

- 45 trades executed across both declared pairs;
- BTC exposure covered `96.23%` of the 61-day execution interval;
- ETH exposure covered `98.67%` of the interval;
- both positions were concurrently active for `95.95%` of the interval;
- 40 policy-driven target-flat exits executed;
- 2 ROI exits, 1 hard stop-loss exit, and 2 terminal force exits executed;
- there were no rejected signals or timed-out entry/exit orders.

The variant reduced trade count from 174 to 45 because long-policy persistence was no longer interrupted
by the targeted external ROI churn. That is a lifecycle-path change, not evidence that the model became
more accurate.

## Separate remaining observation

Eight target-flat exits were followed by a new same-pair entry exactly one 15-minute candle later. This
matches the count observed in the immutable baseline diagnosis for the policy-driven target-flat path.
It is separate from the repaired external ROI/stop-loss mechanism.

This observation does not authorize reward, PPO, feature, threshold, or action-semantics retuning on the
reused March-April window. The downstream target-flat PnL also cannot be interpreted as an independently
improved policy because the lifecycle change altered exposure and the full trade path.

## Interpretation boundary

The correct conclusion is:

> The single prospectively selected lifecycle flag removed the diagnosed inherited external
> ROI/stop-loss immediate re-entry mechanism in the reused historical-development window without
> degenerating into zero trading or disabling exits.

The evidence does **not** establish:

- strict-OOS or protected-final performance;
- cross-pair or cross-month profitability robustness;
- model superiority or ranking;
- Phase 6 selection eligibility;
- dry-run, shadow, live-small, or production readiness.

Phase 6 authoritative `selected_model = null` remains unchanged.

## Future policy

RL-v2 experimentation should now pause. Any future execution requires a separate prospectively declared
work package with frozen inputs and a fresh non-contaminated evidence window. This task does not authorize
that work package, baseline rerun, same-window retuning, consumed historical OOS access, or protected
final holdout access.
