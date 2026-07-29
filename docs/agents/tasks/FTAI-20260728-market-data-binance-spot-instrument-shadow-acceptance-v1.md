---
task_id: FTAI-20260728-market-data-binance-spot-instrument-shadow-acceptance-v1
status: ready
branch: ci/prove-binance-spot-instrument-shadow-acceptance-runtime-v2
base_branch: develop
created: 2026-07-28
updated: 2026-07-29
related_pr: "#695"
owned_paths:
  - ai_platform/market_data/binance-spot-instrument-shadow-acceptance-policy-v1.json
  - ai_platform/market_data/binance_spot_instrument_acceptance.py
  - .github/workflows/ai-platform-binance-spot-instrument-shadow-acceptance-v2.yml
  - tools/market_data/binance_spot_instrument_acceptance_v2_preflight.py
  - tests/ai_platform_integration/test_market_data_binance_spot_instrument_acceptance_v2.py
  - docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SHADOW_ACCEPTANCE_V2.md
  - docs/agents/tasks/FTAI-20260728-market-data-binance-spot-instrument-shadow-acceptance-v1.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SHADOW_ACCEPTANCE.md
  - docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SHADOW_ACCEPTANCE_V2.md
search_first:
  - current existence of the canonical v2 request path
  - current availability of freqtrade-synology-staging
optional_reads:
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE_EXECUTION.md
---

# Binance Spot instrument shadow acceptance v1

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-29T16:10:00+02:00
head: 6687a6c77a26711eb2e364b41c14629a8dce1564
branch: ci/prove-binance-spot-instrument-shadow-acceptance-runtime-v2
pr: "#695"
status: ready
context_routes:
  - Binance Spot public instrument-catalog acceptance
  - Synology self-hosted staging runner
  - credential-free deterministic evidence
owned_paths:
  - .github/workflows/ai-platform-binance-spot-instrument-shadow-acceptance-v2.yml
  - tools/market_data/binance_spot_instrument_acceptance_v2_preflight.py
  - tests/ai_platform_integration/test_market_data_binance_spot_instrument_acceptance_v2.py
  - docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SHADOW_ACCEPTANCE_V2.md
  - docs/agents/tasks/FTAI-20260728-market-data-binance-spot-instrument-shadow-acceptance-v1.md
proven:
  - Original acceptance implementation remains merged as aeb858ebe5266742c257aa7b45b5cffd11c4b5ba with unchanged policy, transport, parser, thresholds, durable evidence and independent evaluator.
  - Consumed v1 trigger workflow 30456309522 failed before network because its isolated runtime lacked jsonschema; no observation or package was created and PR 687 was closed without merge.
  - Runtime v2 repair PR 690 merged as 224ee218b2e62b68c2888e27913a2c3d6c35dfc9 after exact-head AI Platform CI, full Freqtrade CI and zizmor success.
  - Runtime v2 installs and verifies jsonschema 4.26.0 before package import and watches only ai_platform/market_data/run-requests/binance-spot-instrument-shadow-acceptance-20260729-v2.json.
  - Runtime v2 freezes request_id binance-spot-instrument-shadow-acceptance-20260729-v2 and run_id binance-spot-instrument-shadow-acceptance-20260729-v2-r1 while retaining the v1 policy and production-disabled zero-order boundary.
  - Proof PR 695 changed exactly one workflow above exact merged repair 224ee218b2e62b68c2888e27913a2c3d6c35dfc9 and was closed without merge at head 6687a6c77a26711eb2e364b41c14629a8dce1564.
  - Proof workflow 30458935489 job 90599644500 completed success on exact runner freqtrade-synology-staging.
  - Proof validated the exact merged parent, approved runner, canonical durable root, credential and proxy refusal, pinned dependency and complete v2 static preflight.
  - Proof executed complete accepted and rejected 97-slot packages with injected local openers and virtual clocks, independent evaluation, tamper rejection, zero orders and production disabled.
  - Terminal marker BINANCE_SPOT_INSTRUMENT_SHADOW_ACCEPTANCE_V2_NO_NETWORK_PROOF_PASS was recorded after successful cleanup.
  - No canonical v2 request exists, no v2 Binance observation has executed and no durable v2 run directory was left by proof execution.
derived:
  - The exact merged runtime v2 is ready for one separately reviewed canonical v2 24-hour trigger on the approved staging runner.
  - The trigger must add exactly the frozen v2 request path and be closed without merge after its one opened-event execution.
unknown:
  - Outcome of the real v2 24-hour Binance acceptance window.
conflicts: []
first_failure:
  marker: none
  evidence: Workflow 30458935489 job 90599644500 and every proof step completed success with the frozen terminal marker.
rejected_hypotheses:
  - Reuse, reopen, synchronize or rerun the consumed v1 request or either proof PR.
  - Add implementation, workflow or documentation changes to the v2 trigger PR.
  - Treat proof success as source acceptance or production enablement.
changed_paths:
  - docs/agents/tasks/FTAI-20260728-market-data-binance-spot-instrument-shadow-acceptance-v1.md
validation:
  - command: GitHub workflow 30458935489 job 90599644500
    result: PASS
    evidence: Every step completed success on freqtrade-synology-staging, including v2 preflight, full 97-slot proof and cleanup.
  - command: terminal proof marker inspection
    result: PASS
    evidence: BINANCE_SPOT_INSTRUMENT_SHADOW_ACCEPTANCE_V2_NO_NETWORK_PROOF_PASS recorded after durable cleanup.
  - command: GitHub PR 695 terminal state
    result: PASS
    evidence: Closed without merge at exact head 6687a6c77a26711eb2e364b41c14629a8dce1564.
blockers: []
next_action: Create one PR that adds exactly ai_platform/market_data/run-requests/binance-spot-instrument-shadow-acceptance-20260729-v2.json with the frozen public-only request, allow its opened-event 24-hour workflow to execute once on freqtrade-synology-staging, then close the trigger PR without merge and update this checkpoint from the terminal evidence without enabling production.
```
