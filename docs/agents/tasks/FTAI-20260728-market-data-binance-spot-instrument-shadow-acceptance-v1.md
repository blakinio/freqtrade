---
task_id: FTAI-20260728-market-data-binance-spot-instrument-shadow-acceptance-v1
status: blocked
branch: ci/prove-binance-spot-instrument-shadow-acceptance-v1
base_branch: develop
created: 2026-07-28
updated: 2026-07-28
related_pr: "#639"
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
  - current status of PR 639 and workflow 30366399985
  - current status of OKX workflow 30358400049
optional_reads:
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE_EXECUTION.md
---

# Binance Spot instrument shadow acceptance v1

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-28T19:57:00+02:00
head: 4c380b8ca7b7aa64a42b378664fa34e6f329052a
branch: ci/prove-binance-spot-instrument-shadow-acceptance-v1
pr: "#639"
status: blocked
context_routes:
  - Binance Spot public instrument-catalog acceptance
  - Synology self-hosted staging runner
  - credential-free deterministic evidence
owned_paths:
  - ai_platform/market_data/binance-spot-instrument-shadow-acceptance-policy-v1.json
  - ai_platform/market_data/binance_spot_instrument_acceptance.py
  - .github/workflows/ai-platform-binance-spot-instrument-shadow-acceptance.yml
  - .github/workflows/prove-binance-spot-instrument-shadow-acceptance-v1.yml
  - tests/ai_platform_integration/test_market_data_binance_spot_instrument_acceptance.py
  - docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SHADOW_ACCEPTANCE.md
  - docs/agents/tasks/FTAI-20260728-market-data-binance-spot-instrument-shadow-acceptance-v1.md
proven:
  - Implementation PR 633 merged as aeb858ebe5266742c257aa7b45b5cffd11c4b5ba after exact-head AI Platform CI, full Freqtrade CI and zizmor success.
  - The merged package defines 97 observations over 24 hours at 15-minute intervals using the exact reduced-payload Binance Spot URL.
  - Each observation permits one public request attempt, zero retries, no credentials, no proxy, no redirects and a 16 MiB response limit.
  - Successful samples persist raw and normalized evidence; failures persist bounded metadata without partial raw payloads.
  - The independent evaluator returns accepted, rejected or inconclusive while source_acceptance and production_source_enabled remain false.
  - Proof PR 639 changes exactly one no-network workflow and targets exact merged implementation commit aeb858ebe5266742c257aa7b45b5cffd11c4b5ba.
  - Proof workflow 30366399985 job 90298645354 is queued on freqtrade-staging; its Freqtrade CI and zizmor checks passed.
  - OKX workflow 30358400049 job 90271896559 is in progress on the only dedicated staging runner and has not been cancelled or modified.
  - No canonical Binance 24-hour trigger request exists and no Binance acceptance observation has executed.
derived:
  - The queued Binance proof cannot start until the governed OKX workflow becomes terminal and releases freqtrade-synology-staging.
  - Creating the real 24-hour Binance trigger before proof completion would violate the frozen task sequence.
unknown:
  - Terminal time and outcome of OKX workflow 30358400049.
  - Terminal outcome of Binance proof workflow 30366399985.
  - Outcome of any later real 24-hour Binance acceptance window.
conflicts: []
first_failure:
  marker: none
  evidence: No terminal failure is recorded; proof job 90298645354 has not started.
rejected_hypotheses:
  - Cancel or reprioritize the governed OKX run to free the runner.
  - Use a GitHub-hosted or alternate self-hosted runner for the Binance proof.
  - Treat the successful one-shot smoke as production source acceptance.
changed_paths:
  - .github/workflows/prove-binance-spot-instrument-shadow-acceptance-v1.yml
  - docs/agents/tasks/FTAI-20260728-market-data-binance-spot-instrument-shadow-acceptance-v1.md
validation:
  - command: python tools/agents/checkpoint.py docs/agents/tasks/FTAI-20260728-market-data-binance-spot-instrument-shadow-acceptance-v1.md --require-checkpoint
    result: PASS
    evidence: Exact command executed by compact-handover validation workflow against this checkpoint revision.
  - command: python tools/agents/resume.py --task docs/agents/tasks/FTAI-20260728-market-data-binance-spot-instrument-shadow-acceptance-v1.md
    result: PASS
    evidence: Exact command executed after checkpoint validation; its stdout is the handover output.
blockers:
  - The single approved runner is occupied by governed OKX workflow 30358400049.
next_action: When OKX workflow 30358400049 is terminal, verify only its terminal state and proof workflow 30366399985; allow queued proof PR 639 to run, then close it without merge and update this checkpoint from the terminal proof result before considering any real Binance 24-hour trigger.
```
