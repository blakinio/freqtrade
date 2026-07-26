---
task_id: FTAI-20260727-liquidation-okx-shadow-acceptance-infrastructure-v1
status: ready
branch: feat/okx-shadow-long-run-acceptance-v1
base_branch: develop
created: 2026-07-27
updated: 2026-07-27
related_pr: "#417"
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
  - current develop and PR 417 mergeability and exact-head CI
  - protected staging environment and self-hosted runner readiness
optional_reads: []
---

# OKX liquidation shadow acceptance infrastructure v1

## Result

The inert runner, deterministic three-outcome evaluator, independent evidence verifier and guarded self-hosted workflow are implemented for the prospectively frozen OKX 24-hour acceptance declaration. The infrastructure contains no canonical operational request and does not execute the long run, add OKX to Liquid20, authorize replay or model work, or grant trading authority.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-27T01:44:00+02:00
head: b3f60e981a3ccb4f6511eff3a7bcaa5487bab82d
branch: feat/okx-shadow-long-run-acceptance-v1
pr: "#417"
status: ready
context_routes:
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE.md
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE_EXECUTION.md
  - ai_platform/research/liquidations/okx-liquidation-shadow-acceptance-policy-v1.json
owned_paths:
  - ai_platform/scripts/liquidation_okx_shadow_acceptance.py
  - ai_platform/scripts/liquidation_okx_shadow_acceptance_evaluator.py
  - .github/workflows/ai-platform-okx-liquidation-shadow-acceptance.yml
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE_EXECUTION.md
  - tests/ai_platform_integration/test_liquidation_okx_shadow_acceptance.py
  - docs/agents/tasks/FTAI-20260727-liquidation-okx-shadow-acceptance-infrastructure-v1.md
proven:
  - PR 413 merged the prospective policy, three-outcome model and durable-evidence boundary as develop commit 1b6a3ff678971e757cb4b5b643168b02a649712a.
  - The infrastructure reuses the isolated public OKX collector and validates exact host identity, credential-free durable storage, clocks, instruments, canonical events, health, activity, latency, hashes, sizes and self-hashes.
  - Healthy insufficient-activity evidence maps only to inconclusive_insufficient_activity; any non-activity failure maps to rejected.
  - The independent evaluator recomputes the report and verifies the exact five-file checksum package without rewriting evidence.
  - The trigger workflow accepts only a same-repository exact-one-file request on a labelled self-hosted Linux runner and deliberately excludes raw NDJSON from the convenience CI artifact.
  - PR 417 changes exactly six infrastructure, test, runbook and checkpoint files and contains no canonical run-request file.
  - Reconciled infrastructure content head b3f60e981a3ccb4f6511eff3a7bcaa5487bab82d is zero commits behind develop 185e6a5a8fc2c5d70d0ea2173f4c5cd4a5ca702c.
  - Head b3f60e981a3ccb4f6511eff3a7bcaa5487bab82d passed AI Platform CI 30225330763, Freqtrade CI 30225330767 and zizmor 30225330760.
derived:
  - The infrastructure package is repository-ready and remains inert until a separate canonical request is created after staging readiness is verified.
  - A passing future run may support only a separate source-integration research proposal and cannot directly authorize Liquid20 membership, replay, models or trading.
unknown:
  - Whether the protected okx-liquidation-staging environment currently has all three required variables configured.
  - Whether an online self-hosted Linux runner currently carries the okx-liquidation-staging label.
  - Terminal outcome of the future 24-hour operational request.
conflicts: []
first_failure:
  marker: okx-acceptance-staging-not-verified
  evidence: Repository infrastructure CI passed, but the protected environment variables, exact staging host and online labelled runner have not yet been verified.
rejected_hypotheses:
  - Modify the already merged prospective acceptance thresholds in the infrastructure PR.
  - Commit the canonical operational request together with runner or workflow code.
  - Treat insufficient activity as rejection when all non-activity gates pass.
  - Execute branch-controlled code on a self-hosted runner without exact-one-file scope validation.
  - Upload an expiring CI artifact as the sole durable raw authority.
changed_paths:
  - ai_platform/scripts/liquidation_okx_shadow_acceptance.py
  - ai_platform/scripts/liquidation_okx_shadow_acceptance_evaluator.py
  - .github/workflows/ai-platform-okx-liquidation-shadow-acceptance.yml
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE_EXECUTION.md
  - tests/ai_platform_integration/test_liquidation_okx_shadow_acceptance.py
  - docs/agents/tasks/FTAI-20260727-liquidation-okx-shadow-acceptance-infrastructure-v1.md
validation:
  - command: AI Platform CI exact-head validation
    result: PASS
    evidence: Run 30225330763 passed compileall, focused integration tests, checkpoint validation, Ruff, formatting, codespell and JSON checks on b3f60e981a3ccb4f6511eff3a7bcaa5487bab82d.
  - command: Freqtrade CI exact-head validation
    result: PASS
    evidence: Run 30225330767 passed pre-commit, documentation, Python 3.11-3.14 tests, coverage, smoke checks, type checks, distributions and CI Gate on b3f60e981a3ccb4f6511eff3a7bcaa5487bab82d.
  - command: zizmor exact-head workflow security analysis
    result: PASS
    evidence: Run 30225330760 passed on b3f60e981a3ccb4f6511eff3a7bcaa5487bab82d.
  - command: python tools/agents/checkpoint.py docs/agents/tasks/FTAI-20260727-liquidation-okx-shadow-acceptance-infrastructure-v1.md --require-checkpoint
    result: PASS
    evidence: AI Platform CI 30225330763 validated the compact checkpoint against GOVERNANCE_CONTRACT.json.
blockers: []
next_action: Verify the protected okx-liquidation-staging environment, its exact three variables and an online labelled self-hosted Linux runner; only then create the separate exact-one-file canonical request PR for the 24-hour run.
```
