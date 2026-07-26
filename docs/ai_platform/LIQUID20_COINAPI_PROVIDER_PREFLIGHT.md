# Liquid20 CoinAPI Provider Preflight

## Scope

This bounded follow-up evaluates CoinAPI as a possible replacement for the Tardis event-level historical liquidation import selected by `LIQUID20_HISTORICAL_PROVIDER_PREFLIGHT.md`.

It checks the documented Binance Futures and Bybit liquidation metric families, the historical response contract, timestamp provenance, event reconstruction safety, authentication, and one non-secret runtime probe. It does not purchase access, provision a private credential, download paid history, implement an importer, train a model, access the protected final holdout, or change live collection.

Verification date: `2026-07-26`.

Machine-readable evidence:

```text
ai_platform/research/liquidations/historical/liquid20-coinapi-provider-preflight-v1.json
ai_platform/research/liquidations/historical/coinapi-provider-preflight-v1.schema.json
```

## Decision

**CoinAPI is rejected as a replacement for the Tardis event-level replay source.**

**CoinAPI remains a conditional aggregate-feature candidate only.**

The preferred provider for the first event-level import remains Tardis.

The rejection does not depend on proving a multi-event second in a paid sample. The documented historical endpoint already fails two required event-replay properties:

1. it returns bucketed metric time series rather than one joined record per liquidation;
2. it does not expose historical `entry_time` or `recv_time`, so provider availability time cannot be preserved.

## Documented exchange coverage

CoinAPI's current metric-per-exchange table lists the following liquidation metrics.

### Bybit (`BYBIT`)

```text
LIQUIDATION_PRICE
LIQUIDATION_QUANTITY
LIQUIDATION_SIDE
LIQUIDATION_SYMBOL
LIQUIDATION_TIME
```

### Binance Futures (`BINANCEFTS`)

```text
LIQUIDATION_AVERAGE_PRICE
LIQUIDATION_FILLED_ACCUMULATED_QUANTITY
LIQUIDATION_ORDER_LAST_FILLED_QUANTITY
LIQUIDATION_ORDER_STATUS
LIQUIDATION_ORDER_TRADE_TIME
LIQUIDATION_ORDER_TYPE
LIQUIDATION_PRICE
LIQUIDATION_QUANTITY
LIQUIDATION_SYMBOL
LIQUIDATION_TIME_IN_FORCE
```

This establishes documented metric-family coverage at exchange level. CoinAPI explicitly warns that metadata does not guarantee actual availability for every symbol or date. Exact live coverage for all four target symbols therefore remains unverified without an authenticated request.

Target symbols:

```text
BYBIT_PERP_BTC_USDT
BYBIT_PERP_ETH_USDT
BINANCEFTS_PERP_BTC_USDT
BINANCEFTS_PERP_ETH_USDT
```

## Historical response contract

Endpoint:

```text
GET /v1/metrics/symbol/history
```

Relevant documented properties:

- API key required;
- `period_id` defaults to `1SEC`;
- maximum `limit` is `100000`;
- each metric is requested separately;
- response rows expose bucket fields:
  - `time_period_start`;
  - `time_period_end`;
  - `time_open`;
  - `time_close`;
  - `first`;
  - `last`;
  - `min`;
  - `max`;
  - `count`;
  - `sum`.

The historical contract does not expose:

- an event identifier;
- a single joined liquidation record containing time, side, price, and quantity;
- historical `entry_time`;
- historical `recv_time`.

The separate current-metrics endpoint documents `entry_time` and `recv_time`, but the historical endpoint does not. No documented rule permits reconstructing these fields for historical buckets.

## Why event reconstruction is unsafe

Price, quantity, side, symbol, and time are separate metric series. Joining them by one-second bucket is not an event identity.

If a bucket contains more than one liquidation, aggregate values cannot preserve the original pairings. Even when `count == 1`, the historical response still lacks a provider receive timestamp and a durable event identifier. Consequently the result cannot satisfy the existing Liquid20 historical contract:

```text
occurred_at_ms
provider_captured_at_ms
source-specific event identity
```

CoinAPI history must not populate first-party `received_at_ms`, and a provider capture timestamp must not be fabricated from bucket boundaries.

## Runtime probe

A temporary GitHub Actions diagnostic called the metrics-listing endpoint with CoinAPI's publicly documented sample placeholder credential. No private credential was used.

Result:

```text
workflow run: 30196686123
workflow job: 89779333914
endpoint: /v1/metrics/listing
HTTP status: 401
JSON response: true
response keys: error
raw market records emitted: false
```

The public sample string is therefore an example value, not an active trial key.

The temporary workflow is not part of the durable change set.

## What remains possible

CoinAPI may be evaluated in a separate aggregate-source work package for completed-interval features such as liquidation quantity or price aggregates. Such a package must:

- use an authenticated trial credential supplied outside Git;
- verify all four exact symbols and the requested date range;
- preserve CoinAPI bucket semantics without converting buckets into events;
- apply an explicit completed-interval availability lag;
- maintain a separate feature namespace and quality mask;
- preflight license, retention, redistribution, and exact cost terms;
- avoid replacing or weakening the event-level Tardis contract.

## Sources

- `https://www.coinapi.io/products/market-data-api/docs/metadata-tables/metric_id`
- `https://www.coinapi.io/products/market-data-api/docs/rest-api/metrics-v1/metrics/symbol/history/get`
- `https://www.coinapi.io/products/market-data-api/docs/rest-api/metricsv1/metrics/symbol/current/get`
- `https://www.coinapi.io/products/market-data-api/docs/rest-api/metricsv1/metrics/symbol/listing/get`
- `https://www.coinapi.io/products/market-data-api/docs/rest-api/metadata/symbols/exchange_id/active/get`
- `https://www.coinapi.io/products/market-data-api/faq`

## Next action

Do not purchase CoinAPI as a Tardis event-level replacement. Run an authenticated CoinAPI trial only if the owner separately approves an aggregate-feature source evaluation.
