---
task_id: FTAI-20260726-market-data-binance-spot-instrument-smoke-v1
status: validating
branch: fix/binance-spot-smoke-jsonschema-runtime
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
updated_at: 2026-07-27T09:38:00+02:00
head: 707d29c984d234e28560197df0ef789665844fc6
branch: fix/binance-spot-smoke-jsonschema-runtime
pr: "#429"
status: validating
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
  - Trigger PR 425 changed exactly the canonical request file and passed trigger-scope and credential checks.
  - Trigger run 30245809188 failed before transport; the Binance endpoint was not contacted.
  - Diagnostics PR 427 isolated the exact exception as ModuleNotFoundError for jsonschema while importing ai_platform.market_data.contracts.
  - PR 425 and PR 427 were closed without merge.
  - Project metadata declares jsonschema as a runtime dependency.
  - PR 429 adds a minimal workflow install and import verification for jsonschema before the smoke runner.
derived:
  - The first smoke result contains no Binance reachability evidence and must not be classified as a source failure.
  - A fresh trigger is required after the runtime dependency fix is merged.
unknown:
  - Current Binance endpoint reachability and exact production payload because no request has completed yet.
  - Continuous availability, capacity and WebSocket semantics, which remain outside this task.
conflicts: []
first_failure:
  marker: MISSING_JSONSCHEMA_RUNTIME
  evidence: Smoke job 89912491614 raised ModuleNotFoundError No module named jsonschema before transport. Diagnostics job 89914899790 reproduced the exact traceback from the archived job log.
rejected_hypotheses:
  - Classify the first trigger as a Binance network or regional block.
  - Retry the failed trigger without repairing the deterministic dependency defect.
  - Add retries, alternate endpoints or another source family.
  - Commit raw Binance response bytes to Git.
  - Treat one successful smoke as source acceptance.
changed_paths:
  - .github/workflows/ai-platform-binance-spot-instrument-smoke.yml
  - docs/agents/tasks/FTAI-20260726-market-data-binance-spot-instrument-smoke-v1.md
validation:
  - command: exact first-failure diagnostics
    result: PASS
    evidence: Diagnostics job 89914899790 isolated ModuleNotFoundError for jsonschema and confirmed the endpoint was never contacted.
  - command: temporary trigger and diagnostics cleanup
    result: PASS
    evidence: PR 425 and PR 427 are closed without merge.
  - command: PR 429 changed-file inspection
    result: PASS
    evidence: The fix is limited to the smoke workflow and this durable checkpoint.
  - command: exact-head repository CI
    result: NOT_RUN
    evidence: GitHub Actions is pending on the checkpoint update commit.
blockers: []
next_action: Complete exact-head CI for PR 429, merge the runtime dependency fix, then create a fresh exact-one-file trigger and inspect its immutable smoke artifact.
```
