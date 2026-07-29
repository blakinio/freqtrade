---
task_id: FTAI-20260728-market-data-binance-spot-instrument-shadow-acceptance-v1
status: validating
branch: fix/binance-spot-instrument-acceptance-nonblocking-v3
base_branch: develop
created: 2026-07-28
updated: 2026-07-29
related_pr: "#711"
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
  - docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SHADOW_ACCEPTANCE.md
  - docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SHADOW_ACCEPTANCE_V3.md
search_first:
  - current exact-head CI state of PR 711
  - absence of the blocking v2 workflow on PR 711
optional_reads:
  - docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SHADOW_ACCEPTANCE_V2.md
---

# Binance Spot instrument shadow acceptance v1

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-29T17:45:00+02:00
head: b8c6df9289708dacc2c092b5a92737f2230d647d
branch: fix/binance-spot-instrument-acceptance-nonblocking-v3
pr: "#711"
status: validating
context_routes:
  - Binance Spot public instrument-catalog acceptance
  - non-blocking Synology self-hosted sampling
  - credential-free deterministic evidence
owned_paths:
  - ai_platform/market_data/binance_spot_instrument_acceptance_incremental.py
  - .github/workflows/ai-platform-binance-spot-instrument-shadow-acceptance-v3.yml
  - tests/ai_platform_integration/test_market_data_binance_spot_instrument_acceptance_v3.py
  - docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SHADOW_ACCEPTANCE_V3.md
  - docs/agents/tasks/FTAI-20260728-market-data-binance-spot-instrument-shadow-acceptance-v1.md
proven:
  - Original acceptance implementation remains merged as aeb858ebe5266742c257aa7b45b5cffd11c4b5ba with the frozen policy, public URL, 97 observations, one attempt, zero retries, durable evidence and independent evaluator.
  - Runtime v2 workflow 30459738848 job 90602377126 passed every pre-network gate and collected five successful public observations before manual cancellation.
  - The cancelled v2 metadata artifact is 8729171100 with digest sha256:584f8051e87a1a44a6a3daf2efd77baf9ac8a54d8e992a5d3a58edfb39dc5acb.
  - V2 produced no terminal accepted, rejected or inconclusive outcome; PR 699 was closed without merge and must not be reopened or rerun.
  - PR 711 removes the 1500-minute v2 workflow and replaces it with a v3 initializer and scheduled sampler, each limited to ten minutes.
  - V3 persists self-hashed active state on Synology, uses one global workflow concurrency group and a Linux file lock, and collects at most one due observation per invocation.
  - V3 enforces at least 900 seconds between completed observations and independently evaluates only after all 97 reports exist.
  - An attempt marker converts an interrupted observation into one bounded failure without a second Binance request, preserving one attempt and zero retries.
  - The repair PR contains no canonical v3 request and performs no Binance network execution.
derived:
  - The self-hosted runner will be released after every initializer or sampler job rather than reserved for the 24-hour window.
  - A separately reviewed v3 trigger may be created only after exact-head CI, security validation, guarded merge and exact-merged-head no-network proof.
unknown:
  - Terminal exact-head AI Platform CI and Freqtrade CI outcome of PR 711.
  - Terminal outcome of a later real non-blocking v3 acceptance window.
conflicts: []
first_failure:
  marker: none
  evidence: The earlier UP035 Ruff import failure was repaired at b8c6df9289708dacc2c092b5a92737f2230d647d; current exact-head CI is pending.
rejected_hypotheses:
  - Rerun, reopen or synchronize the consumed v2 trigger or workflow.
  - Restore a sleep loop or any job timeout capable of reserving the runner for the full acceptance window.
  - Retry an observation after a process interruption.
  - Treat the five successful partial v2 observations as a terminal acceptance decision.
changed_paths:
  - .github/workflows/ai-platform-binance-spot-instrument-shadow-acceptance-v2.yml
  - .github/workflows/ai-platform-binance-spot-instrument-shadow-acceptance-v3.yml
  - ai_platform/market_data/binance_spot_instrument_acceptance_incremental.py
  - tests/ai_platform_integration/test_market_data_binance_spot_instrument_acceptance_v2.py
  - tests/ai_platform_integration/test_market_data_binance_spot_instrument_acceptance_v3.py
  - docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SHADOW_ACCEPTANCE_V3.md
  - docs/agents/tasks/FTAI-20260728-market-data-binance-spot-instrument-shadow-acceptance-v1.md
validation:
  - command: GitHub workflow 30459738848 job 90602377126 terminal inspection
    result: CANCELLED
    evidence: Run step cancelled; metadata upload and cleanup succeeded; independent evaluator and terminal enforcement were skipped.
  - command: cancelled v2 artifact 8729171100 inspection
    result: PASS
    evidence: Exactly five successful sample reports at 900-second offsets were present; no terminal report was present.
  - command: AI Platform CI 30466865344
    result: FAIL_LINT_REPAIRED
    evidence: All 976 tests passed; sole Ruff UP035 collections import failure was corrected without behavioral changes.
  - command: GitHub compare develop...fix/binance-spot-instrument-acceptance-nonblocking-v3
    result: PASS
    evidence: Blocking v2 workflow removed; v3 workflow, incremental runtime, tests and documentation added; no trigger request included.
blockers: []
next_action: Complete exact-head AI Platform CI, full Freqtrade CI and zizmor for PR 711, resolve any review threads, and merge only when all checks pass and the blocking v2 workflow remains absent.
```
