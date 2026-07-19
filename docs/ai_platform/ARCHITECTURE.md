# AI Trading Platform Architecture

## 1. Mission

Build a reproducible research-to-execution platform on top of Freqtrade that can discover, train, validate, rank, and operate trading strategies without giving an ML model unrestricted control over capital.

The system optimizes for robustness, reproducibility, and controlled risk rather than maximum backtest profit.

## 2. Core design rule

```text
Market data
    |
    v
Feature engineering / context
    |
    +-------------------+
    |                   |
    v                   v
FreqAI prediction   Strategy discovery
    |                   |
    +---------+---------+
              |
              v
       Deterministic strategy
              |
              v
          Risk gates
              |
              v
         Freqtrade core
              |
              v
           Exchange
```

FreqAI produces predictions. Strategy logic interprets them. Risk rules can veto trades. Freqtrade owns execution and trade lifecycle.

## 3. Upstream isolation

Project-specific work should live outside Freqtrade core whenever possible:

```text
ai_platform/
  configs/
  strategies/
  research/
  discovery/
  validation/
  registry/
  monitoring/

docs/ai_platform/
```

This reduces conflicts when synchronizing the fork with `freqtrade/freqtrade`.

## 4. Runtime layers

### 4.1 Market data

Initial universe:

- BTC/USDT
- ETH/USDT

Initial timeframes:

- 15m base timeframe;
- 1h context;
- 4h context.

The initial baseline intentionally avoids a large dynamic universe. Pair expansion is a later phase after the validation pipeline is stable.

### 4.2 Feature layer

Feature families:

- returns and price change;
- RSI/MFI momentum;
- ADX trend strength;
- EMA trend context;
- ATR-normalized volatility;
- relative volume;
- hour-of-day and day-of-week context.

Features should be small and interpretable first. FreqAI can multiply features across indicator periods, timeframes, shifted candles, and correlated pairs, so feature-count growth must be tracked explicitly.

### 4.3 Prediction layer

Baseline model:

`LightGBMRegressor`

Baseline target:

future average return over the configured label horizon.

The model predicts expected return; it does not emit an unconditional order.

Example interpretation:

```text
prediction > entry threshold
AND do_predict == 1
AND deterministic risk checks pass
=> candidate entry
```

Later model comparison can include XGBoost and custom/PyTorch models. More complex models must beat the baseline on out-of-sample trading metrics before adoption.

### 4.4 Strategy layer

The initial strategy is deliberately simple and research-only:

- long-only spot;
- prediction-gated entries;
- prediction-based exits;
- hard stop-loss;
- no leverage;
- dry-run configuration.

Later strategies may add regime filters, volatility filters, portfolio context, and ensemble agreement.

### 4.5 Risk layer

Risk controls remain deterministic and independent from model confidence.

Target controls:

- maximum open trades;
- maximum exposure per asset;
- maximum daily loss;
- maximum rolling drawdown;
- stop-loss guard;
- cooldown after losses;
- stale model/data rejection;
- kill switch for exchange/API instability.

The MVP uses Freqtrade-native limits where available. Portfolio-level controls are added in later phases.

## 5. Research architecture

```text
Hypothesis
   |
   v
Strategy candidate
   |
   v
Backtest
   |
   v
Hyperparameter optimization
   |
   v
Out-of-sample test
   |
   v
Walk-forward evaluation
   |
   +--> lookahead-analysis
   |
   +--> recursive-analysis
   |
   v
Candidate scoring
   |
   +--> reject
   |
   v
Strategy registry
   |
   v
Dry-run
```

A candidate must never be promoted solely because of one profitable backtest.

## 6. Strategy discovery

The future discovery engine is a research orchestrator, not a live trader.

It may generate hypotheses from:

- trend following;
- momentum;
- mean reversion;
- volatility breakout;
- volume/liquidity context;
- cross-asset BTC/ETH context;
- market-regime classification;
- public strategy ideas used as inspiration where licensing permits;
- prior experiment results.

Generated candidates must compile and pass the same validation funnel as manually authored strategies.

## 7. Experiment registry

Every experiment should become reproducible metadata.

Minimum record:

```text
experiment_id
strategy_name
strategy_version
git_commit
freqtrade_version
freqai_identifier
model_type
feature_set
target_definition
training_window
validation_window
pairs
timeframes
model_parameters
strategy_parameters
fees_assumption
trade_count
profit
max_drawdown
sharpe_or_sortino
out_of_sample_metrics
walk_forward_metrics
lookahead_status
recursive_analysis_status
promotion_status
```

Storage implementation is intentionally deferred until the baseline produces real experiments. The initial implementation can start with structured JSON/Parquet artifacts and later move to PostgreSQL if needed.

## 8. Model lifecycle

```text
train
  |
  v
validate
  |
  v
register
  |
  v
serve predictions
  |
  v
monitor drift/performance
  |
  +--> retrain
  |
  +--> retire
```

Model identity must be tied to:

- FreqAI identifier;
- feature definition;
- target definition;
- training window;
- model parameters;
- code revision.

Changing any of these should create a new experiment identity.

## 9. Strategy lifecycle

```text
experiment
  -> candidate
  -> validated
  -> dry-run
  -> shadow
  -> live-small
  -> production
  -> retired
```

The current project scope ends at dry-run until a separate live-capital work package is explicitly approved.

## 10. Validation model

### 10.1 Backtest

Used for fast candidate rejection and basic economics.

### 10.2 Out-of-sample

The final evaluation segment must not be used for tuning.

### 10.3 Walk-forward

Recommended structure:

```text
train A -> test B
train B -> test C
train C -> test D
```

Exact windows are strategy/timeframe dependent and must be recorded with results.

### 10.4 Bias checks

Required before validation status:

- `lookahead-analysis`;
- `recursive-analysis` review.

### 10.5 Stress checks

Later phases should vary:

- fees;
- slippage assumptions;
- entry/exit delay;
- market subperiods;
- parameter perturbations.

A strategy should fail promotion if small parameter changes collapse performance.

## 11. Infrastructure separation

### Research environment

Purpose:

- historical data download;
- feature experiments;
- backtests;
- Hyperopt;
- walk-forward runs;
- model comparison.

Expected to be CPU/GPU intensive.

### Execution environment

Purpose:

- stable dry-run/live-small operation;
- inference/retraining;
- exchange connectivity;
- monitoring.

Research experiments must not mutate production configuration automatically.

## 12. Security boundary

- Exchange credentials are never committed.
- Withdrawal permission must remain disabled.
- Research and future production credentials should be separate.
- API/UI should not be exposed directly to the public Internet without an authenticated secure access layer.
- The baseline config contains no real credentials and is `dry_run` by default.

## 13. MVP definition

The first useful milestone is:

```text
one exchange
spot only
BTC/USDT + ETH/USDT
15m base timeframe
1h + 4h context
LightGBMRegressor
future-return target
controlled feature set
reproducible backtest
walk-forward design
bias checks
dry-run only
```

Success is not defined as profitability. MVP success means the full research path is reproducible and produces trustworthy evidence for or against a candidate.

## 14. Non-goals for MVP

- leverage/futures;
- reinforcement learning;
- autonomous live-capital promotion;
- high-frequency trading;
- order-flow integration;
- hundreds of pairs;
- deep-learning complexity without baseline evidence;
- direct core forks where extension points are sufficient.

## 15. Architectural evolution

After the baseline validation pipeline is working:

1. automate experiment manifests and result collection;
2. implement walk-forward orchestration;
3. add candidate scoring and registry states;
4. compare LightGBM and XGBoost;
5. introduce market-regime features/filters;
6. add ensemble logic only if individual models are complementary out-of-sample;
7. add monitoring and drift detection;
8. consider live-small only under a separate reviewed scope.
