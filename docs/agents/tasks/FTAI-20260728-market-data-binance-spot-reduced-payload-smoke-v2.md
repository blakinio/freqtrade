---
task_id: FTAI-20260728-market-data-binance-spot-reduced-payload-smoke-v2
status: completed
branch: docs/binance-spot-reduced-payload-smoke-v2-terminal-pass
base_branch: develop
created: 2026-07-28
updated: 2026-07-28
related_pr: "#620"
owned_paths:
  - ai_platform/market_data/binance_spot_instrument_smoke.py
  - ai_platform/market_data/binance-spot-instrument-smoke-policy-v2.json
  - .github/workflows/ai-platform-binance-spot-instrument-smoke-selfhosted.yml
  - tests/ai_platform_integration/test_market_data_binance_spot_instrument_smoke.py
  - tests/ai_platform_integration/test_market_data_binance_spot_smoke_request_headers.py
  - tests/ai_platform_integration/test_market_data_binance_spot_instrument_smoke_selfhosted_workflow.py
  - docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SMOKE_SELFHOSTED.md
  - docs/agents/tasks/FTAI-20260728-market-data-binance-spot-reduced-payload-smoke-v2.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SMOKE_SELFHOSTED.md
  - ai_platform/market_data/binance_spot_instrument_smoke.py
  - ai_platform/market_data/instrument_adapters.py
  - .github/workflows/ai-platform-binance-spot-instrument-smoke-selfhosted.yml
search_first:
  - current develop and open Binance Spot smoke ownership
optional_reads: []
---

# Binance Spot reduced-payload smoke v2

## Goal

Add a separately reviewed reduced-payload Binance Spot smoke contract that keeps the frozen 16 MiB limit and all safety boundaries, persists deterministic failure evidence, and permits one new exact-one-file self-hosted trigger only after exact-head CI and a no-request proof.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-28T13:53:00+02:00
base_develop: 68aad2c9593b158af72d8885dd620e5680625d69
branch: docs/binance-spot-reduced-payload-smoke-v2-terminal-pass
implementation_pr: "#609"
proof_pr: "#619"
trigger_pr: "#620"
status: completed
proven:
  - Previous v1 self-hosted workflow 30345196797 job 90229653635 executed exactly one public request and failed closed because the unfiltered exchangeInfo response exceeded the frozen 16 MiB maximum.
  - PR 609 preserved v1 compatibility and introduced strict v2 policy and request contracts for https://api.binance.com/api/v3/exchangeInfo?showPermissionSets=false without changing timeout, byte limit, redirect refusal, retries, credentials, proxy refusal or source_acceptance false.
  - PR 609 added deterministic failure-report.json evidence for transport, response-header, response-body, decode and parser failures without persisting an incomplete oversized body.
  - PR 609 exact-head AI Platform CI 30355080294, Freqtrade CI 30355080286 and zizmor 30355080251 completed success at ebbe73b608a50fea9fe8708a93caf23adf351f72.
  - Freqtrade CI included successful pre-commit, documentation, Python 3.11, 3.12 coverage, 3.13, 3.14, build-distributions and CI Gate jobs; online and live compatibility tests remained skipped.
  - PR 609 changed exactly eight declared implementation, policy, workflow, test and documentation paths, had no reviews or unresolved review threads and merged by guarded squash as 68aad2c9593b158af72d8885dd620e5680625d69.
  - Temporary no-request proof PR 619 workflow 30356269381 job 90265085004 completed success on exact runner freqtrade-synology-staging.
  - The proof checked out merged commit 68aad2c9593b158af72d8885dd620e5680625d69, validated the v2 URL and frozen policy, exercised one synthetic oversized response through an injected local opener, verified deterministic failure evidence and performed no exchange request.
  - PR 619 was closed without merge and its branch was reset to develop.
  - Final trigger PR 620 added exactly ai_platform/market_data/run-requests/binance-spot-instrument-smoke-selfhosted-v2.json at 9bb6c75c00471ef3c46da67aefbe950c4de4e4b3.
  - Final workflow 30356428207 job 90265595023 passed checkout, exact-one-file scope, approved runner identity, credential and proxy refusal, isolated setup-uv runtime, the one reduced-payload request, immutable artifact upload and cleanup.
  - The reduced-payload request executed exactly once, returned HTTP 200 application/json;charset=UTF-8 from the exact final URL and completed in 1810.14753 ms.
  - The raw response was 6629829 bytes, below the frozen 16777216-byte maximum.
  - The raw response contained 3659 symbols. permissionSets remained present as an empty array for all 3659 symbols, confirming that the optional field payload was suppressed without removing the parser-required fields.
  - Normalization produced 3659 unique deterministically ordered instruments: 1369 active and 2290 inactive.
  - Trigger report status was pass, attempt_count was 1, redirect_count was 0, broad_capture was false, websocket was false and source_acceptance remained false.
  - Immutable artifact 8686988992 was published as binance-spot-instrument-smoke-selfhosted-v2-620 with archive size 218332 bytes, artifact digest sha256:1862d17e8c117e31eec6688c8f34c32cce4a505ec125805cd095df6894cc4f6e and expiry 2026-08-27T11:51:17Z.
  - The downloaded artifact contained raw-response.json, instrument-catalog-snapshot.json, run-request.json, policy.json, report.json and checksums.sha256.
  - sha256sum verification passed for every evidence file.
  - PR 620 was closed without merge and its branch was reset to develop. No retry or rerun occurred.
evidence:
  workflow_run: 30356428207
  workflow_job: 90265595023
  artifact_id: 8686988992
  artifact_name: binance-spot-instrument-smoke-selfhosted-v2-620
  artifact_archive_bytes: 218332
  artifact_digest: sha256:1862d17e8c117e31eec6688c8f34c32cce4a505ec125805cd095df6894cc4f6e
  artifact_expires_at: 2026-08-27T11:51:17Z
  response_bytes: 6629829
  http_status: 200
  content_type: application/json;charset=UTF-8
  duration_ms: 1810.14753
  instrument_count: 3659
  active_instrument_count: 1369
  inactive_instrument_count: 2290
  raw_response_sha256: d8964a30646d5ce1918b00d9d69393f2555fbf10c31581eb22e845880fd2cd12
  instrument_catalog_file_sha256: db92d71d053b78a2462fd59432406e9456fdfaf86cb1bb3baabbfc7c8f62f62e
  run_request_file_sha256: 5b39099a8c25848810f823db7457ce80005c476aebd058a1d0c70ddc67f86fe8
  policy_file_sha256: 9e6e85dcf734f5c2e8df5668d082be400edd0c5aecdc3678ea9b729459340dcd
  report_file_sha256: 53e30808502fa137b821aadb17620b6155e130aaf4377c6f56e3c786bf1ce40a
  report_sha256: a6ae705bf99fa474d702e7ac41cdfcb13d9ed2392639470220f27ce030763898
  source_snapshot_id: binance-spot:ae9367428359d4722e7c5c37
  source_snapshot_sha256: ae9367428359d4722e7c5c37ae9253ede8ce9ad074a1d6179d898eb089e3af91
  catalog_snapshot_sha256: 4306241b8b0bed21efe8084a59e1fad57964a7368288150cab4c5709d43981e3
validation:
  - command: implementation exact-head repository CI
    result: PASS
    evidence: AI Platform CI 30355080294, Freqtrade CI 30355080286 and zizmor 30355080251 completed success at ebbe73b608a50fea9fe8708a93caf23adf351f72.
  - command: no-request v2 contract and failure-evidence proof
    result: PASS
    evidence: Workflow 30356269381 job 90265085004 completed success on exact runner freqtrade-synology-staging without an exchange request.
  - command: final exact-one-file reduced-payload smoke
    result: PASS
    evidence: Workflow 30356428207 job 90265595023 completed success after exactly one request and immutable artifact upload.
  - command: artifact integrity
    result: PASS
    evidence: The downloaded artifact contained all six expected files and every checksums.sha256 entry verified successfully.
  - command: source acceptance
    result: FALSE
    evidence: Policy, request and report all retained source_acceptance false; this smoke does not grant production source authorization.
rejected:
  - Raise max_response_bytes after the v1 failure without first testing the official reduced-payload parameter.
  - Retry or rerun either the v1 or v2 terminal workflow.
  - Change endpoint host, use a proxy or VPN, change runner region or introduce credentials.
  - Treat one successful REST snapshot as continuous availability, WebSocket readiness, trading availability or production source acceptance.
blockers: []
next_action: Keep source_acceptance false. Any production source-acceptance, recurring collector or WebSocket decision requires a separate reviewed task using artifact 8686988992 as bounded evidence.
```
