---
task_id: FTAI-20260727-market-data-binance-spot-instrument-smoke-selfhosted-v1
status: ready
branch: feat/market-data-binance-spot-selfhosted-smoke-v1
base_branch: develop
created: 2026-07-27
updated: 2026-07-27
related_pr: "#439"
owned_paths:
  - .github/workflows/ai-platform-binance-spot-instrument-smoke-selfhosted.yml
  - docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SMOKE_SELFHOSTED.md
  - tests/ai_platform_integration/test_market_data_binance_spot_instrument_smoke_selfhosted_workflow.py
  - docs/agents/tasks/FTAI-20260727-market-data-binance-spot-instrument-smoke-selfhosted-v1.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/market_data/ARCHITECTURE.md
  - docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SMOKE.md
  - docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SMOKE_SELFHOSTED.md
  - docs/agents/tasks/FTAI-20260726-market-data-binance-spot-instrument-smoke-v1.md
search_first:
  - current develop HEAD and open market-data, runner and smoke PR ownership
  - existing exact-one-file self-hosted runner workflows and protected environments
optional_reads: []
---

# Binance Spot instrument smoke on approved self-hosted runner v1

## Goal

Add a separate exact-one-file workflow for one unchanged, credential-free Binance Spot instrument-catalog request on the established owner-managed Synology staging runner. Keep the endpoint, policy, one-attempt boundary, evidence format and `source_acceptance = false` unchanged.

## Boundaries

- No alternate Binance endpoint, proxy, VPN workflow or runner-region hopping.
- No exchange credentials, account endpoints, orders, WebSockets or broad capture.
- No global package installation, Docker mutation or persistent runner reconfiguration.
- No automatic retry after any terminal transport or parser result.
- The future trigger PR is closed without merge after evidence capture.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-27T11:50:00+02:00
head: d6adc30e5bfd1c13771b84ffccf98e19727de11a
base_develop: dc15a94388f33c81608acf566b066c845cac7b0f
branch: feat/market-data-binance-spot-selfhosted-smoke-v1
pr: "#439"
status: ready
context_routes:
  - docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SMOKE.md
  - docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SMOKE_SELFHOSTED.md
  - .github/workflows/ai-platform-binance-spot-instrument-smoke-selfhosted.yml
owned_paths:
  - .github/workflows/ai-platform-binance-spot-instrument-smoke-selfhosted.yml
  - docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SMOKE_SELFHOSTED.md
  - tests/ai_platform_integration/test_market_data_binance_spot_instrument_smoke_selfhosted_workflow.py
  - docs/agents/tasks/FTAI-20260727-market-data-binance-spot-instrument-smoke-selfhosted-v1.md
proven:
  - The predecessor smoke infrastructure is merged and its runtime dependency defect is repaired.
  - GitHub-hosted smoke run 30247410490 reached the frozen endpoint and received HTTP 451 with one attempt and zero retries.
  - The repository owner explicitly approved continuing autonomously with an approved compliant runner on 2026-07-27.
  - The established technical boundary is runner oteryn-synology-staging with labels self-hosted/Linux/oteryn-staging and protected environment synology-staging.
  - The workflow reuses the existing smoke module, policy and endpoint; refuses recognized trading credentials and proxy variables; and has no hosted-runner or alternate-endpoint fallback.
  - The runtime uses a temporary venv with repository-pinned jsonschema 4.26.0 and removes it unconditionally.
  - PR 439 contains exactly the four declared infrastructure, documentation, test and checkpoint paths.
  - Prior exact-head AI Platform CI, zizmor and full Freqtrade CI including CI Gate passed on head 43bcd84dcedbdd05f2b2732933025574ec730c50.
  - Develop later advanced through disjoint OKX staging, PI-06 Authentik preflight and inert RL-v2 provenance paths.
  - The same workflow, documentation and focused test were recreated byte-for-byte on current develop dc15a94388f33c81608acf566b066c845cac7b0f.
  - Reconciled head d6adc30e5bfd1c13771b84ffccf98e19727de11a passed AI Platform CI 30255198155, zizmor 30255198970, Freqtrade pre-commit and documentation before this ready-checkpoint-only update.
  - The only review threads reference a deleted temporary Ruff workflow and are resolved and outdated.
derived:
  - A separate owner-managed network path can test the unchanged endpoint without bypassing the prior HTTP 451 through an alternate endpoint or proxy.
  - Protected environment scheduling and exact runner identity are the technical authorization boundary; they are not a general legal determination.
  - Current-develop reconciliation changes no endpoint, credential, retry, runner, evidence or source-acceptance behavior.
unknown:
  - Final exact-head repository CI result after this ready-checkpoint-only update.
  - Whether oteryn-synology-staging is online and has Python venv support at execution time.
  - Whether the unchanged Binance endpoint is reachable and parseable from that runner.
  - Exact current instrument counts and payload hashes until a separate trigger executes.
conflicts: []
first_failure:
  marker: stale-branch-history
  evidence: Develop advanced through disjoint merged paths and GitHub reported PR 439 non-mergeable despite a previously green four-file head.
rejected_hypotheses:
  - Retry from GitHub-hosted runners.
  - Change to data-api.binance.vision or another Binance endpoint.
  - Use a proxy or VPN workflow.
  - Add credentials, account endpoints, WebSockets or retries.
  - Treat a successful smoke as source acceptance.
  - Duplicate the infrastructure in a second PR instead of reconciling PR 439.
changed_paths:
  - .github/workflows/ai-platform-binance-spot-instrument-smoke-selfhosted.yml
  - docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SMOKE_SELFHOSTED.md
  - tests/ai_platform_integration/test_market_data_binance_spot_instrument_smoke_selfhosted_workflow.py
  - docs/agents/tasks/FTAI-20260727-market-data-binance-spot-instrument-smoke-selfhosted-v1.md
validation:
  - command: prior PR 439 exact-head repository CI
    result: PASS
    evidence: AI Platform CI 30253037433, zizmor 30253037447 and Freqtrade CI 30253037478 passed the prior head through build distributions and CI Gate.
  - command: current-develop ownership and path comparison
    result: PASS
    evidence: Develop changes since the prior base are disjoint from all four task-owned paths.
  - command: reconciled head AI Platform CI and zizmor
    result: PASS
    evidence: AI Platform CI 30255198155 and zizmor 30255198970 passed on d6adc30e5bfd1c13771b84ffccf98e19727de11a.
  - command: ready-checkpoint exact-head repository CI
    result: NOT_RUN
    evidence: This final checkpoint update must receive exact-head CI before merge.
  - command: terminal self-hosted smoke
    result: NOT_RUN
    evidence: Infrastructure must merge before a separate exact-one-file trigger is created.
blockers: []
next_action: Run final exact-head repository CI on this ready checkpoint, verify the four-file scope and review state, then guarded-squash merge PR 439 without creating a trigger while the Synology runner remains unavailable.
```
