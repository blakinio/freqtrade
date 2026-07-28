---
task_id: FTAI-20260727-market-data-binance-spot-smoke-freqtrade-runner-routing-v1
status: validating
branch: fix/binance-smoke-setup-uv-runtime-v1
base_branch: develop
created: 2026-07-27
updated: 2026-07-28
related_pr: "#586"
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
updated_at: 2026-07-28T10:16:00+02:00
base_develop: 9ff7717cde0127c12a9cb9da576599f4bbdf6954
branch: fix/binance-smoke-setup-uv-runtime-v1
pr: "#586"
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
  - PR 522 merged as 96d229fc9082c24b0c534685efe9ef7d1ed91699 but incorrectly retained default routing labels that the dedicated runner does not advertise.
  - The dedicated runner registers with custom label freqtrade-staging and --no-default-labels.
  - PR 571 changed routing to runs-on freqtrade-staging while retaining exact runtime name, Linux and architecture assertions; exact-head AI Platform CI, Freqtrade CI and zizmor passed twice.
  - PR 571 merged by guarded squash as 59b62adad7b21d4e1c1114a118ce192eae6a7eea.
  - Temporary no-request proof PR 582 was accepted immediately by the custom-only label; workflow 30340460065 job 90214667352 completed success and verified the exact runner identity.
  - PR 582 was closed without merge and its branch was reset.
  - Fresh exact-one-file trigger PR 583 added only the canonical request at 34d58ccb451c06a2dca582debc56f59b4bd4d45e.
  - Trigger run 30340638216 job 90215215905 passed checkout, exact-one-file scope, runner identity and credential/proxy refusal.
  - Trigger run 30340638216 failed in Create isolated smoke runtime; Run frozen single-request smoke was skipped and no artifact existed.
  - PR 583 was closed without merge; no Binance request executed and no retry was performed.
  - Read-only diagnostic PR 585 reported Python 3.12.3, ensurepip false, pip false, jsonschema false, python3-venv not installed and python3-pip not installed.
  - Diagnostic run 30340916107 job 90216071384 recorded python3 -m venv exit code 1 with the exact ensurepip-unavailable instruction to install python3.12-venv.
  - PR 585 was closed without merge and its branch was reset; it performed no network or Synology mutation.
  - PR 586 reuses the repository-approved pinned astral-sh/setup-uv v8.3.0 action, activates isolated Python 3.12 with cache disabled, installs only jsonschema 4.26.0 and removes .venv in always cleanup.
  - PR 586 does not change the runner image, Docker state, endpoint, credentials, proxy refusal, retry count, evidence contract or source_acceptance false.
derived:
  - Custom-label routing is proven operational and is no longer a blocker.
  - The first corrected trigger failed solely because the minimal runner image intentionally lacks the Debian venv and pip components.
  - Reusing the same SHA-pinned setup-uv action already exercised by repository CI avoids a runner-image publication and live cutover while preserving runtime isolation.
unknown:
  - Final exact-head CI and review result for PR 586.
  - Terminal result of a no-request setup-uv runtime proof on the approved runner.
  - Binance endpoint transport and instrument-catalog result from the approved runner.
conflicts: []
first_failure:
  marker: SYSTEM_PYTHON_VENV_ENSUREPIP_UNAVAILABLE
  evidence: Trigger job 90215215905 failed before transport; diagnostic job 90216071384 proved ensurepip, pip and python3-venv were absent and python3 -m venv exited 1.
rejected_hypotheses:
  - Treat the pre-transport runtime failure as a Binance HTTP, TLS, content-type, parser or schema result.
  - Install packages globally or mutate the live runner image during the request workflow.
  - Use Docker, a proxy, VPN, alternate endpoint, credential or automatic retry.
  - Re-run closed trigger workflow 30340638216.
  - Merge any trigger or temporary diagnostic PR.
changed_paths:
  - .github/workflows/ai-platform-binance-spot-instrument-smoke-selfhosted.yml
  - docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SMOKE_SELFHOSTED.md
  - tests/ai_platform_integration/test_market_data_binance_spot_instrument_smoke_selfhosted_workflow.py
  - docs/agents/tasks/FTAI-20260727-market-data-binance-spot-smoke-freqtrade-runner-routing-v1.md
validation:
  - command: custom-label runner acceptance proof
    result: PASS
    evidence: Workflow 30340460065 job 90214667352 completed success on exact runner freqtrade-synology-staging.
  - command: trigger PR 583 exact-one-file scope and safety gates
    result: PASS
    evidence: Job 90215215905 passed checkout, exact scope, runner identity and credential/proxy refusal before the runtime failure.
  - command: trigger PR 583 transport boundary
    result: NOT_EXECUTED
    evidence: The single-request step was skipped and run 30340638216 produced no artifacts.
  - command: local Python runtime diagnostic
    result: PASS
    evidence: Workflow 30340916107 job 90216071384 captured the absent modules/packages and exact venv exit code without network access.
  - command: PR 586 exact-head repository CI
    result: PENDING
    evidence: AI Platform CI, Freqtrade CI and zizmor must pass before guarded merge.
blockers:
  - Exact-head CI and review are pending for PR 586.
next_action: Complete exact-head CI and guarded merge of PR 586, prove the setup-uv runtime without an exchange request, then create one fresh exact-one-file Binance smoke trigger, collect its terminal evidence, close it without merge and record the result while keeping source_acceptance false.
```
