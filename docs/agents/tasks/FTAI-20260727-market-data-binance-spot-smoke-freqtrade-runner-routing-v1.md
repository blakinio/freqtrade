---
task_id: FTAI-20260727-market-data-binance-spot-smoke-freqtrade-runner-routing-v1
status: terminal-blocked
branch: docs/binance-spot-selfhosted-smoke-terminal-result-v1
base_branch: develop
created: 2026-07-27
updated: 2026-07-28
related_pr: "#595"
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

Align the bounded self-hosted Binance Spot smoke with the repository-owned Synology runner and a reproducible isolated Python runtime without changing the frozen request, endpoint, retry, evidence or source-acceptance contract, then collect one terminal request result.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-28T11:16:00+02:00
base_develop: 6c7e8dc49e6b783b5306fe95ef7c06b749a4889c
branch: docs/binance-spot-selfhosted-smoke-terminal-result-v1
trigger_pr: "#595"
status: terminal-blocked
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
  - PR 522 merged as 96d229fc9082c24b0c534685efe9ef7d1ed91699 but incorrectly retained default routing labels that the dedicated runner does not advertise.
  - The dedicated runner registers with custom label freqtrade-staging and --no-default-labels.
  - PR 571 changed routing to runs-on freqtrade-staging while retaining exact runtime name, Linux and architecture assertions, then merged by guarded squash as 59b62adad7b21d4e1c1114a118ce192eae6a7eea.
  - Temporary no-request runner proof PR 582 completed workflow 30340460065 job 90214667352 successfully and was closed without merge.
  - Trigger PR 583 reached the approved runner but failed before transport because the system Python lacked ensurepip and python3-venv; it was closed without merge and no request executed.
  - Read-only diagnostic PR 585 proved Python 3.12.3 was present while ensurepip, pip, jsonschema, python3-venv and python3-pip were absent; it was closed without merge.
  - PR 586 replaced the system-venv dependency with the repository-approved SHA-pinned astral-sh/setup-uv v8.3.0 action, isolated Python 3.12, cache disabled and jsonschema 4.26.0.
  - PR 586 exact-head AI Platform CI 30343863190, Freqtrade CI 30343866089 and zizmor 30343863186 completed success at 4bfd5de79db1ae51d07cf90d5c0380885ba8e377.
  - PR 586 merged by guarded squash as 6c7e8dc49e6b783b5306fe95ef7c06b749a4889c.
  - Temporary no-request setup-uv proof PR 592 completed workflow 30344249943 job 90226625726 successfully, verified exact runner identity, installed jsonschema 4.26.0, imported Draft202012Validator, cleaned .venv and was closed without merge.
  - Final trigger PR 595 added exactly ai_platform/market_data/run-requests/binance-spot-instrument-smoke-selfhosted-v1.json at 6a166e4811d020a4ef4c7e6bf4181db8520a6b04.
  - Final workflow 30345196797 job 90229653635 passed checkout, exact-one-file scope, approved runner identity, credential and proxy refusal, setup-uv installation and isolated runtime creation.
  - The one allowed request step executed exactly once and failed with RuntimeError response exceeds max_response_bytes.
  - The immutable success artifact step was skipped. The bounded failure upload step completed success, but the Actions artifact API returned no retrievable artifacts for run 30345196797.
  - PR 595 was closed without merge and its branch was reset to develop. No retry or rerun was performed.
  - Read-only exact-log diagnostic PR 596 recorded the first failure from existing job logs, was closed without merge and its branch was reset to develop.
  - Endpoint, one-attempt boundary, zero retries, credential and proxy refusal, redirect refusal and source_acceptance false remained unchanged throughout.
derived:
  - Custom-only runner routing and the isolated setup-uv runtime are proven operational and are no longer blockers.
  - The approved runner reached the frozen Binance endpoint and received a response larger than the frozen 16 MiB maximum.
  - The response was rejected before complete persistence, normalization and instrument counting, so parseability and normalized catalog contents remain unproven.
  - The bounded smoke completed fail-closed exactly as designed and does not authorize a collector or source acceptance.
unknown:
  - The exact response size beyond the proven greater-than-16-MiB boundary.
  - Whether the complete response would satisfy the frozen schema and normalization rules under a separately reviewed larger limit.
  - The normalized Binance Spot instrument count for this endpoint response.
conflicts: []
first_failure:
  marker: RESPONSE_EXCEEDS_MAX_RESPONSE_BYTES
  evidence: Workflow 30345196797 job 90229653635 executed the single request once and raised RuntimeError response exceeds max_response_bytes; no retry occurred.
rejected_hypotheses:
  - Treat the earlier routing or Python runtime defects as the terminal Binance transport result.
  - Raise max_response_bytes inside the trigger PR or after observing the response.
  - Retry the request automatically or rerun workflow 30345196797.
  - Use an alternate endpoint, proxy, VPN, credential, WebSocket or another runner region.
  - Treat endpoint reachability as source acceptance or production authorization.
  - Merge any trigger, proof or temporary diagnostic PR.
changed_paths:
  - docs/agents/tasks/FTAI-20260727-market-data-binance-spot-smoke-freqtrade-runner-routing-v1.md
validation:
  - command: PR 586 exact-head repository CI
    result: PASS
    evidence: AI Platform CI 30343863190, Freqtrade CI 30343866089 and zizmor 30343863186 completed success at 4bfd5de79db1ae51d07cf90d5c0380885ba8e377.
  - command: setup-uv no-request proof
    result: PASS
    evidence: Workflow 30344249943 job 90226625726 completed success on exact runner freqtrade-synology-staging and performed no exchange request.
  - command: final trigger exact-one-file and safety gates
    result: PASS
    evidence: PR 595 contained exactly one canonical request file and job 90229653635 passed all pre-transport safety gates and runtime setup.
  - command: frozen single-request smoke
    result: TERMINAL_FAIL_CLOSED
    evidence: Workflow 30345196797 job 90229653635 executed once and failed with RuntimeError response exceeds max_response_bytes.
  - command: trigger and diagnostic merge boundary
    result: PASS
    evidence: PR 595 and PR 596 are closed and unmerged; both branches were reset to develop and no retry was performed.
  - command: source acceptance
    result: FALSE
    evidence: The request and policy retained source_acceptance false and the terminal response was not normalized or accepted.
blockers:
  - The frozen 16 MiB response limit rejects the current exchangeInfo response before complete persistence and normalization.
next_action: Keep Binance Spot fail-closed and, only if the owner wants further evaluation, open a separate reviewed policy task to decide whether changing max_response_bytes is lawful and safe without retrying workflow 30345196797 or accepting the source.
```
