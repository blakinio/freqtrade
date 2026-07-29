---
task_id: FTAI-20260728-market-data-binance-spot-instrument-shadow-acceptance-v1
status: validating
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
  - current status of PR 684 and its proof workflow
  - terminal status of PR 639 workflow 30366399985
optional_reads:
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE_EXECUTION.md
---

# Binance Spot instrument shadow acceptance v1

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-29T15:22:00+02:00
head: 38cd0c98ddc7055af50648ae716e2e7230458cd7
branch: ci/prove-binance-spot-instrument-shadow-acceptance-v2
pr: "#684"
status: validating
context_routes:
  - Binance Spot public instrument-catalog acceptance
  - Synology self-hosted staging runner
  - credential-free deterministic evidence
owned_paths:
  - ai_platform/market_data/binance-spot-instrument-shadow-acceptance-policy-v1.json
  - ai_platform/market_data/binance_spot_instrument_acceptance.py
  - .github/workflows/ai-platform-binance-spot-instrument-shadow-acceptance.yml
  - .github/workflows/prove-binance-spot-instrument-shadow-acceptance-v2.yml
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
  - Proof workflow 30366399985 job 90298645354 started on the exact approved runner and failed before target-module import because jsonschema was absent.
  - The failed proof cleanup step succeeded and no durable Binance acceptance package was created.
  - PR 639 was closed without merge at head 4c380b8ca7b7aa64a42b378664fa34e6f329052a.
  - PR 684 changes exactly one replacement proof workflow at head 38cd0c98ddc7055af50648ae716e2e7230458cd7.
  - Replacement proof validates that V1 is exactly one workflow-only commit above merged implementation and verifies its blob identity.
  - Replacement proof installs pinned jsonschema 4.26.0, then extracts and executes the exact original 97-slot proof script with injected local openers and virtual clocks.
  - No canonical Binance 24-hour trigger request exists and no Binance acceptance observation has executed.
derived:
  - The PR 639 failure is a proof-runtime dependency gap, not a terminal acceptance implementation result, because execution stopped during package import.
  - A real Binance 24-hour trigger remains forbidden until the replacement proof completes successfully.
unknown:
  - Terminal outcome of PR 684 replacement proof workflow.
  - Outcome of any later real 24-hour Binance acceptance window.
conflicts: []
first_failure:
  marker: "ModuleNotFoundError: No module named 'jsonschema'"
  evidence: Workflow 30366399985 job 90298645354 step Prove complete acceptance package without network exited 1 during ai_platform.market_data package import.
rejected_hypotheses:
  - Retry workflow 30366399985 unchanged.
  - Reopen PR 639 as an authorized retry path.
  - Create the real 24-hour trigger before replacement proof success.
changed_paths:
  - .github/workflows/prove-binance-spot-instrument-shadow-acceptance-v2.yml
  - docs/agents/tasks/FTAI-20260728-market-data-binance-spot-instrument-shadow-acceptance-v1.md
validation:
  - command: GitHub compare develop...ci/prove-binance-spot-instrument-shadow-acceptance-v2
    result: PASS
    evidence: One commit and exactly one added workflow file; no implementation or trigger path changed.
  - command: GitHub PR 684 metadata inspection
    result: PASS
    evidence: Open PR against develop at exact head 38cd0c98ddc7055af50648ae716e2e7230458cd7 with changed_files equal to 1.
blockers:
  - Replacement proof PR 684 has not reached a terminal workflow result.
next_action: Verify only PR 684 and its proof workflow; on terminal success close PR 684 without merge and update this checkpoint before creating the separately reviewed exact-one-file Binance 24-hour trigger, otherwise record the first failure and repair the proof before any trigger.
```
