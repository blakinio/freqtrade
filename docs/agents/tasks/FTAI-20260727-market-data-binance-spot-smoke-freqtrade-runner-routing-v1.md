---
task_id: FTAI-20260727-market-data-binance-spot-smoke-freqtrade-runner-routing-v1
status: validating
branch: fix/binance-smoke-custom-only-runner-label-v1
base_branch: develop
created: 2026-07-27
updated: 2026-07-28
related_pr: "#571"
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
  - deploy/synology/freqtrade-runner/entrypoint.sh
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
updated_at: 2026-07-28T09:30:00+02:00
base_develop: 9ceb684a5114faac44c45081e45d0627f85d9512
branch: fix/binance-smoke-custom-only-runner-label-v1
pr: "#571"
status: validating
context_routes:
  - docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SMOKE_SELFHOSTED.md
  - .github/workflows/ai-platform-binance-spot-instrument-smoke-selfhosted.yml
  - deploy/synology/freqtrade-runner/entrypoint.sh
owned_paths:
  - .github/workflows/ai-platform-binance-spot-instrument-smoke-selfhosted.yml
  - docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SMOKE_SELFHOSTED.md
  - tests/ai_platform_integration/test_market_data_binance_spot_instrument_smoke_selfhosted_workflow.py
  - docs/agents/tasks/FTAI-20260727-market-data-binance-spot-smoke-freqtrade-runner-routing-v1.md
proven:
  - PR 453 merged as 731132c9246a2ae09ee3a2a9c4776ad4f0e4ee6e and corrected the smoke Accept header to application/json.
  - PR 522 merged as 96d229fc9082c24b0c534685efe9ef7d1ed91699 and changed the retired OteryN label to freqtrade-staging, but retained default routing labels self-hosted and Linux.
  - Trigger PR 541 added exactly the canonical request, remained queued before every step, was closed without merge and was cancelled exactly; no Binance request or artifact existed.
  - The dedicated runner entrypoint registers with --labels freqtrade-staging and --no-default-labels.
  - Therefore the registered runner intentionally advertises the custom label freqtrade-staging without default routing labels self-hosted, Linux or X64.
  - Liquid20 push run 30336184269, job 90201466756, completed success on the same runner through runs-on freqtrade-staging after the earlier Binance blocker.
  - Temporary proof PR 562 repeated the mismatched default labels, remained queued and was closed without merge.
  - GitHub-hosted cancellation workflow 30337135171, job 90204373964, completed success and cancelled exact proof run 30336513807; target job 90202464975 is cancelled with no steps.
  - Read-only metadata PR 567 received HTTP 403 from the runner-list endpoint and was closed without merge; it performed no Synology mutation.
  - PR 571 routes only by runs-on freqtrade-staging while retaining fail-closed assertions for exact runner name, Linux and X64 or ARM64 before transport.
  - Endpoint, one-attempt boundary, zero retries, credential and proxy refusal, evidence handling and source_acceptance false remain unchanged.
  - Exact-head validation at 86b6b6a21febc596bc042035d1edba4a04b95ab1 passed AI Platform CI 30337467577, Freqtrade CI 30337468321 and zizmor 30337467688.
  - Develop advanced by one disjoint liquidation checkpoint commit only; the identical four-path repair was recreated on develop 9ceb684a5114faac44c45081e45d0627f85d9512.
derived:
  - The prior queued results were caused by an impossible label conjunction, not by runner downtime or a Binance HTTP, TLS, content-type, parser or schema result.
  - Custom-label routing plus exact runtime identity assertions is the repository-consistent contract for this dedicated runner.
unknown:
  - Final fresh exact-head CI and review result after the disjoint develop reconciliation.
  - Terminal result of a corrected idle job-acceptance proof routed only by freqtrade-staging.
  - Binance endpoint transport and instrument-catalog result from the approved runner.
conflicts: []
first_failure:
  marker: CUSTOM_ONLY_RUNNER_LABEL_MISMATCH
  evidence: The runner is registered with --no-default-labels, while runs 30307224846 and 30336513807 required self-hosted and Linux in addition to freqtrade-staging and remained queued without steps.
rejected_hypotheses:
  - Treat the queued state as runner downtime after job 90201466756 completed successfully.
  - Treat queued or cancelled-before-step state as a Binance transport or parser failure.
  - Add default labels to the live runner registration instead of matching the reviewed custom-only contract.
  - Change endpoint, region, proxy, VPN, credential, retry or request semantics.
  - Merge any trigger or temporary diagnostic PR.
changed_paths:
  - .github/workflows/ai-platform-binance-spot-instrument-smoke-selfhosted.yml
  - docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SMOKE_SELFHOSTED.md
  - tests/ai_platform_integration/test_market_data_binance_spot_instrument_smoke_selfhosted_workflow.py
  - docs/agents/tasks/FTAI-20260727-market-data-binance-spot-smoke-freqtrade-runner-routing-v1.md
validation:
  - command: dedicated runner registration contract
    result: PASS
    evidence: deploy/synology/freqtrade-runner/entrypoint.sh sets RUNNER_LABELS to freqtrade-staging and invokes config.sh with --no-default-labels.
  - command: live runner job acceptance
    result: PASS
    evidence: Liquid20 run 30336184269 job 90201466756 completed success when routed by runs-on freqtrade-staging.
  - command: mismatched proof cleanup
    result: PASS
    evidence: PR 562 and PR 569 are closed and unmerged; exact proof run 30336513807 is terminal cancelled with no steps.
  - command: prior PR 571 exact-head repository CI
    result: PASS
    evidence: AI Platform CI 30337467577, Freqtrade CI 30337468321 and zizmor 30337467688 succeeded at 86b6b6a21febc596bc042035d1edba4a04b95ab1.
  - command: fresh PR 571 exact-head repository CI
    result: PENDING
    evidence: Fresh checks must pass after rebasing the identical four paths onto develop 9ceb684a5114faac44c45081e45d0627f85d9512.
blockers:
  - Fresh exact-head CI and review are pending for PR 571 after disjoint develop reconciliation.
next_action: Complete fresh exact-head CI and guarded merge of PR 571, run one corrected idle acceptance proof routed only by freqtrade-staging and close it without merge, then create one fresh exact-one-file Binance smoke trigger, collect terminal evidence, close it without merge and record the result while keeping source_acceptance false.
```
