---
task_id: FTAI-20260727-market-data-binance-spot-smoke-freqtrade-runner-routing-v1
status: terminal-blocked
branch: fix/binance-smoke-freqtrade-runner-routing-v1
base_branch: develop
created: 2026-07-27
updated: 2026-07-28
related_pr: "#522"
owned_paths:
  - .github/workflows/ai-platform-binance-spot-instrument-smoke-selfhosted.yml
  - docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SMOKE_SELFHOSTED.md
  - tests/ai_platform_integration/test_market_data_binance_spot_instrument_smoke_selfhosted_workflow.py
  - docs/agents/tasks/FTAI-20260727-market-data-binance-spot-smoke-freqtrade-runner-routing-v1.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SMOKE_SELFHOSTED.md
  - .github/workflows/ai-platform-binance-spot-instrument-smoke-selfhosted.yml
search_first:
  - current develop and open Binance Spot smoke, Synology runner and trigger ownership
optional_reads: []
---

# Binance Spot smoke Freqtrade runner routing v1

## Goal

Align the bounded self-hosted Binance Spot smoke with the repository-owned Synology runner without changing the frozen request, endpoint, retry, evidence or source-acceptance contract, then collect one terminal trigger result.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-28T00:28:00+02:00
routing_merge: 96d229fc9082c24b0c534685efe9ef7d1ed91699
branch: fix/binance-smoke-freqtrade-runner-routing-v1
pr: "#522"
status: terminal-blocked
context_routes:
  - docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SMOKE_SELFHOSTED.md
  - .github/workflows/ai-platform-binance-spot-instrument-smoke-selfhosted.yml
owned_paths:
  - .github/workflows/ai-platform-binance-spot-instrument-smoke-selfhosted.yml
  - docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SMOKE_SELFHOSTED.md
  - tests/ai_platform_integration/test_market_data_binance_spot_instrument_smoke_selfhosted_workflow.py
  - docs/agents/tasks/FTAI-20260727-market-data-binance-spot-smoke-freqtrade-runner-routing-v1.md
proven:
  - PR 453 merged as 731132c9246a2ae09ee3a2a9c4776ad4f0e4ee6e and corrected the smoke Accept header to application/json.
  - Trigger PR 521 remained queued before its first step because the workflow requested the retired oteryn runner contract; it was closed without merge and no Binance request executed.
  - PR 522 changed only the runner label, exact runner-name assertion, matching documentation, focused tests and this checkpoint.
  - PR 522 exact-head validation passed AI Platform CI 30305966394, Freqtrade CI 30305966464 and zizmor 30305966522 at 9bd3460ed20d262179eab4c17d0fc9d64ada29d7.
  - PR 522 merged by guarded squash as 96d229fc9082c24b0c534685efe9ef7d1ed91699.
  - Fresh trigger PR 541 added exactly ai_platform/market_data/run-requests/binance-spot-instrument-smoke-selfhosted-v1.json at 6227bf06738ac9d0e5c0437a99b21c088b20e66c.
  - Trigger workflow run 30307224846 and job 90114284852 were created for runner freqtrade-synology-staging with label freqtrade-staging.
  - The trigger first waited behind Liquid20 deployment run 30306056410, which later completed cancelled after its own bounded timeout.
  - After that preceding job became terminal, the Binance smoke remained queued with no Set up job, checkout, runner validation, network transport, parsing or artifact step.
  - PR 541 was closed without merge.
  - Temporary GitHub-hosted diagnostic PR 555 ran cancellation workflow 30310422606; job 90124504305 completed success and cancelled exact run 30307224846.
  - Smoke job 90114284852 is terminal cancelled with no steps and no logs or artifacts.
  - PR 555 was closed without merge and its branch was reset to current develop.
  - No Binance request executed, no payload was collected and no raw or normalized artifact exists.
  - Endpoint, one-attempt boundary, zero retries, credential and proxy refusal and source_acceptance false remained unchanged.
derived:
  - Corrected repository routing is merged and statically validated.
  - The terminal result proves current runner unavailability before first step, not an HTTP, TLS, content-type, parser or schema result from Binance.
  - Binance Spot endpoint reachability and parseability from the approved runner remain unknown.
unknown:
  - Why freqtrade-synology-staging did not accept a new job after the preceding Liquid20 job timed out.
  - Current live runner process, registration and idle health after run 30306056410.
  - Binance endpoint transport and instrument-catalog result from the approved runner.
conflicts: []
first_failure:
  marker: FREQTRADE_SYNOLOGY_RUNNER_UNAVAILABLE_BEFORE_FIRST_STEP
  evidence: Run 30307224846 remained queued without any step after the preceding self-hosted deployment became terminal; exact cancellation was later accepted by workflow 30310422606.
rejected_hypotheses:
  - Treat queued or cancelled-before-step state as a Binance HTTP, TLS, content-type, parser or schema failure.
  - Re-run the closed workflow or create an automatic retry.
  - Change endpoint, runner identity, region, proxy, VPN, credential or request semantics.
  - Merge either trigger PR 541 or diagnostic PR 555.
changed_paths:
  - .github/workflows/ai-platform-binance-spot-instrument-smoke-selfhosted.yml
  - docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SMOKE_SELFHOSTED.md
  - tests/ai_platform_integration/test_market_data_binance_spot_instrument_smoke_selfhosted_workflow.py
  - docs/agents/tasks/FTAI-20260727-market-data-binance-spot-smoke-freqtrade-runner-routing-v1.md
validation:
  - command: PR 522 exact-head repository CI
    result: PASS
    evidence: AI Platform CI 30305966394, Freqtrade CI 30305966464 and zizmor 30305966522 succeeded before guarded merge 96d229fc9082c24b0c534685efe9ef7d1ed91699.
  - command: trigger PR 541 exact-one-file scope
    result: PASS
    evidence: Comparison against routing merge 96d229fc9082c24b0c534685efe9ef7d1ed91699 showed exactly one added canonical request file.
  - command: self-hosted trigger run 30307224846
    result: CANCELLED_BEFORE_FIRST_STEP
    evidence: Job 90114284852 completed cancelled with no steps after exact cancellation workflow 30310422606 succeeded.
  - command: trigger and diagnostic merge boundary
    result: PASS
    evidence: PR 541 and PR 555 are closed and unmerged; the temporary diagnostic branch was reset to develop.
blockers:
  - The approved freqtrade-synology-staging runner did not accept the bounded smoke job after the preceding self-hosted deployment timed out.
next_action: Restore and independently prove idle registration and job acceptance for the exact freqtrade-synology-staging runner, then create one new exact-one-file Binance smoke trigger without re-running 30307224846 or changing the frozen endpoint, routing, credential, retry or source_acceptance boundary.
```
