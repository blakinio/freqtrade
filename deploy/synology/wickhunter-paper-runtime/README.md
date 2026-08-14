# WickHunter WH-09 persistent PAPER runtime

This package runs the independently verified WickHunter candidate only inside an immutable PAPER activation. It reads the deployed Liquid20 live root directly, derives canonical liquidation histories and the dynamic universe, obtains decision-time public Binance USD-M evidence, creates feature-complete `ShadowRuntimeTick` values, and delegates persistence and restart recovery to `CandidatePaperRuntimeService`.

It contains no exchange credentials, private or account endpoints, order adapter, order submission, execution authority, automatic promotion, protected-holdout access, or live-capital authority.

## Required immutable inputs

The deployment request must bind:

- `CANDIDATE_ROOT_HOST`: independently verified candidate package, read-only;
- `ACTIVATION_ROOT_HOST`: fresh immutable PAPER activation, read-only;
- `LIQUID20_LIVE_HOST`: the existing Liquid20 `/data/live` root containing `live-state-v1.json` and `runs/<active_run_id>/<source>.ndjson`, read-only;
- `LIQUID20_READER_GID`: exact numeric group ID of `LIQUID20_LIVE_HOST`, used only as a supplementary read group;
- `JOURNAL_ROOT_HOST`: exact new/empty or independently verified contiguous journal root;
- `OPERATOR_STATE_HOST`: exact health-state directory;
- `OPERATOR_COMMIT`: exact merged implementation SHA;
- `WICKHUNTER_PAPER_RUNTIME_IMAGE`: image built from that SHA and verified by digest.

The activation created before this operator existed is not eligible for the prospective WH-09 window. Deployment must publish a fresh activation and bind its exact candidate, run, policy, and journal identities.

## Liquid20 live boundary

The operator accepts only the exact `liquidation-live-state-v1` deployed directory contract. It validates the active-run pointer, state/run identity, collector and source heartbeats, configured-source state, event/source identity, availability time, path safety, and zero-authority fields. Legacy single-file snapshot input and contract substitution are not accepted.

Liquid20 intentionally publishes its live files under the shared data-root group with group-readable permissions. Before starting WickHunter, resolve the reader group from the mounted live root, for example `LIQUID20_READER_GID="$(stat -c %g "$LIQUID20_LIVE_HOST")"`, require it to be numeric, and pass exactly that value as the container's supplementary group. The primary WickHunter identity remains `65532:65532`. Do not make Liquid20 files world-readable and do not substitute group `0` unless it is actually the verified GID of the mounted Liquid20 live root.

For each cadence it reads the active run plus bounded completed run epochs that overlap the preceding 24 hours, validates their immutable run/source state, derives deterministic event histories and a canonical `DynamicUniverseSnapshot`, and computes one market-wide liquidation intensity value from complete elapsed buckets. Decision requests contain only events inside the current configured burst; when no eligible current burst exists the service journals an empty decision set. Public marks also cover persisted open positions even when a symbol falls outside the current universe.

## Public market boundary and canonical metrics

HTTPS GET is restricted in process to `https://fapi.binance.com` on the standard TLS port 443. Proxies, recognized exchange credentials, redirects, non-JSON responses, oversized responses, symbol mismatches, stale timestamps, and incomplete or gapped candle history fail closed.

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

The immutable activation authorizes candidate validation only. It never authorizes execution. The risk context derives projected exposure, daily loss, drawdown, and consecutive losses from the simulated journal. Consecutive-loss cooldown is anchored to the latest closed loss and therefore expires instead of sliding on every tick. `MODEL_DRIFT` and `DATA_DRIFT` default to `healthy`; `CIRCUIT_BREAKER_ACTIVE` defaults to `false`. A separately reviewed deployment request may set these bounded controls for acceptance exercises.

## Runtime and health behavior

The default cadence is 600 seconds, yielding up to 144 snapshots per 24 hours. Every successful tick has a strictly increasing observation time. `/runtime/operator/health.json` is atomically replaced and self-hashed. It reports exact operator, binding, run, window, generation, runtime health, canonical circuit-breaker reasons, drift, and zero-authority state.

The container healthcheck is `/app/deploy/synology/wickhunter-paper-runtime/paper_runtime_healthcheck.py`. It accepts only fresh, untampered, identity-matching state whose `runtime_health` is exactly `healthy`. Truthful `degraded` or `fail_closed` circuit-breaker evidence remains valid operator evidence, but intentionally makes the container healthcheck fail closed during the exercise and must not be interpreted as a healthy runtime proof.

## Hardened container boundary

The service keeps primary UID/GID `65532:65532` and joins only the exact supplementary `LIQUID20_READER_GID` required to read the mounted Liquid20 data contract. It uses a read-only root filesystem, all capabilities dropped, `no-new-privileges`, no privileged mode, no inbound ports, no Docker socket, read-only candidate/activation/Liquid20 mounts, and only the journal and health roots writable.

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
  tests/ai_platform_integration/test_wickhunter_candidate_runtime_binding.py \
  tests/ai_platform_integration/test_wickhunter_paper_runtime_deploy_contract.py
OPERATOR_COMMIT=<exact-sha> \
CANDIDATE_ROOT_HOST=/tmp/candidate \
ACTIVATION_ROOT_HOST=/tmp/activation \
LIQUID20_LIVE_HOST=/tmp/liquid20-live \
LIQUID20_READER_GID="$(stat -c %g /tmp/liquid20-live)" \
JOURNAL_ROOT_HOST=/tmp/journal \
OPERATOR_STATE_HOST=/tmp/operator \
WICKHUNTER_PAPER_RUNTIME_IMAGE=wickhunter-paper-runtime:<exact-sha> \
  docker compose -f deploy/synology/wickhunter-paper-runtime/compose.yaml config --quiet
```

Implementation merge does not complete WH-09. A separate one-file request-only deployment PR must build and inspect the exact image, publish a fresh activation, derive and verify the exact Liquid20 reader GID, enforce host egress, start the service on the trusted Synology runner, and collect the complete prospective acceptance window before independent verification and explicit owner decision.
