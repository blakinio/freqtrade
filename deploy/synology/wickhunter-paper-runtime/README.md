# WickHunter WH-09 persistent PAPER runtime

This package runs the independently verified WickHunter candidate only inside an immutable PAPER activation. It reads the deployed Liquid20 live root directly, derives canonical liquidation histories and the dynamic universe, obtains decision-time public Binance USD-M evidence, creates feature-complete `ShadowRuntimeTick` values, and delegates persistence and restart recovery to `CandidatePaperRuntimeService`.

It contains no exchange credentials, private or account endpoints, order adapter, order submission, execution authority, automatic promotion, protected-holdout access, or live-capital authority.

## Required immutable inputs

The deployment request must bind:

- `CANDIDATE_ROOT_HOST`: independently verified candidate package, read-only;
- `ACTIVATION_ROOT_HOST`: fresh immutable PAPER activation, read-only;
- `LIQUID20_LIVE_HOST`: the existing Liquid20 `/data/live` root containing `live-state-v1.json` and `runs/<active_run_id>/<source>.ndjson`, read-only;
- `JOURNAL_ROOT_HOST`: exact new/empty or independently verified contiguous journal root;
- `OPERATOR_STATE_HOST`: exact health-state directory;
- `OPERATOR_COMMIT`: exact merged implementation SHA;
- `WICKHUNTER_PAPER_RUNTIME_IMAGE`: image built from that SHA and verified by digest.

The activation created before this operator existed is not eligible for the prospective WH-09 window. Deployment must publish a fresh activation and bind its exact candidate, run, policy, and journal identities.

## Liquid20 live boundary

The operator accepts only the deployed directory contract. It validates the active-run pointer, state/run identity, collector and source heartbeats, configured-source state, event/source identity, availability time, path safety, and zero-authority fields. Legacy single-file snapshot input is not accepted.

For each cadence it derives deterministic 24-hour event histories, complete burst buckets, a canonical `DynamicUniverseSnapshot`, and one market-wide liquidation intensity value. It may journal an empty decision set when no eligible current burst exists.

## Public market boundary and canonical metrics

HTTPS GET is restricted in process to `https://fapi.binance.com`. Proxies, recognized exchange credentials, redirects, non-JSON responses, oversized responses, symbol mismatches, stale timestamps, and incomplete or gapped candle history fail closed.

The operator calls only:

- `/fapi/v1/premiumIndex`;
- `/fapi/v1/ticker/bookTicker`;
- `/fapi/v1/openInterest`;
- `/fapi/v1/klines` with `interval=1m` and `limit=1441`.

It requires 1440 contiguous completed one-minute candles and derives the exact feature contract:

- `quote_volume_24h_usd`;
- `vwap`;
- `vwma`;
- `atr_ratio` from 14 true ranges over the final 15 completed candles;
- `volatility_ratio` as population standard deviation of completed-candle simple returns;
- `wick_ratio`;
- `trend_return_ratio`;
- `spread_bps` from `bookTicker`;
- `market_wide_liquidation_intensity` from the live 24-hour Liquid20 history.

The context additionally includes `funding_rate` and `open_interest_usd` for freshness and risk checks. The trusted deployment request must separately prove host-level egress restriction to DNS and the allowlisted Binance public endpoints.

## PAPER risk and exercises

The immutable activation authorizes candidate validation only. It never authorizes execution. The risk context derives projected exposure, daily loss, drawdown, and consecutive losses from the simulated journal. `MODEL_DRIFT` and `DATA_DRIFT` default to `healthy`; a separately reviewed deployment request may set an explicit enum value for bounded acceptance exercises.

## Runtime and health behavior

The default cadence is 600 seconds, yielding up to 144 snapshots per 24 hours. Every successful tick has a strictly increasing observation time. `/runtime/operator/health.json` is atomically replaced and self-hashed. It reports exact operator, binding, run, window, generation, source, drift, breaker, and zero-authority state.

The container healthcheck is `/app/deploy/synology/wickhunter-paper-runtime/paper_runtime_healthcheck.py`. It rejects stale, tampered, failed, or identity-mismatched state while accepting truthful fail-closed runtime breaker evidence produced by a successful journal step.

## Hardened container boundary

The service uses UID/GID `65532`, a read-only root filesystem, all capabilities dropped, `no-new-privileges`, no privileged mode, no inbound ports, no Docker socket, read-only candidate/activation/Liquid20 mounts, and only the journal and health roots writable.

## Validation

Run on the exact product head:

```bash
ruff format --check \
  ai_platform/wickhunter/candidate_paper_runtime_operator.py \
  deploy/synology/wickhunter-paper-runtime/paper_runtime_healthcheck.py \
  tests/ai_platform_integration/test_wickhunter_candidate_paper_runtime_operator.py
ruff check \
  ai_platform/wickhunter/candidate_paper_runtime_operator.py \
  deploy/synology/wickhunter-paper-runtime/paper_runtime_healthcheck.py \
  tests/ai_platform_integration/test_wickhunter_candidate_paper_runtime_operator.py
mypy ai_platform/wickhunter/candidate_paper_runtime_operator.py
pytest -q \
  tests/ai_platform_integration/test_wickhunter_candidate_paper_runtime_operator.py \
  tests/ai_platform_integration/test_wickhunter_candidate_paper_runtime_service.py \
  tests/ai_platform_integration/test_wickhunter_candidate_runtime_binding.py
OPERATOR_COMMIT=<exact-sha> \
CANDIDATE_ROOT_HOST=/tmp/candidate \
ACTIVATION_ROOT_HOST=/tmp/activation \
LIQUID20_LIVE_HOST=/tmp/liquid20-live \
JOURNAL_ROOT_HOST=/tmp/journal \
OPERATOR_STATE_HOST=/tmp/operator \
WICKHUNTER_PAPER_RUNTIME_IMAGE=wickhunter-paper-runtime:<exact-sha> \
  docker compose -f deploy/synology/wickhunter-paper-runtime/compose.yaml config --quiet
```

Implementation merge does not complete WH-09. A separate one-file request-only deployment PR must build and inspect the exact image, publish a fresh activation, enforce host egress, start the service on the trusted Synology runner, and collect the complete prospective acceptance window before independent verification and explicit owner decision.
