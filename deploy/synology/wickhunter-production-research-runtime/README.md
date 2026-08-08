# WickHunter WH09 production research/shadow runtime

This service runs the frozen H900 WickHunter model continuously against the existing internal-production Liquid20 data path and public Binance USD-M context in `BotMode.SHADOW`.

It is a research/data-collection runtime, not a PAPER activation and not a live-capital deployment. It keeps `no_trade_confidence=0.60`, keeps `candidate_paper_validation_authorized=false`, records every evaluated decision including `NO_TRADE`, and materializes a separate 900-second research outcome only after that horizon becomes observable.

## Frozen H900 binding

- package: `wickhunter-wh09-candidate-materialization-20260808-r1-h900s-7b23a958fd4d`
- package manifest: `9f5ba852e33915678ca085c2eeafbf526457a079ba8f6f2fb7c1097f1d20ab79`
- model artifact: `0488eaea68a316e3659e3b9e2fcea667eb57de87a22888ce396d112a5c075d2e`
- model version: `wickhunter-lightgbm-eddd12e3d0c59225`
- model hash: `eddd12e3d0c5922547df89d9fa3d8556b8131a62c3cb8057c5a20c66747a240b`
- parameter version: `wickhunter-production-h900s-09`
- parameter hash: `014b471b9ccc663c3551a151353ae7cd932bd43ed48b9fbf239baad3483e2c11`
- model source commit: `7b23a958fd4d2bb43569c7f693d2247ef43d1ae9`
- no-trade confidence: `0.60`
- outcome horizon: `900000 ms`

The model package is verified with the existing candidate-package verifier, but this service creates and consumes no PAPER activation.

## Decision and outcome evidence

Each create-once decision record contains decision-time market evidence and availability timestamps, candidate/risk reason codes, raw LightGBM probability, calibrated confidence, the frozen threshold, final `NO_TRADE` or simulated decision, and immutable model/parameter/dataset/code identities.

For directional observations, the first runtime mark observed at or after `decision_timestamp + 900 s` becomes a separate create-once research outcome. It records the actual observation delay and side-adjusted return. The record explicitly declares `deterministic_replay_equivalent=false` and uses semantics `first_observed_mark_at_or_after_target_horizon_no_costs`; it is not an exact-fill or fee-adjusted trade claim.

Telemetry reports decision/no-trade/simulated-signal counts, confidence distribution, matured and pending outcomes, positive outcome rate, runtime generation and simulated PnL.

## Safety boundary

The required authority state is always:

```text
protected_holdout_accessed=false
automatic_promotion_enabled=false
trading_credentials_present=false
order_adapter_present=false
execution_enabled=false
orders_submitted=0
live_capital_authorized=false
```

`SHADOW` does not bypass candidate promotion. The H900 model remains candidate/advisory evidence and the deterministic risk layer can continue to reject unapproved model execution while inference, journaling and outcome collection continue.

## Container boundary

The service runs as `65532:65532`, uses only the verified Liquid20 supplementary reader GID, mounts H900 and Liquid20 read-only, exposes no inbound port, clears proxy variables, drops all capabilities, sets `no-new-privileges`, uses a read-only root filesystem and has no Docker socket.

Required deployment variables are:

```text
OPERATOR_COMMIT=<exact merged implementation SHA>
WICKHUNTER_RESEARCH_RUNTIME_IMAGE=<image built from exact SHA>
LIQUID20_LIVE_HOST=<verified Liquid20 /data/live root>
LIQUID20_READER_GID=<numeric GID of that root>
```

The default H900 model root is `/var/lib/freqtrade-staging-state/wickhunter-candidate-materialization/packages/wickhunter-wh09-candidate-materialization-20260808-r1-h900s-7b23a958fd4d`. Writable research state defaults under `/var/lib/freqtrade-staging-state/wickhunter-production-research-runtime/`.

A healthy path is:

```text
Liquid20 demo/live-data root
→ bounded public market context
→ frozen H900 shadow inference
→ immutable decision journal
→ delayed 900 s research outcome
→ telemetry + health
```

Any challenger retraining or candidate promotion remains a separate governed work package; this service never promotes itself.
