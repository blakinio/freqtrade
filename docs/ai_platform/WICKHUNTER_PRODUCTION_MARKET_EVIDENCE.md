# WickHunter production market evidence

## Purpose

The production market-evidence subsystem captures, verifies and exposes the public market data required to build WickHunter WH-01 inputs without inventing historical spread, rolling volume, instrument state or completed-candle availability.

The subsystem is deliberately separated into four boundaries:

1. a source-separated public collector for Binance USD-M and Bybit Linear;
2. an immutable package publisher and verifier;
3. a no-network WH-01 input adapter that binds real accepted liquidation imports;
4. a read-only Portal projection.

OKX Swap is represented in the Portal as a liquidation source only. It is not reported as WH-01 candle, market-quality or instrument-history evidence.

The subsystem grants no replay, model-training, strategy-research, execution, order or live-capital authority.

## Frozen capture interval

The production request is fixed before collection begins:

| Boundary | UTC | Epoch milliseconds |
| --- | --- | ---: |
| Candle pre-roll start | 2026-07-30 06:00 | `1785391200000` |
| Decision interval start | 2026-07-31 06:00 | `1785477600000` |
| Decision interval end, exclusive | 2026-07-31 18:00 | `1785520800000` |
| Protected final holdout start | 2026-08-01 00:00 | `1785542400000` |

The request has:

- a 5-minute decision cadence;
- a 24-hour pre-roll;
- a 12-hour decision interval;
- 432 completed 5-minute candles per source and symbol;
- 144 market-quality samples per source and symbol;
- a six-hour gap before the protected final holdout.

The request cannot be retargeted by editing an active run. A different interval requires a new versioned request and policy.

## Sources and market identity

The market-evidence scope is exactly:

```text
bybit-linear
binance-usdm
```

Each source remains distinct through collection, normalization, package publication, Portal projection and WH-01 input generation. Cross-exchange deduplication is disabled.

The collector refuses:

- Binance Spot in place of Binance USD-M;
- inverse Bybit markets in place of Linear perpetuals;
- a symbol outside the frozen Liquid20 cohort;
- a source or market label that differs from the request;
- a missing source-symbol pair;
- duplicate source-symbol observations.

## Collector architecture

### Core acquisition

`ai_platform/wickhunter/production_market_evidence.py` performs public acquisition and writes the restart-safe inner run:

- exact public response bytes;
- normalized market snapshots;
- Binance USD-M best bid and ask;
- Binance USD-M rolling 24-hour quote volume;
- Bybit Linear best bid and ask;
- Bybit Linear rolling 24-hour turnover;
- last price and spread in basis points;
- completed 5-minute OHLCV candles;
- source, symbol, request URL, timestamps, counts and SHA-256 identities.

An unclosed candle is never written as a completed candle. Candle availability is `close_time_ms_exclusive`.

### Publication service

`ai_platform/wickhunter/production_market_evidence_service.py` wraps the core collector and adds:

- versioned policy data;
- historical instrument snapshots;
- source-health snapshots;
- source-separated market-quality observations;
- an outer immutable package;
- exact artifact hashes and independent verification.

Publication uses a sibling `.immutable-package.partial` directory. The final directory is created with one atomic rename only after every identity and geometry gate passes. A partial directory left by a crash blocks publication until an operator investigates it. An existing final package is verified and returned idempotently; it is never overwritten.

### Persistent daemon

`ai_platform/wickhunter/production_market_evidence_daemon.py` provides a Linux/Synology-compatible long-running process. It:

- initializes from an immutable mounted request when no active pointer exists;
- takes at most one due sample in each loop;
- resumes from the self-hashed active pointer and state after restart;
- writes an atomic `collector-health.json` file;
- handles `SIGTERM` and `SIGINT` without deleting state;
- records a bounded fail-closed error instead of hiding a gap.

The daemon does not contain exchange credentials and does not expose a public port.

## Pre-roll policy

The WH-01 adapter policy is stored at:

```text
ai_platform/wickhunter/policies/
  wickhunter-production-market-evidence-wh01-policy-v1.json
```

The declared 5-minute lookbacks are:

| Metric | Rows | Effective history |
| --- | ---: | ---: |
| quote volume 24h | 288 | 24h |
| VWAP | 288 | 24h |
| VWMA | 288 | 24h |
| ATR ratio | 14 plus previous close | 75m |
| volatility ratio | 287 returns over 288 candles | 24h |
| wick ratio | 288 | 24h |
| trend return ratio | 288 | 24h |

The enforced maximum is 288 completed candles, or 24 hours. The adapter fails closed when the captured pre-roll is shorter than the versioned maximum lookback or contains a missing candle.

No lookback is inferred from a default value at runtime.

## Availability semantics

Every value used by WH-01 is checked as-of the decision timestamp.

| Evidence | Availability rule |
| --- | --- |
| completed candle | `close_time_ms_exclusive <= decision_timestamp_ms` |
| market-quality observation | `available_at_ms <= decision_timestamp_ms` |
| instrument snapshot | latest snapshot with `available_at_ms <= decision_timestamp_ms` |
| liquidation event | `received_at_ms <= decision_timestamp_ms` |

The adapter never uses the newest row merely because it is present in the package. A later ticker, candle, instrument state or liquidation event is excluded from an earlier decision.

A source timestamp in the future, a quality observation received after decision time or a candle that has not closed is a controlled error.

## Instrument history

Each source-symbol instrument snapshot preserves:

- source ID;
- native and canonical symbol;
- market type;
- settlement and quote identity;
- active state;
- `captured_at_ms`;
- `available_at_ms`;
- normalization metadata;
- source payload SHA-256;
- normalized snapshot SHA-256.

Snapshots are append-only historical observations. The current catalogue is never backdated to an earlier decision.

## Immutable package

A successful outer package is stored under:

```text
<run-root>/immutable-package/
```

It contains:

```text
request.json
policy.json
run-state.json
source-snapshots.ndjson
market-quality-observations.ndjson
instrument-snapshots.ndjson
completed-candles-index.json
source-artifacts-index.json
manifest.json
artifact-sha256.txt
verification-report.json
```

The package manifest binds:

- run ID and terminal state;
- exact collector commit SHA;
- request and policy SHA-256;
- source and instrument identities;
- capture start, decision start and decision end;
- cadence, timeframe and pre-roll;
- record counts;
- first and last timestamps;
- gaps and gap duration;
- source health;
- WH-01 readiness and exact blocker;
- every artifact name, size and SHA-256;
- all authority flags set to false.

`artifact-sha256.txt` covers the package artifacts and manifest. `verification-report.json` records the independent terminal result.

The package verifier rejects:

- path traversal;
- symlink escape;
- a missing or non-regular file;
- a changed size or SHA-256;
- a changed manifest self-hash;
- a changed source set;
- changed authority flags;
- an inconsistent verification report.

## WH-01 input adapter

`ai_platform/wickhunter/production_market_evidence_wh01.py` converts verified raw evidence to the contracts already consumed by the unchanged WH-01 materialization operator.

The adapter:

1. verifies the outer immutable package;
2. independently verifies the inner acquisition package;
3. verifies every completed-candle artifact hash and row geometry;
4. binds one or more real accepted immutable liquidation imports;
5. computes source-balanced metrics only when both required sources are present;
6. creates `MarketContextSnapshot` history with explicit metric availability;
7. creates historical `DynamicUniverseSnapshot` decisions;
8. freezes dataset cadence, lookbacks, history policy, source freshness, partition span, label horizon, embargo and split window;
9. creates a self-contained materialization input package;
10. runs the existing no-network WH-01 preflight against that package.

The generated package contains:

```text
accepted-imports/<import-run-id>/...
market-context.jsonl
universe-history.jsonl
materialization-request.json
wh01-input-manifest.json
artifact-sha256.txt
verification-report.json
```

When no accepted liquidation import is bound, the adapter returns:

```text
LIQUIDATION_ARCHIVE_NOT_BOUND
```

and writes no output directory. It does not substitute fixtures, zero rows or a different source.

The existing materialization operator is not weakened to pass incomplete input.

## Portal projection

The Portal reads package metadata and bounded normalized rows through the server-side read model documented in:

```text
docs/ai_platform/portal/MARKET_EVIDENCE_READ_MODEL.md
```

The browser never receives:

- host filesystem paths;
- raw exchange response bytes;
- exchange credentials or secret references;
- unbounded artifact dumps;
- mutation or acceptance controls.

## Synology deployment

Persistent v1 and v2 collectors publish distinct `live` and `ready` booleans. `live` reports that
the daemon loop is functioning; `ready` reports that the immutable request is mounted, readable,
valid and the collector is in an explicit operational lifecycle state. Container and deployment
readiness require both booleans plus the compatibility `healthy=true` field. Blocked, failed,
rejected, stale, malformed and schema-mismatched observations fail closed, while the exact blocker
remains visible under `result.reason_code`.

The persistent collector definition is in:

```text
deploy/synology/wickhunter-market-evidence/
```

The container is configured with:

- a non-root UID and GID;
- a read-only root filesystem;
- all Linux capabilities dropped;
- `no-new-privileges`;
- memory and PID limits;
- a persistent writable bind mount only for evidence state;
- a read-only request mount;
- no host network;
- no published port;
- a healthcheck;
- `restart: always`.

The Portal preview deployment script mounts both Liquid20 and market-evidence roots read-only:

```text
deploy/synology/portal/deploy-market-evidence-preview.sh
```

It checks group-readable source paths, starts a candidate container, validates identity and every market-evidence endpoint, rejects host-path or secret disclosure, then replaces the existing preview with rollback support.

## Operator runbook

### Initialize or resume the collector

Set:

```text
COLLECTOR_COMMIT=<exact lowercase 40-character SHA>
MARKET_EVIDENCE_REQUEST_FILE=<absolute immutable request file>
MARKET_EVIDENCE_STATE_DIR=<absolute durable Synology directory>
```

Then validate and start:

```bash
docker compose \
  -f deploy/synology/wickhunter-market-evidence/compose.yaml \
  config --quiet

docker compose \
  -f deploy/synology/wickhunter-market-evidence/compose.yaml \
  up -d --build
```

### Check health

```bash
docker inspect --format '{{json .State.Health}}' wickhunter-market-evidence
docker logs --tail 100 wickhunter-market-evidence
cat <durable-root>/collector-health.json
```

A failed health report must be investigated. Operators must not delete a gap, rewrite a closed package or manually mark a run accepted.

### Verify a completed package

```bash
PYTHONPATH=. python -m ai_platform.wickhunter.production_market_evidence_service \
  verify \
  --package-root <run-root>/immutable-package
```

### Build WH-01 inputs

```bash
PYTHONPATH=. python -m ai_platform.wickhunter.production_market_evidence_wh01 \
  --evidence-package-root <run-root>/immutable-package \
  --accepted-import-root <accepted-liquidation-import-root> \
  --policy ai_platform/wickhunter/policies/wickhunter-production-market-evidence-wh01-policy-v1.json \
  --output-root <new-wh01-input-root>
```

Run the existing materialization operator only when the adapter report and existing WH-01 preflight both return `ready`.

## Stable blocker and reason codes

| Code | Meaning |
| --- | --- |
| `MARKET_EVIDENCE_UNAVAILABLE` | no active or verified run can be read |
| `IMMUTABLE_PACKAGE_PENDING` | capture exists but final package is not verified |
| `LIQUIDATION_ARCHIVE_NOT_BOUND` | market evidence is valid but a matching accepted liquidation archive is not bound |
| `OKX_CANDLE_EVIDENCE_NOT_CONFIGURED` | OKX liquidation status is available but WH-01 candle and quality scope is absent |
| `CAPTURE_FAILED` | active capture entered a terminal failed state |
| `COLLECTOR_FAIL_CLOSED` | daemon recorded a controlled acquisition or persistence failure |
| `instrument_source_coverage_incomplete` | required historical instrument state is absent for one source |
| `quote_volume_below_minimum` | frozen universe volume gate failed |
| `spread_above_maximum` | frozen universe spread gate failed |
| `insufficient_candle_history` | completed-candle history is shorter than policy |
| `insufficient_feature_history` | historical liquidation event count is below policy |
| `insufficient_healthy_liquidation_sources` | source freshness or coverage gate failed |
| `eligible` | all frozen inclusion gates passed |

## Fail-closed boundaries

Collection, publication, adaptation or Portal projection rejects or reports blocked for:

- a missing source;
- a missing or duplicate symbol;
- a wrong market;
- an incomplete candle;
- a candle gap;
- stale or unavailable quality data;
- a future timestamp;
- a metric available after decision time;
- insufficient pre-roll;
- a missing instrument snapshot;
- source or symbol mismatch;
- hash mismatch;
- path traversal;
- symlink escape;
- overwrite;
- recognized exchange credentials;
- non-false authority flags;
- access to the protected final holdout.

## Authority boundary

Every request, package, adapter output and Portal summary preserves:

```text
execution_enabled = false
orders_submitted = 0
trading_credentials_present = false
model_execution_authorized = false
replay_authorized = false
performance_research_authorized = false
live_capital_authorized = false
```

No file in this subsystem authorizes order submission, live trading, model execution, protected holdout access, dataset promotion or WH-02.
