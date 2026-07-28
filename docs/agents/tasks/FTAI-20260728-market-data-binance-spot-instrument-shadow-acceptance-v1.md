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
updated_at: 2026-07-28T15:43:00+02:00
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
  - Temporary diagnostic PR 635 workflow 30362301758 job 90284741497 captured exact Ruff 0.15.21 diagnostics without network or branch mutation.
  - SHA-guarded Ruff workflow 30362494245 job 90285387351 changed only the runner and focused test, passed Ruff check and format, and fast-forwarded PR 633.
  - Full Freqtrade CI exposed one overly narrow tamper-test assertion: the evaluator correctly rejected modified raw evidence on manifest size before reaching the hash comparison. The assertion now accepts either fail-closed size or hash mismatch.
  - Temporary diagnostic PR 636 extracted that exact failure and was closed without merge; its branch was reset to develop.
  - AI Platform CI 30363206794 passed after the tamper assertion repair.
  - Pre-commit job 90288008264 identified only mypy typing gaps around dynamic JSON summary values; runtime validation semantics were already fail-closed.
  - Temporary diagnostic PR 637 captured the mypy output and was used only for SHA-guarded transformations without Binance or Synology access.
  - Complete typed-summary workflow 30364594023 job 90292487644 verified exact target head ec569a0521fc46e382fa5c41cda9bb64d22a00f9, changed only ai_platform/market_data/binance_spot_instrument_acceptance.py, passed Ruff, formatter and mypy, and fast-forwarded PR 633 to d9cbd0be6507e4a171c53432652e49c180aea25c.
  - The typing repair added fail-closed numeric summary accessors, an explicitly typed sleep wrapper and typed independent-evaluator summary reads; acceptance thresholds and outcomes are unchanged.
  - Diagnostic PRs 635, 636 and 637 were closed without merge and their branches were reset to develop.
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
  - Focused policy, request, virtual 24-hour runner and independent-evaluator tests passed.
  - Static workflow and documentation boundary tests passed.
  - Ruff, formatter and mypy passed on the complete typed-summary repair before push.
  - Fresh exact-head AI Platform CI pending on the auditable post-repair checkpoint head.
  - Fresh exact-head Freqtrade CI including Python 3.11 through 3.14, build and CI Gate pending on the auditable post-repair checkpoint head.
  - Fresh exact-head zizmor pending on the auditable post-repair checkpoint head.
blockers:
  - Guarded merge requires full exact-head green CI and no unresolved review threads.
next_action: Complete fresh exact-head CI and guarded merge. Do not create the 24-hour trigger until the merged package passes a separate no-network proof on freqtrade-synology-staging.
```
