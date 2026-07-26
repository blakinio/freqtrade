---
task_id: FTAI-20260726-market-data-binance-spot-instrument-smoke-v1
status: implementing
branch: feat/market-data-binance-spot-instrument-smoke-v1
base_branch: develop
created: 2026-07-26
updated: 2026-07-26
related_pr: null
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

Add guarded infrastructure for one credential-free Binance Spot `exchangeInfo` request, exact raw and normalized artifact evidence, and a separate exact-one-file trigger. Do not run the endpoint in this infrastructure PR and do not authorize source acceptance, retries, WebSockets or broad capture.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-26T23:00:00+02:00
head: PENDING
branch: feat/market-data-binance-spot-instrument-smoke-v1
pr: "not_opened"
status: implementing
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
  - Instrument snapshot adapters v1 are the required predecessor and expose a deterministic Binance Spot parser.
  - The smallest next live scope is one public Binance Spot exchangeInfo request.
  - Existing repository patterns separate smoke infrastructure from an exact-one-file execution trigger.
  - Raw exchange payloads belong in temporary workflow artifacts and not Git.
derived:
  - A standard-library HTTP runner can enforce one attempt, bounded bytes, timeout, content type, redirect and credential boundaries without adding a runtime dependency.
  - Successful transport and mapping evidence cannot grant broad source acceptance.
unknown:
  - Current endpoint reachability and exact production payload until the separate trigger PR runs.
  - Continuous availability, capacity and WebSocket semantics, which are outside this task.
conflicts: []
first_failure:
  marker: NONE
  evidence: Implementation and exact-head CI have not run yet.
rejected_hypotheses:
  - Execute the endpoint from the infrastructure PR.
  - Add retries or multiple source families.
  - Commit raw Binance response bytes to Git.
  - Treat one successful smoke as source acceptance.
changed_paths:
  - ai_platform/market_data/binance_spot_instrument_smoke.py
  - ai_platform/market_data/binance-spot-instrument-smoke-policy-v1.json
  - tests/ai_platform_integration/test_market_data_binance_spot_instrument_smoke.py
  - docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SMOKE.md
  - .github/workflows/ai-platform-binance-spot-instrument-smoke.yml
  - docs/agents/tasks/FTAI-20260726-market-data-binance-spot-instrument-smoke-v1.md
validation:
  - command: live-state and ownership preflight
    result: NOT_RUN
    evidence: The predecessor merge must complete before branch creation.
  - command: focused synthetic runner tests and repository CI
    result: NOT_RUN
    evidence: Infrastructure files are not committed yet.
blockers: []
next_action: Merge the adapter predecessor, create this six-file infrastructure package, validate exact-head CI and merge it before creating the separate one-file trigger.
```
