# RL-v2 Seed Validity Diagnosis

## Result

The immutable evidence is internally consistent. No artifact, runtime-configuration, strategy-hash, trade-accounting, data-coverage or aggregate-evidence defect explains the two invalid seeds.

The frozen lifecycle seed-robustness decision remains **`inconclusive`**. Seeds `1710810709` and `1950377252` remain invalid because they completed `14` and `13` trades, below the prospectively frozen minimum of `20`. They may not be rerun, replaced or reclassified.

The observed low-turnover pattern is associated with **much longer completed position durations and much wider completed-position initiation spacing**, not with long periods spent flat. The immutable artifacts do not contain per-candle action or prediction timelines, so a causal claim about PPO action persistence or entry suppression remains **unknown**.

## Scope and method

This diagnosis used only the exact immutable aggregate, anchor and four new-seed artifacts declared in `RL_V2_SEED_VALIDITY_DIAGNOSIS_DECLARATION.md`. It executed no model, training, backtest, market-data download, cache restore, baseline or seed operation.

Deterministic calculations were made from recorded completed trades and embedded configurations over execution timerange `20260301-20260501` (`61` days, `87,840` minutes). Occupancy is the union of recorded open-to-close intervals. Same-pair flat gap is the interval from one completed trade's close to the next completed trade's open for that pair.

## Evidence integrity

All six downloaded artifact SHA-256 values exactly matched the frozen declarations. For every seed:

- the raw embedded backtest configuration reconciled with `effective-runtime-config.json` after the extractor's documented normalization;
- the embedded strategy source SHA-256 was `366785129798d1332ce593f919c54aa23eefb2b15b2d850ab32d5c5cbdf0d5b7`;
- each new seed's normalized runtime-config SHA-256 matched its accepted `seed-evidence.json`;
- raw trade counts matched backtest summaries;
- each trade satisfied `gross price PnL - recorded fees = profit_abs` within `5e-9 USDT` maximum absolute error;
- recomputed aggregate descriptive metrics matched the accepted evidence;
- all five data-coverage records were identical and stopped at the exclusive `2026-05-01T00:00:00Z` boundary.

No error, critical message or traceback was recorded. Each run contained the same non-fatal FreqAI exchange-check override warning.

## Completed-trade geometry

| Seed | Status | Trades | BTC / ETH | Initiations/day | Median duration | Any-position occupancy |
|---|---:|---:|---:|---:|---:|---:|
| `42` | valid anchor | 45 | 32 / 13 | 0.738 | 1,065 min | 98.941% |
| `300538280` | valid | 280 | 96 / 184 | 4.590 | 150 min | 82.650% |
| `1710810709` | invalid | 14 | 8 / 6 | 0.230 | 10,837.5 min | 99.915% |
| `1950377252` | invalid | 13 | 8 / 5 | 0.213 | 10,260 min | 99.915% |
| `1146911492` | valid | 29 | 6 / 23 | 0.475 | 3,855 min | 99.949% |

The valid-set medians are `45` trades, `0.738` initiations/day, `1,065` minutes median duration and `98.941%` any-position occupancy.

Compared with those medians:

- seed `1710810709` produced `31` fewer trades (`0.311x`) and a median duration `9,772.5` minutes longer (`10.176x`), while occupancy was only `0.973` percentage points higher;
- seed `1950377252` produced `32` fewer trades (`0.289x`) and a median duration `9,195` minutes longer (`9.634x`), while occupancy was also only `0.973` percentage points higher.

Thus almost-continuous portfolio occupancy alone does not distinguish the invalid seeds: valid seed `1146911492` also occupied the portfolio for `99.949%` of the window. The distinguishing descriptive feature is how that occupancy was segmented into completed positions.

## Pair-level comparison

| Metric | Valid-set median | Seed `1710810709` | Ratio | Seed `1950377252` | Ratio |
|---|---:|---:|---:|---:|---:|
| BTC trades | 32 | 8 | 0.250x | 8 | 0.250x |
| BTC median duration | 577.5 min | 8,160 min | 14.130x | 8,797.5 min | 15.234x |
| BTC occupancy | 96.226% | 99.163% | 1.031x | 99.744% | 1.037x |
| BTC median inter-initiation interval | 630 min | 6,075 min | 9.643x | 10,320 min | 16.381x |
| BTC median flat gap | 75 min | 60 min | 0.800x | 30 min | 0.400x |
| ETH trades | 23 | 6 | 0.261x | 5 | 0.217x |
| ETH median duration | 3,285 min | 14,152.5 min | 4.308x | 16,890 min | 5.142x |
| ETH occupancy | 98.600% | 99.761% | 1.012x | 99.880% | 1.013x |
| ETH median inter-initiation interval | 3,637.5 min | 11,430 min | 3.142x | 16,710 min | 4.594x |
| ETH median flat gap | 52.5 min | 45 min | 0.857x | 15 min | 0.286x |

Neither invalid seed has longer median flat gaps than the valid-set median. Their sparse completed-trade counts are therefore not observationally associated with prolonged post-close inactivity. They are associated with positions remaining open for substantially longer before the next completed-position initiation.

## Month and exit-reason decomposition

| Seed | Mar closes | Apr closes | May boundary closes | Target-flat | ROI | Stop-loss | Force-exit |
|---|---:|---:|---:|---:|---:|---:|---:|
| `42` | 28 | 15 | 2 | 40 | 2 | 1 | 2 |
| `300538280` | 149 | 129 | 2 | 278 | 0 | 0 | 2 |
| `1710810709` | 8 | 4 | 2 | 6 | 3 | 3 | 2 |
| `1950377252` | 5 | 6 | 2 | 6 | 2 | 3 | 2 |
| `1146911492` | 16 | 11 | 2 | 20 | 2 | 5 | 2 |

The two May records per seed are force exits at the execution boundary. Both invalid seeds otherwise show closely similar lifecycle outcomes: each has `8` BTC trades, `6` target-flat exits, `3` stop-loss exits, `2` force exits, identical primary mechanism metrics and exactly `87,765` minutes with at least one position open. Their overall median durations differ by only `577.5` minutes (`5.5%` relative difference).

## Action-level evidence limit

Each raw archive contains:

- one completed-trade result JSON;
- one embedded runtime config;
- the lifecycle-aligned strategy source;
- a wallet Feather file with columns `index`, `date`, `currency`, `rate`, `balance`, `total_quote`;
- a market-change Feather file with columns `date`, `mean`, `rel_mean`, `count`.

The archives contain no per-candle action, target, prediction or model-state timeline. Runtime logs reference transient `backtesting_predictions/..._prediction.feather` paths, but those files were not retained in the immutable artifacts.

Consequently:

- repeated PPO hold actions cannot be proven;
- suppressed entry actions while flat cannot be proven;
- the observed completed-trade geometry supports only the descriptive statement that long-held positions and widely spaced completed-position initiations coincide with the invalid seeds.

## Frozen interpretation

- Evidence classification: `paired_historical_development_seed_validity_diagnosis`.
- `strict_oos=false`.
- `protected_final_validation=false`.
- Profitability remains descriptive and non-gating.
- Consumed historical OOS and the protected final holdout were not accessed.
- No automatic ranking, promotion, dry-run or live action is authorized.
- Phase 6 remains complete with authoritative `selected_model=null`.
- The lifecycle seed-robustness decision remains `inconclusive`.

Any action-level instrumentation or further experiment requires a new prospective declaration. It cannot replace, rescue or erase this completed result.
