---
task_id: FTAI-20260728-market-data-binance-spot-instrument-shadow-acceptance-v1
status: ready
branch: ci/prove-binance-spot-instrument-shadow-acceptance-v2
base_branch: develop
created: 2026-07-28
updated: 2026-07-29
related_pr: "#684"
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
  - docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SHADOW_ACCEPTANCE.md
search_first:
  - current existence of the canonical Binance acceptance request path
  - current availability of freqtrade-synology-staging
optional_reads:
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE_EXECUTION.md
---

# Binance Spot instrument shadow acceptance v1

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-29T15:27:00+02:00
head: 38cd0c98ddc7055af50648ae716e2e7230458cd7
branch: ci/prove-binance-spot-instrument-shadow-acceptance-v2
pr: "#684"
status: ready
context_routes:
  - Binance Spot public instrument-catalog acceptance
  - Synology self-hosted staging runner
  - credential-free deterministic evidence
owned_paths:
  - ai_platform/market_data/binance-spot-instrument-shadow-acceptance-policy-v1.json
  - ai_platform/market_data/binance_spot_instrument_acceptance.py
  - .github/workflows/ai-platform-binance-spot-instrument-shadow-acceptance.yml
  - tests/ai_platform_integration/test_market_data_binance_spot_instrument_acceptance.py
  - docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SHADOW_ACCEPTANCE.md
  - docs/agents/tasks/FTAI-20260728-market-data-binance-spot-instrument-shadow-acceptance-v1.md
proven:
  - Implementation PR 633 merged as aeb858ebe5266742c257aa7b45b5cffd11c4b5ba after exact-head AI Platform CI, full Freqtrade CI and zizmor success.
  - The merged package defines 97 observations over 24 hours at 15-minute intervals using the exact reduced-payload Binance Spot URL.
  - Each observation permits one public request attempt, zero retries, no credentials, no proxy, no redirects and a 16 MiB response limit.
  - Successful samples persist raw and normalized evidence; failures persist bounded metadata without partial raw payloads.
  - The independent evaluator returns accepted, rejected or inconclusive while source_acceptance and production_source_enabled remain false.
  - OKX workflow 30358400049 job 90271896559 completed success and released freqtrade-synology-staging.
  - Initial proof workflow 30366399985 failed before target-module import only because jsonschema was absent; PR 639 was closed without merge.
  - Replacement proof PR 684 changed exactly one workflow and was closed without merge at head 38cd0c98ddc7055af50648ae716e2e7230458cd7.
  - Replacement workflow 30455561706 job 90588120948 completed success on exact runner freqtrade-synology-staging.
  - The replacement validated the exact merged implementation relation, original proof blob identity, credential and proxy refusal, and pinned jsonschema 4.26.0.
  - The exact original proof script completed all accepted and rejected 97-slot packages, independent evaluation, tamper rejection and zero-order boundaries.
  - Terminal marker BINANCE_SPOT_INSTRUMENT_SHADOW_ACCEPTANCE_V1_NO_NETWORK_PROOF_PASS was recorded.
  - Cleanup completed successfully and no durable Binance acceptance package was left by proof execution.
  - No canonical Binance 24-hour trigger request exists and no Binance acceptance observation has executed.
derived:
  - The merged acceptance package is ready for one separately reviewed canonical 24-hour trigger on the approved staging runner.
  - The trigger must add exactly the frozen request path and must be closed without merge after its one opened-event execution.
unknown:
  - Outcome of the real 24-hour Binance acceptance window.
conflicts: []
first_failure:
  marker: none
  evidence: Replacement proof workflow 30455561706 completed success with the frozen terminal marker and cleanup success.
rejected_hypotheses:
  - Reuse or reopen either closed proof PR as a trigger.
  - Add implementation, workflow or documentation changes to the canonical trigger PR.
  - Treat proof success as source acceptance or production enablement.
changed_paths:
  - docs/agents/tasks/FTAI-20260728-market-data-binance-spot-instrument-shadow-acceptance-v1.md
validation:
  - command: GitHub workflow 30455561706 job 90588120948
    result: PASS
    evidence: Every step completed success on freqtrade-synology-staging, including exact V1 proof execution and durable cleanup.
  - command: terminal proof marker inspection
    result: PASS
    evidence: BINANCE_SPOT_INSTRUMENT_SHADOW_ACCEPTANCE_V1_NO_NETWORK_PROOF_PASS recorded before cleanup.
blockers: []
next_action: Create one PR that adds exactly ai_platform/market_data/run-requests/binance-spot-instrument-shadow-acceptance-20260728-v1.json with the frozen public-only request, allow its opened-event 24-hour workflow to execute once on freqtrade-synology-staging, then close the trigger PR without merge and update this checkpoint from the terminal evidence.
```
