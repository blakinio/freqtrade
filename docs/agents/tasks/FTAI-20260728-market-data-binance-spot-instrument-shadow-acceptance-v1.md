---
task_id: FTAI-20260728-market-data-binance-spot-instrument-shadow-acceptance-v1
status: blocked
branch: docs/binance-v2-cancelled-runner-architecture-checkpoint
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
  - current state of PR 699, workflow 30459738848 and job 90602377126
  - non-blocking short-lived sampling workflow design
optional_reads:
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE_EXECUTION.md
---

# Binance Spot instrument shadow acceptance v1

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-29T17:20:00+02:00
head: cda800b20ec4323be21a0a5b46a91e5e5fd2fdab
branch: docs/binance-v2-cancelled-runner-architecture-checkpoint
pr: "#699"
status: blocked
context_routes:
  - Binance Spot public instrument-catalog acceptance
  - Synology self-hosted staging runner
  - credential-free deterministic evidence
owned_paths:
  - .github/workflows/ai-platform-binance-spot-instrument-shadow-acceptance-v2.yml
  - tools/market_data/binance_spot_instrument_acceptance_v2_preflight.py
  - docs/agents/tasks/FTAI-20260728-market-data-binance-spot-instrument-shadow-acceptance-v1.md
proven:
  - Original acceptance implementation remains merged as aeb858ebe5266742c257aa7b45b5cffd11c4b5ba with unchanged policy, transport, parser, thresholds, durable evidence and independent evaluator.
  - Runtime v2 repair PR 690 merged as 224ee218b2e62b68c2888e27913a2c3d6c35dfc9 and exact-merged-head no-network proof workflow 30458935489 job 90599644500 completed success.
  - PR 699 added exactly the canonical v2 request at head cda800b20ec4323be21a0a5b46a91e5e5fd2fdab and triggered workflow 30459738848 job 90602377126 on freqtrade-synology-staging.
  - Exact-one-file scope, staging identity, durable storage, credential and proxy refusal, isolated Python, pinned jsonschema 4.26.0 and no-network package preflight completed success.
  - The workflow then held the single self-hosted staging runner inside one 24-hour process instead of releasing it between 15-minute observations.
  - Workflow 30459738848 was explicitly cancelled; job 90602377126 completed with conclusion cancelled while the 24-hour package step was active.
  - Independent package verification and terminal outcome enforcement were skipped, so the run produced no accepted, rejected or inconclusive source-quality decision.
  - Bounded artifact 8729171100 was uploaded at 4002 bytes with digest sha256:584f8051e87a1a44a6a3daf2efd77baf9ac8a54d8e992a5d3a58edfb39dc5acb.
  - Isolated runtime cleanup and checkout cleanup completed success.
  - PR 699 was closed without merge and its request, run and opened-event identities are consumed.
derived:
  - Cancellation is a technical execution termination, not a source rejection and not production acceptance.
  - The current one-job 24-hour workflow is unsuitable for a shared or single self-hosted runner because it monopolizes the runner between observations.
  - No rerun, reopen, synchronization or reuse of PR 699, workflow 30459738848, request_id binance-spot-instrument-shadow-acceptance-20260729-v2 or run_id binance-spot-instrument-shadow-acceptance-20260729-v2-r1 is authorized.
unknown:
  - Binance Spot instrument-catalog acceptance outcome under a non-blocking complete 97-observation execution.
conflicts: []
first_failure:
  marker: BINANCE_ACCEPTANCE_RUNNER_MONOPOLIZATION
  evidence: The workflow used one self-hosted job for the full 86400-second observation window; it was cancelled during the package step before independent evaluation.
rejected_hypotheses:
  - Treat cancellation as accepted, rejected or inconclusive source evidence.
  - Rerun, reopen, synchronize or reuse the consumed v2 trigger and identities.
  - Enable source_acceptance, production_source_enabled, orders or live capital.
changed_paths:
  - docs/agents/tasks/FTAI-20260728-market-data-binance-spot-instrument-shadow-acceptance-v1.md
validation:
  - command: GitHub workflow 30459738848 job 90602377126
    result: CANCELLED
    evidence: Preflight gates passed; the 24-hour package step was cancelled; independent verification and terminal enforcement were skipped; cleanup succeeded.
  - command: GitHub artifact 8729171100 metadata
    result: PASS
    evidence: Bounded 4002-byte artifact exists with recorded SHA-256 digest and no terminal acceptance report claim.
  - command: GitHub PR 699 terminal state
    result: PASS
    evidence: Closed without merge at exact consumed head cda800b20ec4323be21a0a5b46a91e5e5fd2fdab.
blockers:
  - The merged v2 workflow monopolizes freqtrade-synology-staging for the complete 24-hour window.
next_action: Replace the continuous 24-hour self-hosted job with separately reviewed short-lived idempotent observation jobs that atomically persist one scheduled sample at a time, release the runner after each sample, finalize only after 97 valid slots, use new immutable request and run identities, and require exact-merged-head no-network proof before any real trigger.
```
