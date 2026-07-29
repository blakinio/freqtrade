---
task_id: FTAI-20260728-market-data-binance-spot-instrument-shadow-acceptance-v1
status: blocked
branch: run/binance-spot-instrument-shadow-acceptance-20260728-v1
base_branch: develop
created: 2026-07-28
updated: 2026-07-29
related_pr: "#687"
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
  - current status of PR 687 and workflow 30456309522
  - current production workflow dependency setup and canonical trigger identity
optional_reads:
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE_EXECUTION.md
---

# Binance Spot instrument shadow acceptance v1

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-29T15:34:00+02:00
head: 918f708bf0de300ffcd3c22fd207dad263e8c981
branch: run/binance-spot-instrument-shadow-acceptance-20260728-v1
pr: "#687"
status: blocked
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
  - Replacement no-network proof workflow 30455561706 job 90588120948 completed success on exact runner freqtrade-synology-staging and PR 684 was closed without merge.
  - The proof executed accepted and rejected 97-slot packages, independent evaluation, tamper rejection, credential and proxy refusal, and durable cleanup.
  - PR 687 added exactly the canonical v1 request at head 918f708bf0de300ffcd3c22fd207dad263e8c981.
  - Workflow 30456309522 job 90590650458 validated exact-one-file scope, staging identity, durable storage, and credential and proxy refusal.
  - The workflow failed in Validate frozen package without network before the first Binance request because jsonschema was absent from the isolated runtime.
  - The 24-hour runner, independent evaluator and artifact upload steps were skipped; no Binance acceptance observation executed and no acceptance package was produced.
  - Cleanup completed successfully and PR 687 was closed without merge.
  - The used v1 request and run identities must not be reused, reopened, synchronized or rerun.
derived:
  - The terminal result is a workflow preflight failure, not accepted, rejected or inconclusive source-quality evidence.
  - A new acceptance attempt requires a separately reviewed workflow repair and a new canonical request identity and path.
unknown:
  - Outcome of any later repaired Binance 24-hour acceptance window.
conflicts: []
first_failure:
  marker: "ModuleNotFoundError: No module named 'jsonschema'"
  evidence: Workflow 30456309522 job 90590650458 failed during ai_platform.market_data package import in the no-network preflight; network execution was skipped.
rejected_hypotheses:
  - Reopen, synchronize or rerun PR 687 or workflow 30456309522.
  - Reuse request_id binance-spot-instrument-shadow-acceptance-20260728-v1 or run_id binance-spot-instrument-shadow-acceptance-20260728-r1.
  - Create another trigger before repairing and proving the production workflow runtime.
  - Interpret the preflight failure as a source rejection or production decision.
changed_paths:
  - ai_platform/market_data/run-requests/binance-spot-instrument-shadow-acceptance-20260728-v1.json
  - docs/agents/tasks/FTAI-20260728-market-data-binance-spot-instrument-shadow-acceptance-v1.md
validation:
  - command: GitHub workflow 30456309522 job 90590650458
    result: FAIL_PRE_NETWORK
    evidence: Scope, runner, durable-storage and credential gates passed; no-network import failed and all network/evidence steps were skipped.
  - command: GitHub PR 687 terminal state
    result: PASS
    evidence: Closed without merge at exact head 918f708bf0de300ffcd3c22fd207dad263e8c981.
blockers:
  - Production acceptance workflow does not install its required jsonschema dependency before package import.
  - The v1 request identity and opened-event attempt are consumed.
next_action: Prepare and merge a separately reviewed production-workflow repair that installs pinned jsonschema in the isolated runtime and introduces a new v2 canonical request identity and path; prove the exact merged repair without network on freqtrade-synology-staging before creating any new 24-hour trigger.
```
