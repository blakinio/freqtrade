# Experimental Model Historical Backtest Evidence v1

This document preserves the durable repository-level summary of the one-shot historical execution for the two isolated experimental research tracks:

- `pytorch-research-v1`;
- `rl-research-v1`.

The execution was triggered by PR #94 and completed in GitHub Actions workflow run `29844351936`. PR #94 was an execution carrier only and was closed without merge after artifact collection.

The two tracks remain independent. This evidence does not define or imply a cross-track ranking, model selection, promotion decision, profitability claim, or superiority claim.

## Frozen boundaries

The run used the already-frozen execution contract:

- execution timerange: `20260301-20260701`;
- semantic prediction window: `20260301-20260630`;
- download timerange: `20250801-20260701`;
- strict historical-OOS scoring window: `20260501-20260630`;
- strict OOS close upper bound: `2026-07-01T00:00:00Z` exclusive;
- Kraken `BTC/USDT` and `ETH/USDT`;
- `15m`, `1h`, and `4h`;
- fee ratio `0.002`;
- frozen entry threshold `0.006`;
- frozen exit threshold `-0.009`.

The protected final holdout `20260801-20260930` was not used.

## PyTorch track

Canonical identity:

- track: `pytorch-research-v1`;
- model: `SeededPyTorchMLPRegressor`;
- strategy: `AiFrozenCandidateStrategy`;
- FreqAI identifier: `ai-platform-pytorch-research-v1`;
- run ID: `20260721T165446Z-cb63cd31`;
- execution Git commit: `af9e27c48c9f2bf4e7277d09fe5eaec2ee020af3`.

Strict historical-OOS result:

- profit: `-0.001927824937`;
- drawdown: `0.0022277419634928177`;
- trades: `20`;
- stability: `0.0`;
- May profit: `-0.0006747305089999999` from `11` trades;
- June profit: `-0.001253094428` from `9` trades;
- profitable folds: `0` of `2`.

The strict extractor included 20 of 34 input trades and excluded 14 trades whose opens preceded the OOS window.

GitHub Actions artifact:

- artifact ID: `8503203347`;
- name: `experimental-model-historical-backtest-pytorch-94`;
- GitHub digest: `sha256:5092ef0d5b44de9812a822299b1af88c69d10c8c4f1ccc6b55c30359b3bf864d`;
- independently downloaded ZIP SHA-256: `5092ef0d5b44de9812a822299b1af88c69d10c8c4f1ccc6b55c30359b3bf864d`.

Durable machine-readable record:

`ai_platform/experimental_model_research/evidence/pytorch-research-v1-historical-oos-v1.json`

## Reinforcement-learning track

Canonical identity:

- track: `rl-research-v1`;
- model: `LongOnlyReinforcementLearner`;
- strategy: `AiLongOnlyRLResearchStrategy`;
- FreqAI identifier: `ai-platform-rl-research-v1`;
- run ID: `20260721T165410Z-e46e31f6`;
- execution Git commit: `af9e27c48c9f2bf4e7277d09fe5eaec2ee020af3`.

Strict historical-OOS result:

- profit: `0.0`;
- drawdown: `0.0`;
- trades: `0`;
- stability: `0.0`;
- May trades: `0`;
- June trades: `0`;
- profitable folds: `0` of `2`.

The RL run completed successfully but generated no trades. Therefore zero profit and zero drawdown are not evidence of profitability or superiority; they are the observed result of an inactive strategy over the frozen historical window.

GitHub Actions artifact:

- artifact ID: `8503197359`;
- name: `experimental-model-historical-backtest-rl-94`;
- GitHub digest: `sha256:66bef9f73ea898e81707ad2088693d93e86f13fdae59f3782075fb456cb9f9d4`;
- independently downloaded ZIP SHA-256: `66bef9f73ea898e81707ad2088693d93e86f13fdae59f3782075fb456cb9f9d4`.

Durable machine-readable record:

`ai_platform/experimental_model_research/evidence/rl-research-v1-historical-oos-v1.json`

## Interpretation boundary

These observations close the bounded historical execution work package only.

They do not authorize:

- selecting PyTorch over RL or RL over PyTorch;
- adding either track retroactively to completed Phase 6;
- changing the authoritative Phase 6 result `selected_model = null`;
- retuning thresholds, features, model parameters, or RL reward design from consumed historical OOS;
- promotion to dry-run or live capital;
- accessing the protected final holdout;
- a claim that either track is profitable or superior.

Any follow-up experimental-model work requires a new prospectively declared bounded task with its own frozen hypothesis and evaluation policy.
