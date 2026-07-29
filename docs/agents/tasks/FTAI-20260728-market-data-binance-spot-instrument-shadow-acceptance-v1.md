---
task_id: FTAI-20260728-market-data-binance-spot-instrument-shadow-acceptance-v1
status: running
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
  - current steps of job 90590650458
optional_reads:
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE_EXECUTION.md
---

# Binance Spot instrument shadow acceptance v1

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-29T15:31:00+02:00
head: 918f708bf0de300ffcd3c22fd207dad263e8c981
branch: run/binance-spot-instrument-shadow-acceptance-20260728-v1
pr: "#687"
status: running
context_routes:
  - Binance Spot public instrument-catalog acceptance
  - Synology self-hosted staging runner
  - credential-free deterministic evidence
owned_paths:
  - ai_platform/market_data/binance-spot-instrument-shadow-acceptance-policy-v1.json
  - ai_platform/market_data/binance_spot_instrument_acceptance.py
  - .github/workflows/ai-platform-binance-spot-instrument-shadow-acceptance.yml
  - ai_platform/market_data/run-requests/binance-spot-instrument-shadow-acceptance-20260728-v1.json
  - tests/ai_platform_integration/test_market_data_binance_spot_instrument_acceptance.py
  - docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SHADOW_ACCEPTANCE.md
  - docs/agents/tasks/FTAI-20260728-market-data-binance-spot-instrument-shadow-acceptance-v1.md
proven:
  - Implementation PR 633 merged as aeb858ebe5266742c257aa7b45b5cffd11c4b5ba after exact-head AI Platform CI, full Freqtrade CI and zizmor success.
  - The merged package defines 97 observations over 24 hours at 15-minute intervals using the exact reduced-payload Binance Spot URL.
  - Each observation permits one public request attempt, zero retries, no credentials, no proxy, no redirects and a 16 MiB response limit.
  - Successful samples persist raw and normalized evidence; failures persist bounded metadata without partial raw payloads.
  - The independent evaluator returns accepted, rejected or inconclusive while source_acceptance and production_source_enabled remain false.
  - Replacement proof workflow 30455561706 job 90588120948 completed success on exact runner freqtrade-synology-staging and PR 684 was closed without merge.
  - The proof executed the exact original accepted and rejected 97-slot packages, independent evaluation, tamper rejection, credential and proxy refusal, and durable cleanup.
  - Terminal marker BINANCE_SPOT_INSTRUMENT_SHADOW_ACCEPTANCE_V1_NO_NETWORK_PROOF_PASS was recorded.
  - PR 687 adds exactly ai_platform/market_data/run-requests/binance-spot-instrument-shadow-acceptance-20260728-v1.json at head 918f708bf0de300ffcd3c22fd207dad263e8c981.
  - The canonical request keeps the exact public URL, 86400 seconds, 900-second interval, approved host and durable URI, reviewed smoke evidence, zero orders and production disabled.
  - Opened-event workflow 30456309522 job 90590650458 started on freqtrade-synology-staging.
derived:
  - The single authorized real Binance acceptance attempt is now active and must not be synchronized, reopened, rerun or automatically retried.
  - PR 687 must remain unmerged and be closed only after the workflow becomes terminal.
unknown:
  - Terminal outcome and evidence of workflow 30456309522.
conflicts: []
first_failure:
  marker: none
  evidence: Job 90590650458 entered in_progress on the exact approved runner; no terminal failure is recorded.
rejected_hypotheses:
  - Modify the request PR while the opened-event workflow is active.
  - Rerun or replace the workflow before a terminal outcome exists.
  - Treat an in-progress window as accepted source evidence.
changed_paths:
  - ai_platform/market_data/run-requests/binance-spot-instrument-shadow-acceptance-20260728-v1.json
  - docs/agents/tasks/FTAI-20260728-market-data-binance-spot-instrument-shadow-acceptance-v1.md
validation:
  - command: GitHub compare develop...run/binance-spot-instrument-shadow-acceptance-20260728-v1
    result: PASS
    evidence: One commit and exactly one added canonical request file; no implementation, workflow or documentation changed in PR 687.
  - command: GitHub workflow 30456309522 job 90590650458
    result: RUNNING
    evidence: Exact opened-event acceptance job started on freqtrade-synology-staging.
blockers: []
next_action: When workflow 30456309522 becomes terminal, verify only job 90590650458, bounded artifact metadata and the durable terminal report; close PR 687 without merge, update this checkpoint with accepted, rejected or inconclusive evidence, and do not authorize production enablement.
```
