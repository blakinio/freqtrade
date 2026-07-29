---
task_id: FTAI-20260728-market-data-binance-spot-instrument-shadow-acceptance-v1
status: running
branch: run/binance-spot-instrument-shadow-acceptance-20260729-v2
base_branch: develop
created: 2026-07-28
updated: 2026-07-29
related_pr: "#699"
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
  - current status of PR 699 and workflow 30459738848
  - current steps of job 90602377126
optional_reads:
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE_EXECUTION.md
---

# Binance Spot instrument shadow acceptance v1

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-29T16:14:00+02:00
head: cda800b20ec4323be21a0a5b46a91e5e5fd2fdab
branch: run/binance-spot-instrument-shadow-acceptance-20260729-v2
pr: "#699"
status: running
context_routes:
  - Binance Spot public instrument-catalog acceptance
  - Synology self-hosted staging runner
  - credential-free deterministic evidence
owned_paths:
  - .github/workflows/ai-platform-binance-spot-instrument-shadow-acceptance-v2.yml
  - tools/market_data/binance_spot_instrument_acceptance_v2_preflight.py
  - ai_platform/market_data/run-requests/binance-spot-instrument-shadow-acceptance-20260729-v2.json
  - docs/agents/tasks/FTAI-20260728-market-data-binance-spot-instrument-shadow-acceptance-v1.md
proven:
  - Original acceptance implementation remains merged as aeb858ebe5266742c257aa7b45b5cffd11c4b5ba with unchanged policy, transport, parser, thresholds, durable evidence and independent evaluator.
  - Consumed v1 trigger workflow 30456309522 failed before network because its isolated runtime lacked jsonschema; no observation or package was created and PR 687 was closed without merge.
  - Runtime v2 repair PR 690 merged as 224ee218b2e62b68c2888e27913a2c3d6c35dfc9 after exact-head AI Platform CI, full Freqtrade CI and zizmor success.
  - Exact-merged-head proof workflow 30458935489 job 90599644500 completed success on freqtrade-synology-staging and PR 695 was closed without merge.
  - The proof validated v2 runner, durable storage, pinned jsonschema 4.26.0, complete static preflight, accepted and rejected 97-slot packages, independent evaluation, tamper rejection, zero orders and production disabled.
  - Terminal marker BINANCE_SPOT_INSTRUMENT_SHADOW_ACCEPTANCE_V2_NO_NETWORK_PROOF_PASS was recorded after successful proof cleanup.
  - PR 699 adds exactly ai_platform/market_data/run-requests/binance-spot-instrument-shadow-acceptance-20260729-v2.json at head cda800b20ec4323be21a0a5b46a91e5e5fd2fdab.
  - The canonical request freezes request_id binance-spot-instrument-shadow-acceptance-20260729-v2 and run_id binance-spot-instrument-shadow-acceptance-20260729-v2-r1 with the exact public URL, 86400 seconds, 900-second interval, approved host and durable URI, zero orders and production disabled.
  - Opened-event workflow 30459738848 job 90602377126 started on exact runner freqtrade-synology-staging.
  - Exact-one-file scope, staging identity, durable storage preparation, credential and proxy refusal, isolated Python, pinned dependency and no-network package preflight all completed success.
  - The frozen 24-hour acceptance package step is in progress.
derived:
  - The single authorized real v2 acceptance attempt is active and must not be synchronized, reopened, rerun or automatically retried.
  - PR 699 must remain unmerged and be closed only after workflow 30459738848 becomes terminal.
unknown:
  - Terminal accepted, rejected or inconclusive outcome and evidence of workflow 30459738848.
conflicts: []
first_failure:
  marker: none
  evidence: Job 90602377126 is in progress in Run frozen 24-hour acceptance package after every pre-network gate completed success.
rejected_hypotheses:
  - Modify or synchronize PR 699 while its opened-event workflow is active.
  - Rerun, reopen or replace workflow 30459738848 before a terminal outcome exists.
  - Treat an in-progress window as source acceptance or production authorization.
changed_paths:
  - ai_platform/market_data/run-requests/binance-spot-instrument-shadow-acceptance-20260729-v2.json
  - docs/agents/tasks/FTAI-20260728-market-data-binance-spot-instrument-shadow-acceptance-v1.md
validation:
  - command: GitHub compare develop...run/binance-spot-instrument-shadow-acceptance-20260729-v2
    result: PASS
    evidence: One commit and exactly one added canonical v2 request file; no implementation, workflow or documentation changed in PR 699.
  - command: GitHub workflow 30459738848 job 90602377126
    result: RUNNING
    evidence: Exact opened-event acceptance job passed every pre-network gate and entered the frozen 24-hour package on freqtrade-synology-staging.
blockers: []
next_action: When workflow 30459738848 becomes terminal, verify only job 90602377126, bounded artifact metadata and the durable terminal report; close PR 699 without merge, update this checkpoint with accepted, rejected or inconclusive evidence, and do not authorize production enablement.
```
