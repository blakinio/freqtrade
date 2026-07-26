---
task_id: FTAI-20260727-liquidation-okx-shadow-acceptance-infrastructure-v1
status: implementing
branch: feat/okx-shadow-long-run-acceptance-v1
base_branch: develop
created: 2026-07-27
updated: 2026-07-27
related_pr: "pending"
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
  - current develop and open OKX acceptance implementation ownership
  - existing OKX smoke and Liquid20 acceptance implementation patterns
optional_reads: []
---

# OKX liquidation shadow acceptance infrastructure v1

## Goal

Implement the inert runner, deterministic evaluator, independent evidence verifier and guarded self-hosted workflow for the already merged prospective OKX 24-hour acceptance declaration. Do not add the canonical operational request or execute the long run in this infrastructure package.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-27T01:00:00+02:00
head: 1b6a3ff678971e757cb4b5b643168b02a649712a
branch: feat/okx-shadow-long-run-acceptance-v1
pr: "pending"
status: implementing
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
  - The merged declaration requires an always-on non-restricted Linux staging host and forbids GitHub-hosted execution.
  - The merged declaration requires durable raw evidence, self-hashed manifest and report, a checksum index and an immutable storage URI.
  - The existing isolated OKX public collector already writes canonical NDJSON, an instrument snapshot and a summary with clocks, availability, parser, duplicate and latency evidence.
  - The original implementation branch conflict was resolved by resetting to the merged declaration and dropping all overlapping policy, declaration-document and checkpoint changes.
derived:
  - The infrastructure PR must contain no canonical run-request file and must remain inert after merge.
  - Healthy insufficient-activity evidence must be inconclusive; any non-activity failure must be rejected.
  - The trigger workflow must execute only an exact-one-file same-repository request on a labelled self-hosted Linux runner with configured durable storage.
unknown:
  - Exact-head repository CI outcome for the infrastructure implementation.
  - Whether a correctly labelled always-on staging runner is currently online.
  - Terminal outcome of the future 24-hour operational request.
conflicts: []
first_failure:
  marker: infrastructure-not-yet-validated
  evidence: The new implementation has not yet completed repository CI on an exact pull-request head.
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
  - command: python -m compileall ai_platform/scripts/liquidation_okx_shadow_acceptance.py ai_platform/scripts/liquidation_okx_shadow_acceptance_evaluator.py tests/ai_platform_integration/test_liquidation_okx_shadow_acceptance.py
    result: PASS
    evidence: All new Python files parsed and compiled successfully in the available sandbox copy.
  - command: pytest -q tests/ai_platform_integration/test_liquidation_okx_shadow_acceptance.py
    result: NOT_RUN
    evidence: The repository checkout is unavailable locally; exact execution is delegated to repository CI.
  - command: python tools/agents/checkpoint.py docs/agents/tasks/FTAI-20260727-liquidation-okx-shadow-acceptance-infrastructure-v1.md --require-checkpoint
    result: NOT_RUN
    evidence: Repository CI has not yet validated the committed checkpoint.
blockers: []
next_action: Commit the non-overlapping infrastructure files, open a pull request, resolve exact-head CI or review failures, reconcile with current develop and guarded-merge only if all required checks pass.
```
