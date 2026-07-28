---
task_id: FTAI-20260728-market-data-binance-spot-instrument-shadow-acceptance-v1
status: validating
branch: feat/binance-spot-instrument-shadow-acceptance-v1
base_branch: develop
created: 2026-07-28
updated: 2026-07-28
related_pr: "#633"
owned_paths:
  - ai_platform/market_data/binance-spot-instrument-shadow-acceptance-policy-v1.json
  - ai_platform/market_data/binance_spot_instrument_acceptance.py
  - .github/workflows/ai-platform-binance-spot-instrument-shadow-acceptance.yml
  - tests/ai_platform_integration/test_market_data_binance_spot_instrument_acceptance.py
  - docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SHADOW_ACCEPTANCE.md
  - docs/agents/tasks/FTAI-20260728-market-data-binance-spot-instrument-shadow-acceptance-v1.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SMOKE_SELFHOSTED.md
  - docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SHADOW_ACCEPTANCE.md
  - docs/agents/tasks/FTAI-20260728-market-data-binance-spot-reduced-payload-smoke-v2.md
  - ai_platform/market_data/binance_spot_instrument_smoke.py
  - ai_platform/market_data/instrument_adapters.py
search_first:
  - current develop and open Binance Spot market-data acceptance ownership
optional_reads:
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE_EXECUTION.md
  - ai_platform/research/liquidations/okx-liquidation-shadow-acceptance-policy-v1.json
---

# Binance Spot instrument shadow acceptance v1

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-28T15:17:00+02:00
status: validating
branch: feat/binance-spot-instrument-shadow-acceptance-v1
base_develop: 81a45bbae0e7b63655ca5a684fb110c5a03fb4d5
implementation_pr: "#633"
proven:
  - Reduced-payload implementation PR 609 merged as 68aad2c9593b158af72d8885dd620e5680625d69.
  - No-request proof workflow 30356269381 job 90265085004 completed success on exact runner freqtrade-synology-staging.
  - Exact-one-file smoke trigger PR 620 executed workflow 30356428207 job 90265595023 exactly once and closed without merge.
  - Smoke artifact 8686988992 has digest sha256:1862d17e8c117e31eec6688c8f34c32cce4a505ec125805cd095df6894cc4f6e.
  - The reviewed smoke returned HTTP 200 in 1810.14753 ms with 6629829 bytes and normalized 3659 instruments, including 1369 active.
  - All six smoke evidence files and their checksum index verified successfully.
  - Smoke policy, request and report kept source_acceptance false and production remained disabled.
  - Repository OKX precedent requires a separate operational acceptance window, durable raw evidence, independent evaluation and accepted/rejected/inconclusive outcomes before any later integration proposal.
  - PR 633 initial AI Platform CI 30362097366 compiled the package and passed all focused functional tests, including the virtual 24-hour runner, independent evaluator, fail-closed parse sample, credential and proxy refusal, and tamper detection.
  - The only initial AI Platform failure was Ruff static validation after tests had passed.
  - Temporary diagnostic PR 635 workflow 30362301758 job 90284741497 captured exact Ruff 0.15.21 diagnostics without network or branch mutation.
  - Ruff required one local C901 justification on the frozen request validator, itertools.pairwise for consecutive catalog counts, removal of one unused noqa, and formatter output for the runner and focused test.
  - SHA-guarded workflow 30362494245 job 90285387351 verified exact target head 803e7ce021022bba7de08a66502da393098dfdd8, changed only the runner and focused test, passed Ruff check and format, and fast-forwarded PR 633 to af3e0b763e90e5d08ae61750d6deb89a06924201.
  - Diagnostic PR 635 was closed without merge and its branch was reset to develop.
changes:
  - Add a frozen 24-hour Binance Spot instrument shadow-acceptance policy.
  - Schedule 97 observations at 15-minute intervals on exact runner freqtrade-synology-staging.
  - Reuse the reviewed reduced-payload transport and existing Binance Spot parser; do not create a parallel collector or parser.
  - Keep one request attempt and zero retries per scheduled observation.
  - Persist successful raw and normalized snapshots under the canonical durable Synology state root.
  - Persist bounded sample failure metadata without incomplete raw payloads.
  - Add deterministic summary, manifest, terminal report, self hashes and complete checksum index.
  - Add an independent evaluator that recomputes summary metrics, gates and terminal outcome.
  - Upload only bounded metadata to GitHub Actions while raw evidence remains durable on Synology.
  - Keep source_acceptance false, production_source_enabled false and orders_submitted zero even when the shadow outcome is accepted.
policy:
  endpoint: https://api.binance.com/api/v3/exchangeInfo?showPermissionSets=false
  duration_seconds: 86400
  sample_interval_seconds: 900
  scheduled_samples: 97
  timeout_seconds: 20
  maximum_response_bytes: 16777216
  retries_per_sample: 0
  minimum_successful_samples: 95
  minimum_availability_ratio: 0.98
  maximum_consecutive_failures: 1
  maximum_transport_failures: 2
  maximum_parse_failures: 0
  minimum_instrument_count: 3000
  minimum_active_instrument_count: 1000
  required_active_native_symbols:
    - BTCUSDT
    - ETHUSDT
  maximum_consecutive_catalog_count_change_ratio: 0.02
safety:
  - No canonical trigger request is included in this implementation branch.
  - No Binance request executes from implementation CI or tests; tests use an injected local opener and virtual clock.
  - GitHub-hosted runners remain forbidden for the acceptance run.
  - Trading credentials and proxy variables are refused before runtime or network activity.
  - No alternate endpoint, VPN, WebSocket, order, replay, model, strategy or live-capital capability is added.
  - An accepted shadow package authorizes only a later separately reviewed integration proposal.
validation:
  - Focused policy, request, virtual 24-hour runner and independent-evaluator tests passed at the initial head before Ruff repair.
  - Static workflow and documentation boundary tests passed at the initial head before Ruff repair.
  - Fresh exact-head AI Platform CI pending at the post-Ruff checkpoint head.
  - Fresh exact-head Freqtrade CI including CI Gate pending at the post-Ruff checkpoint head.
  - Fresh exact-head zizmor pending at the post-Ruff checkpoint head.
blockers:
  - Guarded merge requires full exact-head green CI and no unresolved review threads.
next_action: Complete fresh exact-head CI and guarded merge. Do not create the 24-hour trigger until the merged package passes a separate no-network proof on freqtrade-synology-staging.
```
