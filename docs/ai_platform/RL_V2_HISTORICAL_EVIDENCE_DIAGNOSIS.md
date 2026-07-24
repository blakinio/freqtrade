# RL-v2 Historical Evidence Diagnosis

## Scope

This document diagnoses the immutable historical-development artifact produced by workflow run
`30022863894` / trigger PR `#218`.

The diagnosis is analysis-only:

- no new model training;
- no new backtest;
- no market-data download or access;
- no retuning of PPO, policy, reward, features, thresholds, pairs, fee assumptions, or execution geometry;
- no ranking, promotion, profitability, or superiority conclusion;
- no access to consumed historical OOS `20260501-20260630`;
- no access to protected final holdout `20260801-20260930`.

The source remains classified as `historical_development_evidence` with `strict_oos=false`.

## Source identity

- Workflow run: `30022863894`
- Trigger PR: `#218`, closed without merge
- Execution head: `36f175477c848ae2ecfc92dbd335d7573af4933d`
- Artifact: `rl-v2-historical-training-execution-218`
- Artifact digest: `sha256:5d74d87bf4408c7b51779cd9038d815c88d3f5cc193cd229b6757edf32112b55`
- Evidence window: `20260301-20260430`
- Starting balance: `10000 USDT`
- Stake per trade: approximately `100 USDT`
- Fee assumption: `0.002` on entry and `0.002` on exit

## Accounting decomposition

The 174 completed trades produced:

| Measure | Value |
|---|---:|
| Gross price PnL before fees | `+21.791297 USDT` |
| Entry plus exit fees | `-69.643465 USDT` |
| Net backtest result | `-47.852168 USDT` |
| Gross return on starting balance | `+0.2179%` |
| Fee drag on starting balance | `-0.6964%` |
| Net return on starting balance | `-0.4785%` |
| Gross-positive trades | `124 / 174` |
| Net-positive trades | `89 / 174` |
| Gross-positive trades converted to net losses by fees | `35` |
| Average round-trip fee per trade | `0.400250 USDT` |
| Median holding duration | `720 minutes` |

The negative result is therefore not explained solely by adverse price direction. Gross price movement
was positive in aggregate, but transaction costs were more than three times the gross price PnL.

## Pair decomposition

| Pair | Trades | Gross price PnL | Fees | Net PnL | Gross-positive | Net wins |
|---|---:|---:|---:|---:|---:|---:|
| `BTC/USDT` | 93 | `+9.102588` | `-37.218091` | `-28.115502` | 62 | 42 |
| `ETH/USDT` | 81 | `+12.688709` | `-32.425374` | `-19.736665` | 62 | 47 |

The same mechanism is present in both pairs; the total loss is not isolated to one instrument.

## Exit-reason decomposition

| Exit reason | Trades | Gross price PnL | Fees | Net PnL | Net wins | Median duration |
|---|---:|---:|---:|---:|---:|---:|
| `roi` | 122 | `+136.102404` | `-49.072122` | `+87.030282` | 88 | 720 min |
| `freqai_rl_v2_target_flat` | 39 | `-58.907848` | `-15.482153` | `-74.390001` | 1 | 225 min |
| `stop_loss` | 11 | `-54.998259` | `-4.290001` | `-59.288261` | 0 | 1380 min |
| `force_exit` | 2 | `-0.404999` | `-0.799189` | `-1.204188` | 0 | 375 min |

Two separate observations follow:

1. Policy-driven `target_flat` exits are strongly loss-concentrated and remain a later research question.
2. The larger lifecycle mismatch is visible around external ROI and stop-loss exits followed by immediate
   re-entry.

These mechanisms must not be modified in the same future experiment.

## Primary diagnosis: desired-position lifecycle conflicts with inherited ROI exits

`AiDesiredPositionRLResearchStrategy` correctly maps:

- action `0` to `target_flat`;
- action `1` to `target_long`.

The strategy nevertheless inherits this deterministic ROI schedule from
`AiLongOnlyRLResearchStrategy`:

```python
minimal_roi = {
    "0": 0.03,
    "240": 0.015,
    "720": 0.0,
}
```

After 720 minutes, a trade with any positive gross price movement may be closed by the ROI subsystem,
even when the next accepted policy decision still requests `target_long`.

The artifact shows:

- all `122` ROI exits had positive gross price PnL;
- `34` of those trades became net losses after fees;
- every one of the `122` ROI exits was followed by a new entry in the same pair exactly one 15-minute
  candle later;
- `9` of the `11` stop-loss exits were also followed by re-entry after exactly 15 minutes;
- ROI plus stop-loss produced `131` immediate external-exit/re-entry boundaries;
- close-plus-reopen fees at those boundaries totaled `52.582123 USDT`.

That boundary fee amount exceeds the complete net loss of `47.852168 USDT`.

This is an accounting diagnosis, not a counterfactual performance result. Removing those boundaries
would alter exposure, risk, and price paths; the evidence does not authorize a claim that disabling ROI
would have made the strategy profitable.

## Secondary observation: target-flat exit quality

The policy-driven exit path also requires separate investigation:

- `39` target-flat exits;
- `-58.907848 USDT` gross price PnL;
- `-74.390001 USDT` net PnL;
- `38 / 39` net losses;
- median duration `225 minutes`.

This suggests that `target_flat` frequently arrives after an adverse move. However, changing reward,
features, PPO parameters, or action semantics together with lifecycle behavior would make attribution
impossible. It is therefore not selected as the first experiment.

## Training-log observation

The two pair training evaluations completed at `6878` timesteps with episode rewards approximately
`-26.16` and `-25.76`, each over `1718` steps.

Those values confirm that training completed but are insufficient to diagnose model quality in
isolation. The artifact does not contain a full action-time-series export or multiple seeds, so this
task does not infer PPO stability or convergence.

## Selected next hypothesis

The only recommended next experiment is a single-variable lifecycle-alignment task:

> Prospectively prevent inherited ROI profit-taking from closing a position while the frozen policy
> still requests `target_long`, while preserving the hard stop-loss and every frozen PPO, reward,
> feature, fee, pair, threshold, and action-semantics input.

This diagnosis does **not** authorize that experiment. A separate task must prospectively define:

- the exact one-variable strategy change;
- a non-overlapping or otherwise honestly classified development evaluation window;
- execution and evidence semantics;
- immutable input hashes;
- the rule that the result cannot be labeled strict OOS or final validation unless separately
  authorized.

## Rejected actions

- Re-run the completed `#218` trigger.
- Tune PPO, reward, features, thresholds, ROI, stop-loss, and cooldown simultaneously.
- Use consumed historical OOS `20260501-20260630`.
- Access protected final holdout `20260801-20260930`.
- Treat March-April evidence as strict OOS.
- Rank RL-v2 against PyTorch or Phase 6 candidates.
- Infer promotion or profitability from this diagnosis.
