# Market Data Source and Instrument-Catalog Preflight v1

Status: **current-documentation preflight complete; source acceptance not granted**

Machine-readable result:
`docs/ai_platform/market_data/source-and-instrument-catalog-preflight-v1.json`

Schema:
`ai_platform/market_data/source-and-instrument-catalog-preflight-v1.schema.json`

Verification date: `2026-07-26`.

## 1. Scope

This package verifies the current official public documentation needed before implementing bounded
instrument snapshot adapters for the six source declarations in Market Data Fabric foundation v1:

- Binance Spot and USD-M derivatives;
- Bybit Spot and Linear derivatives;
- OKX Spot and SWAP/FUTURES.

It records public instrument-catalog endpoints, documented pagination, rate and connection constraints,
official example-payload fields, and the mapping evidence required by `InstrumentSnapshot`.

This package performs no live endpoint request, WebSocket connection, broad capture, raw-record commit,
instrument adapter implementation, source acceptance, replay, model, portal, deployment or execution change.

## 2. Decision

The preflight result is `partial_pass`.

| Source | Adapter gate | Reason |
|---|---|---|
| `binance-spot` | ready for a bounded adapter | Official `exchangeInfo` fields cover symbol identity, assets, status, tick size and quantity step. |
| `binance-usdm` | blocked | Official `exchangeInfo` examples do not provide explicit contract value and contract-value unit evidence required by the foundation contract. |
| `bybit-spot` | ready for a bounded adapter | Official instrument metadata covers identity, assets, status, tick size and base quantity precision. |
| `bybit-linear` | ready with an explicit normalization rule | Instrument metadata covers derivative identity and filters; official order documentation states perpetual and futures quantity uses the base coin. |
| `okx-spot` | ready for a bounded adapter | Official instrument metadata exposes identity, assets, state, tick size, lot size and lifecycle timestamps. |
| `okx-swap-futures` | ready with fail-closed multiplier handling | Official metadata exposes `ctVal`, `ctValCcy`, settlement, lifecycle and filters; an adapter must reject a non-unit `ctMult` until represented explicitly. |

“Ready” authorizes only a separate bounded public instrument-snapshot adapter package. It does not accept
any source or authorize capture.

## 3. Cross-source invariants

- Preserve exchange, market type and native instrument identity.
- Use only public endpoints and no exchange credentials.
- Read current rate-limit evidence at runtime where the exchange publishes dynamic limits.
- Paginate Bybit Linear until `nextPageCursor` is empty.
- Do not infer missing derivative contract metadata from a symbol string.
- Reject unsupported contract types, missing settlement metadata and unrepresentable multipliers.
- Keep every source declaration `source_acceptance: false`.
- Do not commit live or licensed raw payloads.
- Do not treat missing instruments or fields as zero values.

## 4. Binance

### 4.1 Spot

The public catalog endpoint is `GET /api/v3/exchangeInfo`. Official documentation examples expose
`symbol`, `status`, `baseAsset`, `quoteAsset`, `PRICE_FILTER.tickSize` and `LOT_SIZE.stepSize`.
The response also publishes current rate-limit objects; implementations must back off on `429` and must
not freeze an example limit as a permanent contract.

The official Spot market-data WebSocket documentation limits incoming control/ping/pong messages,
streams per connection and connection attempts per IP. These are capacity constraints, not acceptance
evidence.

### 4.2 USD-M derivatives

The public catalog endpoint is `GET /fapi/v1/exchangeInfo`. Official examples expose product identity,
contract type, onboarding and delivery timestamps, status, base/quote/margin assets and price/quantity
filters.

The inspected official material does not expose an explicit contract value and value unit suitable for
the foundation `InstrumentSnapshot`. `quantityPrecision` or `LOT_SIZE.stepSize` is not contract-value
evidence. The source therefore remains fail-closed until an official rule or an additional authoritative
field resolves both values.

## 5. Bybit

The public catalog endpoint is `GET /v5/market/instruments-info`.

Spot does not use pagination. Linear has more than the default 500 entries and must be paginated with
`cursor`; the documented maximum page size is 1000.

Official instrument examples expose symbol identity, product type, status, assets, launch/delivery time,
tick size and quantity step. Bybit’s official order documentation states that perpetuals and futures
always use base coin as the quantity unit. The bounded Linear adapter may therefore represent one quantity
unit as contract value `1` in `base_asset`, while retaining the exact source quantity step and rejecting
unsupported products.

The default documented IP limits are ceilings, not target operating rates. Implementations must use
conservative pacing and reconnect behavior.

## 6. OKX

The public catalog endpoint is `GET /api/v5/public/instruments` with an explicit `instType`.
Spot, SWAP and FUTURES are separate bounded requests.

Official metadata exposes `instId`, product type, state, assets or settlement identity, `ctVal`,
`ctValCcy`, `ctMult`, tick size, lot size, listing time and expiry/offline time.

For derivatives, `ctVal` is the documented contract value and `ctValCcy` its unit. Because the foundation
contract has no separate multiplier field, a bounded adapter must fail closed when `ctMult` is non-empty
and cannot be proven equivalent to one under an explicit source rule.

The public WebSocket service documents three connection requests per second per IP, 480
subscribe/unsubscribe/login requests per connection per hour, and ping/pong behavior when no message is
received for less than 30 seconds. Order-book work remains a later package; current OKX documentation
requires sequence evidence and no longer permits relying on the deprecated checksum as integrity proof.

## 7. Sample-evidence boundary

All sample field evidence in this package comes from examples in current official documentation.
No first-party live response was requested or retained. Therefore:

- field structure is verified for adapter design;
- current production inventory, exact counts and endpoint reachability are not verified;
- no source is accepted;
- the future adapter package must produce immutable snapshots and hashes from bounded public requests.

## 8. Next package

Implement bounded public instrument snapshot adapters for:

- `binance-spot`;
- `bybit-spot`;
- `bybit-linear`;
- `okx-spot`;
- `okx-swap-futures`.

Keep `binance-usdm` disabled until explicit contract-value and contract-value-unit evidence is resolved.
The adapter package must not add WebSocket capture or broad market-data collection.
