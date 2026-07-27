---
task_id: FTAI-20260726-market-data-binance-spot-instrument-smoke-v1
status: blocked
branch: develop
base_branch: develop
created: 2026-07-26
updated: 2026-07-27
related_pr: "#429"
owned_paths:
  - ai_platform/market_data/binance_spot_instrument_smoke.py
  - ai_platform/market_data/binance-spot-instrument-smoke-policy-v1.json
  - tests/ai_platform_integration/test_market_data_binance_spot_instrument_smoke.py
  - docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SMOKE.md
  - .github/workflows/ai-platform-binance-spot-instrument-smoke.yml
  - docs/agents/tasks/FTAI-20260726-market-data-binance-spot-instrument-smoke-v1.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/market_data/ARCHITECTURE.md
  - docs/ai_platform/market_data/INSTRUMENT_SNAPSHOT_ADAPTERS.md
  - ai_platform/market_data/instrument_adapters.py
  - docs/agents/tasks/FTAI-20260726-market-data-instrument-snapshot-adapters-v1.md
search_first:
  - current develop HEAD and open market-data, liquidation, collector and smoke PR ownership
  - existing guarded one-shot workflow patterns
optional_reads: []
---

# Binance Spot instrument catalog smoke v1

## Goal

Add guarded infrastructure for one credential-free Binance Spot `exchangeInfo` request, exact raw and normalized artifact evidence, and a separate exact-one-file trigger. Do not authorize source acceptance, retries, WebSockets or broad capture.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-27T10:02:00+02:00
head: f21a258643d70b4387e366e8b466dbc56735f44f
branch: develop
pr: "#429"
status: blocked
context_routes:
  - docs/ai_platform/market_data/ARCHITECTURE.md
  - docs/ai_platform/market_data/INSTRUMENT_SNAPSHOT_ADAPTERS.md
  - ai_platform/market_data/binance_spot_instrument_smoke.py
  - docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SMOKE.md
owned_paths:
  - ai_platform/market_data/binance_spot_instrument_smoke.py
  - ai_platform/market_data/binance-spot-instrument-smoke-policy-v1.json
  - tests/ai_platform_integration/test_market_data_binance_spot_instrument_smoke.py
  - docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SMOKE.md
  - .github/workflows/ai-platform-binance-spot-instrument-smoke.yml
  - docs/agents/tasks/FTAI-20260726-market-data-binance-spot-instrument-smoke-v1.md
proven:
  - Instrument snapshot adapters v1 are merged and expose the deterministic Binance Spot parser.
  - Smoke infrastructure PR 406 was squash-merged as ae63e2aaa403dc3d0a7e192edca6f8126f2d5dbb after exact-head AI Platform CI, full Freqtrade CI and security analysis passed.
  - The merged workflow requires an exact-one-file trigger, refuses recognized trading credentials, freezes one attempt and zero retries, and uploads raw plus normalized evidence only as a temporary artifact.
  - First trigger PR 425 passed scope and credential checks but failed before transport because jsonschema was absent from the lightweight runner environment.
  - Diagnostics PR 427 isolated ModuleNotFoundError for jsonschema; PR 425 and PR 427 were closed without merge.
  - Runtime dependency fix PR 429 passed exact-head pre-commit, documentation, final CI gate and security analysis, then squash-merged as 6bfcff630ca3aa37b766995b16b84ee03fec39fe.
  - Fresh trigger PR 430 changed exactly the canonical request file; scope, credential refusal, Python setup and jsonschema import verification passed.
  - Smoke run 30247410490 job 89917454366 reached the frozen Binance Spot endpoint and failed with urllib.error.HTTPError HTTP Error 451.
  - Diagnostics PR 433 isolated the exact HTTP 451 result; PR 430 and PR 433 were closed without merge.
  - No successful response payload or normalized catalog artifact was produced and source_acceptance remains false.
derived:
  - The missing dependency defect is repaired and is not the current blocker.
  - HTTP 451 is external regional or legal access denial for the GitHub-hosted runner environment, not evidence of an adapter mapping defect.
  - Repeating the same request from GitHub-hosted runners, changing endpoint, hopping regions or adding retries would violate the bounded fail-closed policy.
unknown:
  - Binance Spot endpoint behavior from a separately approved compliant runner in a jurisdiction where public market-data access is legally permitted.
  - Exact current production payload and normalized instrument counts because no successful response was obtained.
  - Continuous availability, capacity and WebSocket semantics, which remain outside this task.
conflicts: []
first_failure:
  marker: BINANCE_HTTP_451_ON_GITHUB_HOSTED_RUNNER
  evidence: Smoke job 89917454366 reached https://api.binance.com/api/v3/exchangeInfo after all local gates passed and raised urllib.error.HTTPError HTTP Error 451; diagnostics job 89919839815 reproduced the exact terminal line.
rejected_hypotheses:
  - Classify the second trigger as an adapter, schema or jsonschema runtime failure.
  - Retry from the same GitHub-hosted environment.
  - Switch to an alternate Binance endpoint, runner region or proxy to bypass HTTP 451.
  - Add retries or another source family.
  - Commit raw Binance response bytes to Git.
  - Treat the failed smoke as source acceptance or source rejection beyond this runner environment.
changed_paths:
  - docs/agents/tasks/FTAI-20260726-market-data-binance-spot-instrument-smoke-v1.md
validation:
  - command: smoke infrastructure exact-head CI and merge
    result: PASS
    evidence: PR 406 passed AI Platform CI, full Freqtrade CI and security analysis before merge ae63e2aaa403dc3d0a7e192edca6f8126f2d5dbb.
  - command: runtime dependency fix exact-head CI and merge
    result: PASS
    evidence: PR 429 passed pre-commit, documentation, final CI gate and security analysis before merge 6bfcff630ca3aa37b766995b16b84ee03fec39fe.
  - command: fresh exact-one-file trigger validation
    result: PASS
    evidence: PR 430 passed exact-one-file scope, credential refusal, Python setup and jsonschema import verification.
  - command: bounded public Binance Spot request
    result: BLOCKED
    evidence: Run 30247410490 job 89917454366 returned HTTP 451 from the frozen endpoint with one attempt and zero retries.
  - command: temporary trigger and diagnostics cleanup
    result: PASS
    evidence: PR 425, PR 427, PR 430 and PR 433 are closed without merge.
blockers:
  - GitHub-hosted runner access to the frozen Binance Spot endpoint is denied with HTTP 451.
next_action: Obtain explicit approval for a compliant runner in a jurisdiction where Binance public market-data access is legally permitted, then rerun the unchanged one-shot request under a separate task while keeping source_acceptance false.
```
