# Binance Spot Instrument Smoke on Self-Hosted Runner

## Purpose

This package provides a separate, fail-closed execution path for the existing bounded Binance Spot instrument-catalog smoke after GitHub-hosted runners received HTTP 451 from the frozen endpoint.

The repository owner explicitly approved continuing with the established owner-managed Synology staging runner on 2026-07-27. That approval authorizes only one credential-free public market-data request. It does not waive applicable law, Binance terms, environment protection or repository safety rules.

## Reused frozen contract

The self-hosted workflow does not introduce a new collector or endpoint. It reuses:

- `ai_platform.market_data.binance_spot_instrument_smoke`;
- `ai_platform/market_data/binance-spot-instrument-smoke-policy-v1.json`;
- `https://api.binance.com/api/v3/exchangeInfo` through the frozen policy;
- one attempt and zero retries;
- a 20-second timeout;
- a 16 MiB maximum response;
- redirect refusal;
- exact raw and normalized artifact evidence;
- `source_acceptance = false`.

It must not switch to `api1.binance.com`, `api-gcp.binance.com`, `data-api.binance.vision` or another endpoint in response to HTTP 451.

## Runner and environment boundary

The guarded workflow routes by the dedicated runner's only registered custom label:

- routing label: `freqtrade-staging`;
- exact runner name asserted after assignment: `freqtrade-synology-staging`;
- protected environment: `synology-staging`;
- runner operating system asserted after assignment: `Linux`;
- runner architecture asserted after assignment: `X64` or `ARM64`.

The dedicated runner entrypoint registers with `--labels freqtrade-staging --no-default-labels`. Therefore `self-hosted`, `Linux` and `X64` are not routing labels and must not be added to `runs-on`. Identity, operating system and architecture remain fail-closed runtime assertions before transport.

There is no fallback to GitHub-hosted runners, another self-hosted label or an alternate runner identity.

## Credential and routing refusal

Before creating the runtime, the workflow rejects recognized Binance, Bybit, OKX, generic exchange and Freqtrade exchange credential variables.

It also rejects uppercase and lowercase HTTP, HTTPS and all-protocol proxy variables. The task must not use a proxy, VPN workflow, alternate runner region or endpoint change to bypass a geographic or legal response.

## Isolated runtime

The workflow uses the runner's existing `python3` only to create a temporary virtual environment below `runner.temp`. It installs the repository-pinned `jsonschema==4.26.0`, verifies `Draft202012Validator`, runs the existing smoke module and removes the virtual environment in an `always()` cleanup step.

No global package installation, Docker mutation, persistent runner configuration or service restart is authorized.

## Trigger contract

The workflow remains inert until a separate pull request adds exactly:

`ai_platform/market_data/run-requests/binance-spot-instrument-smoke-selfhosted-v1.json`

The request content must remain equivalent to the existing public-only smoke request. The trigger pull request must contain no other changed path and must be closed without merge after terminal evidence is collected.

## Result interpretation

A successful artifact proves only that one public Binance Spot instrument-catalog response was reachable and parseable from the approved self-hosted runner at that time. It does not prove continuous availability, WebSocket behavior, capacity, trading availability or production suitability.

A successful result does not grant source acceptance. Any source-acceptance decision remains a separate reviewed task.

HTTP 451, another HTTP error, timeout, TLS failure, content-type mismatch, oversized response or parser failure leaves the source fail-closed. The task must record the exact first failure and must not retry automatically.
