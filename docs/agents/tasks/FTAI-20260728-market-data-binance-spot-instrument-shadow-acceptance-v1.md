---
task_id: FTAI-20260728-market-data-binance-spot-instrument-shadow-acceptance-v1
status: ready
branch: docs/binance-v3-no-network-proof-checkpoint
base_branch: develop
created: 2026-07-28
updated: 2026-07-29
related_pr: "#730"
owned_paths:
  - ai_platform/market_data/binance-spot-instrument-shadow-acceptance-policy-v1.json
  - ai_platform/market_data/binance_spot_instrument_acceptance.py
  - ai_platform/market_data/binance_spot_instrument_acceptance_incremental.py
  - .github/workflows/ai-platform-binance-spot-instrument-shadow-acceptance-v3.yml
  - tests/ai_platform_integration/test_market_data_binance_spot_instrument_acceptance_v3.py
  - docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SHADOW_ACCEPTANCE_V3.md
  - docs/agents/tasks/FTAI-20260728-market-data-binance-spot-instrument-shadow-acceptance-v1.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SHADOW_ACCEPTANCE_V3.md
search_first:
  - current state of PR 730, workflow 30481244949 and job 90675586189
  - canonical v3 trigger request path and frozen request/run identities
optional_reads:
  - docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SHADOW_ACCEPTANCE_V2.md
---

# Binance Spot instrument shadow acceptance v1

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-29T20:51:00+02:00
head: 1675e66dbff382720f9717c43c650f270da88029
branch: docs/binance-v3-no-network-proof-checkpoint
pr: none
status: ready
context_routes:
  - Binance Spot public instrument-catalog acceptance
  - Synology self-hosted staging runner
  - credential-free deterministic evidence
owned_paths:
  - ai_platform/market_data/binance-spot-instrument-shadow-acceptance-policy-v1.json
  - ai_platform/market_data/binance_spot_instrument_acceptance.py
  - ai_platform/market_data/binance_spot_instrument_acceptance_incremental.py
  - .github/workflows/ai-platform-binance-spot-instrument-shadow-acceptance-v3.yml
  - tests/ai_platform_integration/test_market_data_binance_spot_instrument_acceptance_v3.py
  - docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SHADOW_ACCEPTANCE_V3.md
  - docs/agents/tasks/FTAI-20260728-market-data-binance-spot-instrument-shadow-acceptance-v1.md
proven:
  - Runtime v3 repair PR 711 merged as 3d3c5d2c5806e2d23c86d2fc53cb01322d85a147.
  - The blocking v2 workflow is removed; v3 uses a five-minute due check, ten-minute initializer, five-minute sampler and at most one observation per sampler job.
  - Runtime v3 preserves 97 observations, at least 900 seconds between completed observations, one attempt, zero retries, durable Synology evidence and independent final evaluation.
  - Exact-one-workflow proof PR 730 used head 1675e66dbff382720f9717c43c650f270da88029 and executed merged runtime commit 3d3c5d2c5806e2d23c86d2fc53cb01322d85a147.
  - Proof workflow 30481244949 job 90675586189 completed success on freqtrade-synology-staging.
  - The proof executed 97 accepted local-opener observations with a virtual clock, verified immediate not_due behavior, independent evaluation and tamper rejection without a Binance request.
  - The proof verified interrupted-attempt recovery as one bounded failure with zero retry and verified parallel initialization fails closed.
  - Proof cleanup removed its temporary durable root and confirmed no active v3 pointer remained.
  - PR 730 was closed without merge after terminal proof evidence.
  - Consumed v2 PR 699, workflow 30459738848 and v2 request/run identities remain forbidden from rerun or reuse.
derived:
  - Runtime v3 is ready for one separately reviewed canonical real trigger.
  - The no-network proof validates runtime behavior only and is not Binance source acceptance or production enablement.
unknown:
  - Binance Spot instrument-catalog acceptance outcome from the complete real v3 97-observation window.
conflicts: []
first_failure:
  marker: BINANCE_ACCEPTANCE_RUNNER_MONOPOLIZATION
  evidence: Runtime v2 held the single self-hosted runner inside one 24-hour job and was cancelled before terminal evaluation; runtime v3 removes that architecture.
rejected_hypotheses:
  - Treat the v3 no-network proof as real source acceptance.
  - Rerun, reopen or reuse consumed v2 trigger identities.
  - Merge the temporary proof workflow into develop.
  - Enable source_acceptance, production_source_enabled, orders or live capital.
changed_paths:
  - ai_platform/market_data/binance_spot_instrument_acceptance_incremental.py
  - .github/workflows/ai-platform-binance-spot-instrument-shadow-acceptance-v3.yml
  - tests/ai_platform_integration/test_market_data_binance_spot_instrument_acceptance_v3.py
  - docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SHADOW_ACCEPTANCE_V3.md
  - docs/agents/tasks/FTAI-20260728-market-data-binance-spot-instrument-shadow-acceptance-v1.md
validation:
  - command: GitHub PR 711 terminal state
    result: PASS
    evidence: Merged to develop as 3d3c5d2c5806e2d23c86d2fc53cb01322d85a147 after exact-head CI and security checks.
  - command: GitHub workflow 30481244949 job 90675586189
    result: PASS
    evidence: Exact merged v3 runtime proof completed success on freqtrade-synology-staging with all proof and cleanup steps successful.
  - command: BINANCE_SPOT_INSTRUMENT_SHADOW_ACCEPTANCE_V3_NO_NETWORK_PROOF_PASS
    result: PASS
    evidence: Full 97-step local-opener proof, final evaluation, tamper refusal, interrupted-attempt no-retry and parallel-init refusal passed.
  - command: GitHub PR 730 terminal state
    result: PASS
    evidence: Closed without merge at exact proof head 1675e66dbff382720f9717c43c650f270da88029.
  - command: python tools/agents/checkpoint.py docs/agents/tasks/FTAI-20260728-market-data-binance-spot-instrument-shadow-acceptance-v1.md --require-checkpoint
    result: PASS
    evidence: Compact checkpoint contract validates successfully.
blockers: []
next_action: Create a separately reviewed exact-one-file PR from current develop adding ai_platform/market_data/run-requests/binance-spot-instrument-shadow-acceptance-20260729-v3.json with the frozen v3 identities, verify the short initializer succeeds, close the trigger without merge, and then observe scheduled short sampler jobs through terminal evaluation without rerun or retry.
```
