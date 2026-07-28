# Binance Spot Reduced-Payload Instrument Smoke on Self-Hosted Runner

## Purpose

This package provides a separate, fail-closed execution path for one public Binance Spot instrument-catalog snapshot on the established owner-managed Synology staging runner.

The original v1 request reached `https://api.binance.com/api/v3/exchangeInfo` successfully on 2026-07-28 but the response exceeded the frozen 16 MiB maximum before complete persistence and normalization. It was not retried and did not grant source acceptance.

Policy v2 keeps the same REST endpoint and adds only the official optional query parameter:

`showPermissionSets=false`

Binance documents this parameter as controlling whether `permissionSets` is populated and records that it may be used to reduce payload size. The repository parser does not consume `permissionSets`; it requires symbol identity, status, base and quote assets, `PRICE_FILTER.tickSize` and `LOT_SIZE.stepSize`.

Official references:

- <https://github.com/binance/binance-spot-api-docs/blob/master/rest-api.md#exchange-information>
- <https://github.com/binance/binance-spot-api-docs/blob/master/CHANGELOG.md#2024-10-17>

## Frozen v2 contract

The self-hosted workflow reuses `ai_platform.market_data.binance_spot_instrument_smoke` with:

- policy `ai_platform/market_data/binance-spot-instrument-smoke-policy-v2.json`;
- exact URL `https://api.binance.com/api/v3/exchangeInfo?showPermissionSets=false`;
- one attempt and zero retries;
- a 20-second timeout;
- a 16 MiB maximum response;
- redirect refusal;
- JSON content-type validation;
- exact raw and normalized evidence on success;
- bounded failure evidence on terminal failure;
- `source_acceptance = false`.

The v1 policy remains supported for historical compatibility but is no longer used by the self-hosted trigger workflow.

The task must not switch to `api1.binance.com`, `api-gcp.binance.com`, `data-api.binance.vision` or another endpoint. It must not remove the query parameter, raise the byte limit, add retries or alter source acceptance inside a trigger pull request.

## Runner and environment boundary

The guarded workflow routes by the dedicated runner's only registered custom label:

- routing label: `freqtrade-staging`;
- exact runner name asserted after assignment: `freqtrade-synology-staging`;
- protected environment: `synology-staging`;
- runner operating system asserted after assignment: `Linux`;
- runner architecture asserted after assignment: `X64` or `ARM64`.

The dedicated runner registers with `--labels freqtrade-staging --no-default-labels`. Therefore `self-hosted`, `Linux` and `X64` are not routing labels. Identity, operating system and architecture remain fail-closed runtime assertions before transport.

There is no fallback to GitHub-hosted runners, another self-hosted label or an alternate runner identity.

## Credential and routing refusal

Before creating the runtime, the workflow rejects recognized Binance, Bybit, OKX, generic exchange and Freqtrade exchange credential variables.

It also rejects uppercase and lowercase HTTP, HTTPS and all-protocol proxy variables. The task must not use a proxy, VPN workflow, alternate runner region or endpoint change to bypass a geographic or legal response.

## Isolated runtime

The workflow reuses the repository-approved, SHA-pinned `astral-sh/setup-uv` action to install and activate an isolated Python 3.12 environment. Action caching is disabled. The runtime installs only `jsonschema==4.26.0`, verifies `Draft202012Validator`, runs the existing smoke module and removes `.venv` in an `always()` cleanup step.

No global package installation, Docker mutation, runner-image change, persistent runner configuration or service restart is authorized.

## Trigger contract

The workflow remains inert until a separate pull request adds exactly:

`ai_platform/market_data/run-requests/binance-spot-instrument-smoke-selfhosted-v2.json`

The request must contain the v2 request and policy versions, the exact reduced-payload URL, public-only execution, raw-payload persistence and `source_acceptance = false`.

The trigger pull request must contain no other changed path and must be closed without merge after terminal evidence is collected.

## Evidence contract

On success, the evidence directory contains:

- `raw-response.json`;
- `instrument-catalog-snapshot.json`;
- `run-request.json`;
- `policy.json`;
- `report.json`;
- `checksums.sha256`.

On transport, response-header, response-body, JSON-decoding or parser failure, the evidence directory contains:

- `run-request.json`;
- `policy.json`;
- `failure-report.json`;
- `checksums.sha256`.

The failure report records the exact stage, error type and message, attempt count, frozen timeout and byte limit, available response metadata, whether a size was declared or observed, and `source_acceptance = false`. A partial oversized payload is not persisted or treated as parseable evidence.

## Result interpretation

A successful artifact proves only that one reduced-payload public Binance Spot instrument-catalog response was reachable and parseable from the approved self-hosted runner at that time. It does not prove continuous availability, WebSocket behavior, capacity, trading availability or production suitability.

A successful result does not grant source acceptance. Any source-acceptance decision remains a separate reviewed task.

HTTP 451, another HTTP error, timeout, TLS failure, content-type mismatch, oversized response or parser failure leaves the source fail-closed. The task must record the exact first failure and must not retry automatically.
