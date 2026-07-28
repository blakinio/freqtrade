---
task_id: FTAI-20260728-market-data-binance-spot-instrument-shadow-acceptance-v1
status: proof-queued-runner-occupied
branch: docs/binance-instrument-acceptance-proof-queued
base_branch: develop
created: 2026-07-28
updated: 2026-07-28
related_pr: "#639"
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
updated_at: 2026-07-28T16:10:00+02:00
status: proof-queued-runner-occupied
branch: docs/binance-instrument-acceptance-proof-queued
implementation_pr: "#633"
implementation_merge: aeb858ebe5266742c257aa7b45b5cffd11c4b5ba
proof_pr: "#639"
proof_workflow_run: 30366399985
proof_job: 90298645354
proven:
  - Reduced-payload implementation PR 609 merged as 68aad2c9593b158af72d8885dd620e5680625d69.
  - No-request smoke proof workflow 30356269381 job 90265085004 completed success on exact runner freqtrade-synology-staging.
  - Exact-one-file smoke trigger PR 620 executed workflow 30356428207 job 90265595023 exactly once and closed without merge.
  - Smoke artifact 8686988992 has digest sha256:1862d17e8c117e31eec6688c8f34c32cce4a505ec125805cd095df6894cc4f6e.
  - The reviewed smoke returned HTTP 200 in 1810.14753 ms with 6629829 bytes and normalized 3659 instruments, including 1369 active.
  - PR 633 added the frozen 24-hour, 97-slot Binance Spot instrument shadow-acceptance package without adding its canonical execution request.
  - The package reuses the reviewed reduced-payload transport and existing Binance Spot parser, performs one request and zero retries per scheduled observation, and preserves raw plus normalized successful snapshots under the canonical durable Synology root.
  - The package adds deterministic sample reports, summary, manifest, terminal report, self hashes, complete checksum index and an independent evaluator that recomputes the package and outcome.
  - Even an accepted shadow outcome keeps source_acceptance false, production_source_enabled false and orders_submitted zero.
  - PR 633 exact-head AI Platform CI 30364864990, Freqtrade CI 30364864798 and zizmor 30364864240 completed success at b2ade29cee162a84d6b6e46d291c836a823954fe.
  - Freqtrade CI passed pre-commit, documentation, Python 3.11, Python 3.12 coverage, Python 3.13 including Ruff, format and mypy, Python 3.14, build distributions and CI Gate; online and live compatibility tests remained skipped.
  - PR 633 changed exactly six declared policy, runtime, workflow, test and documentation files, was mergeable, and had no reviews or unresolved review threads.
  - PR 633 merged by guarded squash as aeb858ebe5266742c257aa7b45b5cffd11c4b5ba.
  - Temporary proof PR 639 adds exactly one no-network workflow and checks out the exact merged implementation commit.
  - Proof PR 639 is designed to validate exact runner identity, canonical durable-root atomic IO, all 97 virtual observation slots, accepted and rejected packages, independent evaluation, tamper rejection, credential refusal, proxy refusal, zero orders and disabled source state without any Binance request.
  - Proof workflow 30366399985 job 90298645354 is queued on routing label freqtrade-staging.
  - The dedicated runner is intentionally occupied by governed OKX 24-hour acceptance PR 624 workflow 30358400049 job 90271896559, whose frozen acceptance package is actively running.
  - The OKX run was not cancelled, reprioritized or modified. No alternate runner, endpoint, proxy, VPN or region was introduced for the Binance proof.
  - The canonical Binance 24-hour trigger request does not exist and no Binance acceptance observation has executed.
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
validation:
  implementation_exact_head_ai_platform_ci:
    run: 30364864990
    result: PASS
  implementation_exact_head_freqtrade_ci:
    run: 30364864798
    result: PASS
  implementation_exact_head_security:
    run: 30364864240
    result: PASS
  no_network_exact_runner_proof:
    pr: 639
    run: 30366399985
    job: 90298645354
    result: QUEUED
safety:
  - No canonical Binance acceptance request is present.
  - No Binance request has executed from the acceptance package.
  - GitHub-hosted and alternate self-hosted runner fallback remains forbidden.
  - Trading credentials, proxy routing, alternate endpoints, VPN, WebSocket, replay, model work, strategy work, orders and live capital remain unauthorized.
  - Source acceptance and production enablement remain false.
blockers:
  - Exact-runner no-network proof is queued behind the already-running governed OKX 24-hour acceptance on the single dedicated staging runner.
next_action: After governed OKX workflow 30358400049 becomes terminal and releases freqtrade-synology-staging, allow queued proof workflow 30366399985 to execute. Close PR 639 without merge after terminal proof, reset its branch, update this checkpoint, and only then consider a separate exact-one-file 24-hour Binance acceptance trigger.
```
