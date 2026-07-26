# Liquid20 CoinAPI Authenticated Trial

## Scope

This bounded follow-up tests the CoinAPI free account and repository secret `COINAPI_KEY`
against the exact Liquid20 target symbols:

```text
BYBIT_PERP_BTC_USDT
BYBIT_PERP_ETH_USDT
BINANCEFTS_PERP_BTC_USDT
BINANCEFTS_PERP_ETH_USDT
```

The trial checks authenticated symbol metadata, liquidation metric listings, the requested
history window, and the exact account quota response. It does not purchase access, expose
the secret, emit raw market values, download history, implement an importer, train a model,
run a backtest, change the live collector, mutate Synology, or access the protected final
holdout.

Verification date: `2026-07-26`.

Machine-readable evidence:

```text
ai_platform/research/liquidations/historical/liquid20-coinapi-authenticated-trial-v1.json
ai_platform/research/liquidations/historical/coinapi-authenticated-trial-v1.schema.json
```

## Result

**The current CoinAPI free account cannot execute the Liquid20 provider trial.**

The repository secret was present and masked in GitHub Actions. Authenticated requests were
accepted far enough for CoinAPI to return structured quota responses, but both tested REST
endpoint families returned HTTP `403` for every target:

- `GET /v1/symbols/{exchange_id}/active`
- `GET /v1/metrics/symbol/listing`

Because the metric listing was forbidden, no metric identifier could be selected and no
historical request was made. Exact target metric coverage and historical availability
therefore remain unverified with this account.

## Coverage probe

GitHub Actions evidence:

```text
workflow run: 30197961324
workflow job: 89782783001
requests:     8
```

For each target, the trial issued one exact-symbol metadata request and one exact-symbol
metric-listing request. All eight requests returned HTTP `403`.

The workflow emitted only:

- HTTP status;
- response field names;
- target identifiers;
- aggregate booleans.

It emitted no raw market records or market values. The secret was displayed only as GitHub's
masked `***` value.

## Exact quota blocker

A second one-request probe captured only non-secret quota metadata:

```text
workflow run: 30198031682
workflow job: 89782989299
endpoint:     /v1/metrics/symbol/listing
symbol:       BYBIT_PERP_BTC_USDT
HTTP status:  403
```

CoinAPI returned:

```text
QuotaKey:               BA
QuotaName:              Insufficient Usage Credits or Subscription
QuotaType:              Organization Limit
QuotaValue:             0
QuotaValueCurrentUsage: 0
QuotaValueUnit:         $
QuotaValueAdjustable:   Yes, acquire or upgrade subscription, add service credits manually or setup auto-recharge.
title:                  Forbidden
```

This is not a daily-request exhaustion result: the reported monetary quota value and current
usage were both zero. The tested organization had no usable service credits or subscription
for the endpoint.

## Interpretation

The authenticated result changes only the account-access conclusion:

- the secret is validly provisioned and usable by GitHub Actions;
- the free account supplies zero usable credits for the tested REST endpoints;
- exact symbol, metric and history coverage cannot be verified without credited or paid access.

It does **not** change the prior provider decision. CoinAPI's documented historical Metrics V1
contract remains bucketed and omits historical provider receive time and event identity.
Paying merely to repeat this test is therefore not recommended as a route to replace Tardis
for event-level replay.

CoinAPI may still be evaluated later as an aggregate completed-interval feature source, but
only through a separate owner-approved work package with explicit cost, license, retention,
availability-lag and feature-namespace contracts.

## Decision

```text
CoinAPI free account usable for Liquid20 trial: no
CoinAPI selected as Tardis event-level replacement: no
Preferred event-level provider: Tardis
Further CoinAPI access required for this programme: no
Optional future CoinAPI scope: aggregate completed-interval features only
```

## Sources

- `https://www.coinapi.io/products/market-data-api/docs/rest-api/metadata/symbols/exchange_id/active/get`
- `https://www.coinapi.io/products/market-data-api/docs/rest-api/metricsv1/metrics/symbol/listing/get`
- `https://www.coinapi.io/products/market-data-api/docs/rest-api/metrics-v1/metrics/symbol/history/get`
- `https://www.coinapi.io/products/market-data-api/docs/rest-api/metricsv1/metrics/symbol/current/get`

## Next action

Do not purchase CoinAPI as an event-level replacement. Continue the provider-neutral H1/H2
work and keep Tardis as the owner-gated event-level source. Declare a separate CoinAPI
aggregate-feature trial only if the owner explicitly approves that scope.
