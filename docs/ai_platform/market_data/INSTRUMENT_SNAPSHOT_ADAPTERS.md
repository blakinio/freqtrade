# Bounded Instrument Snapshot Adapters v1

Status: **deterministic adapter infrastructure only; no live execution or source acceptance**

Implementation: `ai_platform/market_data/instrument_adapters.py`

## 1. Scope

This package implements deterministic parsers and bounded request planning for five public instrument catalogs:

- Binance Spot;
- Bybit Spot;
- Bybit Linear perpetuals and dated futures;
- OKX Spot;
- OKX SWAP and FUTURES.

Binance USD-M remains unavailable because the preceding preflight did not resolve explicit contract value and contract-value unit semantics required by the foundation `InstrumentSnapshot` contract.

The package has no default HTTP client. The caller must inject a `PublicJsonFetcher`. Tests and repository CI use synthetic payloads and perform no exchange request.

## 2. Safety boundary

The adapter boundary:

- accepts public JSON responses only;
- refuses recognized exchange trading credential environment variables before invoking the injected transport;
- contains no private, account, balance, position or order endpoint;
- contains no WebSocket subscription or raw market-data capture;
- does not grant source acceptance;
- does not update the frozen source catalog;
- does not write files, select storage paths or deploy collectors;
- does not authorize replay, models, strategies, portal access or execution.

A later bounded execution package must separately define timeout, retry, host, output and operational evidence policy.

## 3. Snapshot identity

Every catalog result produces an immutable `InstrumentCatalogSnapshot` containing:

- adapter version and source identity;
- capture timestamp supplied by the caller;
- exact ordered request URLs;
- canonical SHA-256 for every supplied response payload;
- an aggregate source snapshot SHA-256 and deterministic source snapshot ID;
- deterministically ordered `InstrumentSnapshot` records;
- a self-hash over the complete snapshot manifest.

Every instrument record is rebound to the same source snapshot ID and source snapshot SHA-256. Duplicate canonical instrument IDs, empty snapshots, hash mismatches and non-deterministic ordering fail closed.

## 4. Source mappings

### 4.1 Binance Spot

Request: `GET https://api.binance.com/api/v3/exchangeInfo`

Mapping:

- identity: `symbol`;
- assets: `baseAsset`, `quoteAsset`;
- active: `status == TRADING`;
- tick size: exactly one `PRICE_FILTER.tickSize`;
- quantity step: exactly one `LOT_SIZE.stepSize`.

Spot contract and settlement metadata remain null.

### 4.2 Bybit Spot

Request: `GET https://api.bybit.com/v5/market/instruments-info?category=spot`

The response must have `retCode == 0`, category `spot` and an empty `nextPageCursor`. A non-empty cursor fails closed because Spot pagination is outside the verified contract.

Mapping uses `symbol`, `baseCoin`, `quoteCoin`, `priceFilter.tickSize`, `lotSizeFilter.basePrecision` and `status == Trading`.

### 4.3 Bybit Linear

Initial request:

`GET https://api.bybit.com/v5/market/instruments-info?category=linear&limit=1000`

The injected transport follows `nextPageCursor` using URL-encoded cursor values. Pagination is bounded to ten pages and rejects repeated cursors.

Supported contract types:

- `LinearPerpetual` → `perpetual` with no expiry;
- `LinearFutures` → `dated_future` with required `deliveryTime`.

The preflight-approved quantity rule represents one source quantity unit as contract value `1` with unit `base_asset`. Settlement uses `settleCoin`.

### 4.4 OKX Spot

Request: `GET https://www.okx.com/api/v5/public/instruments?instType=SPOT`

The response must have `code == "0"` and every row must be `SPOT`. Mapping uses `instId`, `baseCcy`, `quoteCcy`, `tickSz`, `lotSz`, `listTime` and `state == live`. Any non-empty expiry fails closed.

### 4.5 OKX SWAP and FUTURES

Requests:

- `GET https://www.okx.com/api/v5/public/instruments?instType=SWAP`;
- `GET https://www.okx.com/api/v5/public/instruments?instType=FUTURES`.

Mapping uses `instId`, `uly` or `instFamily`, `settleCcy`, `ctVal`, `ctValCcy`, `tickSz`, `lotSz`, `listTime`, `expTime` and `state`.

`SWAP` maps to perpetual and forbids expiry. `FUTURES` maps to dated future and requires expiry. A non-empty `ctMult` must equal one; any non-unit multiplier is rejected because foundation v1 has no separate multiplier field.

## 5. Fail-closed cases

The package rejects:

- Binance USD-M and unknown source IDs;
- recognized trading credentials;
- malformed response containers and non-success source codes;
- wrong categories or instrument types;
- missing or non-positive price/quantity filters;
- unsupported derivative contract types;
- missing settlement, contract value or contract value unit;
- missing dated-future expiry or expiry on spot/perpetual instruments;
- repeated or excessive Bybit pagination;
- non-unit OKX `ctMult`;
- duplicate instruments, empty catalogs and provenance/self-hash mismatch.

## 6. Next package

The next package may run a bounded, public, credential-free instrument-catalog smoke for one source family using these adapters and persist immutable snapshot evidence. It must remain separate from WebSocket capture and cannot grant broad source acceptance from a single smoke result.
