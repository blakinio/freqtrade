---
task_id: FTAI-20260727-liquidation-okx-shadow-acceptance-infrastructure-v1
status: blocked
branch: docs/okx-shadow-acceptance-staging-blocker-v1
base_branch: develop
created: 2026-07-27
updated: 2026-07-27
related_pr: "#417 (merged); staging-readiness closeout pending"
owned_paths:
  - ai_platform/scripts/liquidation_okx_shadow_acceptance.py
  - ai_platform/scripts/liquidation_okx_shadow_acceptance_evaluator.py
  - .github/workflows/ai-platform-okx-liquidation-shadow-acceptance.yml
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE_EXECUTION.md
  - tests/ai_platform_integration/test_liquidation_okx_shadow_acceptance.py
  - docs/agents/tasks/FTAI-20260727-liquidation-okx-shadow-acceptance-infrastructure-v1.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_SOURCE.md
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_SMOKE.md
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE.md
search_first:
  - current develop and PR 417 merge state
  - protected staging environment and self-hosted runner readiness
optional_reads: []
---

# OKX liquidation shadow acceptance infrastructure v1

## Result

The inert runner, deterministic three-outcome evaluator, independent evidence verifier and guarded self-hosted workflow are merged for the prospectively frozen OKX 24-hour acceptance declaration. The infrastructure contains no canonical operational request and does not execute the long run, add OKX to Liquid20, authorize replay or model work, or grant trading authority. Execution is blocked until the protected staging environment and labelled runner are verified.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-27T09:15:00+02:00
head: 237196b2b5b3bfbdd52609e139f55f585711d4d5
branch: docs/okx-shadow-acceptance-staging-blocker-v1
pr: not_opened
status: blocked
context_routes:
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE.md
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE_EXECUTION.md
  - ai_platform/research/liquidations/okx-liquidation-shadow-acceptance-policy-v1.json
  - .github/workflows/ai-platform-okx-liquidation-shadow-acceptance.yml
owned_paths:
  - ai_platform/scripts/liquidation_okx_shadow_acceptance.py
  - ai_platform/scripts/liquidation_okx_shadow_acceptance_evaluator.py
  - .github/workflows/ai-platform-okx-liquidation-shadow-acceptance.yml
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE_EXECUTION.md
  - tests/ai_platform_integration/test_liquidation_okx_shadow_acceptance.py
  - docs/agents/tasks/FTAI-20260727-liquidation-okx-shadow-acceptance-infrastructure-v1.md
proven:
  - PR 413 merged the prospective policy, three-outcome model and durable-evidence boundary as develop commit 1b6a3ff678971e757cb4b5b643168b02a649712a.
  - PR 417 merged the six-file acceptance infrastructure package into develop as 237196b2b5b3bfbdd52609e139f55f585711d4d5 from exact head a583bb20453d4ec56f0005ac19e8b828c31abbf7.
  - Exact PR head a583bb20453d4ec56f0005ac19e8b828c31abbf7 passed required repository CI and security gates before merge.
  - The infrastructure reuses the isolated public OKX collector and validates exact host identity, credential-free durable storage, clocks, instruments, canonical events, health, activity, latency, hashes, sizes and self-hashes.
  - Healthy insufficient-activity evidence maps only to inconclusive_insufficient_activity; any non-activity failure maps to rejected.
  - The independent evaluator recomputes the report and verifies the exact five-file checksum package without rewriting evidence.
  - The trigger workflow accepts only a same-repository exact-one-file request on a self-hosted Linux runner labelled okx-liquidation-staging and excludes raw NDJSON from the convenience CI artifact.
  - The workflow requires protected environment variables OKX_ACCEPTANCE_HOST_ID, OKX_ACCEPTANCE_DURABLE_ROOT and OKX_ACCEPTANCE_DURABLE_URI before collection starts.
derived:
  - The repository implementation is complete; the remaining gate is operational host readiness rather than code.
  - Creating a canonical request with guessed host identity or storage URI would violate the frozen request and durable-evidence contract.
  - A passing future run may support only a separate source-integration research proposal and cannot directly authorize Liquid20 membership, replay, models or trading.
unknown:
  - Whether the protected okx-liquidation-staging environment currently exists and contains all three non-empty variables.
  - Exact non-sensitive value of OKX_ACCEPTANCE_HOST_ID.
  - Exact writable absolute OKX_ACCEPTANCE_DURABLE_ROOT outside runner temp and workspace storage.
  - Exact credential-free immutable OKX_ACCEPTANCE_DURABLE_URI.
  - Whether an online self-hosted Linux runner currently carries the okx-liquidation-staging label.
  - Whether the durable root is covered by immutable retention or snapshot policy.
  - Terminal outcome of the future 24-hour operational request.
conflicts: []
first_failure:
  marker: OKX_ACCEPTANCE_STAGING_UNVERIFIABLE_WITH_AVAILABLE_GITHUB_CONNECTOR
  evidence: Repository files, PRs and Actions are accessible, but the available GitHub connector exposes neither protected-environment variable metadata nor self-hosted runner inventory; Issues are also disabled, so a separate operational issue could not be created.
rejected_hypotheses:
  - Create the request with placeholder host identity or durable URI.
  - Start the 24-hour workflow merely to discover whether a runner or environment exists.
  - Modify the prospectively frozen acceptance thresholds.
  - Upload an expiring CI artifact as the sole durable raw authority.
  - Add OKX to liquid20-v1 or authorize replay, models or trading before a separate accepted evidence package and reviewed integration proposal.
changed_paths:
  - docs/agents/tasks/FTAI-20260727-liquidation-okx-shadow-acceptance-infrastructure-v1.md
validation:
  - command: PR 417 merge-state verification
    result: PASS
    evidence: GitHub reports PR 417 merged at 237196b2b5b3bfbdd52609e139f55f585711d4d5 from exact head a583bb20453d4ec56f0005ac19e8b828c31abbf7.
  - command: current develop relation check
    result: PASS
    evidence: develop was identical to 237196b2b5b3bfbdd52609e139f55f585711d4d5 at staging preflight time.
  - command: protected environment variable inspection
    result: BLOCKED
    evidence: The available GitHub connector has no environment-variable or environment-secret inventory action.
  - command: self-hosted runner label and online-state inspection
    result: BLOCKED
    evidence: The available GitHub connector has no repository or organization runner inventory action.
  - command: create operational readiness issue
    result: BLOCKED
    evidence: GitHub returned HTTP 410 because Issues are disabled in this repository.
blockers:
  - Verify or configure protected environment okx-liquidation-staging with OKX_ACCEPTANCE_HOST_ID, OKX_ACCEPTANCE_DURABLE_ROOT and OKX_ACCEPTANCE_DURABLE_URI.
  - Verify an online self-hosted Linux runner carrying the okx-liquidation-staging label.
  - Verify the durable root is writable, outside runner temporary/workspace storage and covered by immutable retention or snapshots.
next_action: Verify the protected okx-liquidation-staging environment, its exact three non-secret variables, durable-root retention and an online labelled self-hosted Linux runner; then create the separate exact-one-file canonical request PR without modifying infrastructure or policy.
```
