# WickHunter WH-09 persistent PAPER runtime

This package runs the independently verified WickHunter candidate only inside the immutable PAPER activation. It continuously creates canonical `ShadowRuntimeTick` values from read-only Liquid20 evidence and public Binance USD-M market data, then delegates persistence and restart recovery to `CandidatePaperRuntimeService`.

It does not contain exchange credentials, private/account endpoints, an order adapter, order submission, execution authority, automatic promotion, protected-holdout access or live-capital authority.

## Required immutable inputs

The deployment request must bind all of the following to the exact reviewed identities:

- `CANDIDATE_ROOT_HOST`: verified candidate package, mounted read-only;
- `ACTIVATION_ROOT_HOST`: fresh immutable PAPER activation, mounted read-only;
- `LIQUID20_LIVE_HOST`: directory containing `latest.json`, mounted read-only;
- `JOURNAL_ROOT_HOST`: exact empty/new or verified contiguous journal root;
- `OPERATOR_STATE_HOST`: exact health-state directory;
- `OPERATOR_COMMIT`: exact merged implementation SHA;
- `WICKHUNTER_PAPER_RUNTIME_IMAGE`: image built from that SHA and verified by digest.

The activation created before this operator existed is not eligible for the prospective WH-09 window. Deployment must publish a fresh activation and bind its exact candidate, run, policy and journal identities.

## Liquid20 read-only contract

`latest.json` uses schema `wickhunter-liquid20-public-snapshot-v1`. It is a bounded canonical JSON object with:

- `observed_at_ms`;
- canonical liquidation `events`, unique and sorted by `source_event_id`;
- one `histories` row per selected symbol;
- sorted `source_states` with truthful health and receipt timestamps;
- sorted `universe` decisions and `universe_policy_version`;
- `snapshot_sha256`, calculated as the canonical SHA-256 of the object without that field.

Every event, history row and source state must have been available no later than `observed_at_ms`. The operator rejects future, stale, malformed, duplicated, unsorted or self-hash-mismatched input before calling the runtime service.

A minimal shape is:

```json
{
  "schema_version": "wickhunter-liquid20-public-snapshot-v1",
  "observed_at_ms": 1800000000000,
  "universe_policy_version": "liquid20-public-v1",
  "events": [{
    "schema_version": 1,
    "source": "binance-usdm",
    "source_event_id": "event-0001",
    "symbol": "BTCUSDT",
    "liquidated_position_side": "long",
    "occurred_at_ms": 1799999998000,
    "received_at_ms": 1799999999000,
    "price": "100",
    "quantity": "10",
    "notional_usd": "1000",
    "raw_side": "SELL"
  }],
  "histories": [{
    "symbol": "BTCUSDT",
    "event_notionals_usd": ["100", "200"],
    "burst_window_notionals_usd": ["150", "250"],
    "previous_burst_received_at_ms": 1799999990000,
    "available_at_ms": 1799999999500,
    "history_id": "history-btcusdt-v1",
    "history_sha256": "<64 lowercase hex>"
  }],
  "source_states": [{
    "source": "binance-usdm",
    "health": "healthy",
    "coverage_available": true,
    "last_received_at_ms": 1799999999000,
    "observed_at_ms": 1800000000000
  }],
  "universe": [{
    "canonical_instrument_id": "perpetual:BTCUSDT",
    "symbol": "BTCUSDT",
    "included": true,
    "reason_codes": ["eligible"]
  }],
  "snapshot_sha256": "<canonical hash of all preceding fields>"
}
```

## Public market boundary

The process permits HTTPS GET requests only to the allowlisted public USD-M futures host. It uses no proxy, rejects redirects, bounds response size, accepts JSON only and calls only:

- `/fapi/v1/premiumIndex`;
- `/fapi/v1/ticker/24hr`;
- `/fapi/v1/openInterest`;
- `/fapi/v1/klines`.

Recognized exchange credentials and proxy environment variables cause startup or collection to fail closed. The Synology deployment must additionally restrict the container bridge to DNS and public market-data egress; no inbound port, Docker socket or private network route is authorized.

## Runtime and health behavior

The default cadence is 600 seconds, producing up to 144 prospective snapshots per 24 hours and remaining below the 900-second maximum needed for at least 96 snapshots. The runtime service verifies activation identity, policy identity and the contiguous journal before every recovery and commits one immutable generation per successful tick.

`/runtime/operator/health.json` is atomically replaced and self-hashed. It reports the exact operator commit, binding, run, activation window, journal generation, last success, bounded error details and all zero-authority fields. The container healthcheck fails when this state is stale, fail-closed, tampered, outside the activation window or inconsistent with `OPERATOR_COMMIT`.

## Hardened container boundary

The Compose service has:

- a read-only root filesystem;
- UID/GID `65532`;
- all Linux capabilities dropped;
- `no-new-privileges` and no privileged mode;
- no published or exposed inbound ports;
- no Docker socket;
- read-only candidate, activation and Liquid20 mounts;
- writable journal and operator-health mounts only;
- bounded tmpfs, memory, CPU and PID limits;
- `restart: unless-stopped` and an exact healthcheck.

## Validation

Before a deployment request is reviewed, run on the exact product head:

```bash
ruff format --check \
  ai_platform/wickhunter/candidate_paper_runtime_operator.py \
  deploy/synology/wickhunter-paper-runtime/healthcheck.py \
  tests/ai_platform_integration/test_wickhunter_candidate_paper_runtime_operator.py
ruff check \
  ai_platform/wickhunter/candidate_paper_runtime_operator.py \
  deploy/synology/wickhunter-paper-runtime/healthcheck.py \
  tests/ai_platform_integration/test_wickhunter_candidate_paper_runtime_operator.py
mypy ai_platform/wickhunter/candidate_paper_runtime_operator.py
pytest -q \
  tests/ai_platform_integration/test_wickhunter_candidate_paper_runtime_operator.py \
  tests/ai_platform_integration/test_wickhunter_candidate_paper_runtime_service.py \
  tests/ai_platform_integration/test_wickhunter_candidate_runtime_binding.py
OPERATOR_COMMIT=<exact-sha> \
CANDIDATE_ROOT_HOST=/tmp/candidate \
ACTIVATION_ROOT_HOST=/tmp/activation \
LIQUID20_LIVE_HOST=/tmp/liquid20 \
JOURNAL_ROOT_HOST=/tmp/journal \
OPERATOR_STATE_HOST=/tmp/operator \
WICKHUNTER_PAPER_RUNTIME_IMAGE=wickhunter-paper-runtime:<exact-sha> \
  docker compose -f deploy/synology/wickhunter-paper-runtime/compose.yaml config --quiet
```

Implementation merge does not complete WH-09. A separate one-file request-only deployment PR must build and inspect the exact image, publish a fresh activation, start this service on the trusted Synology runner and collect the full prospective acceptance window before owner review.
