---
task_id: FTAI-20260727-liquidation-okx-shadow-acceptance-staging-preflight-v1
status: ready
branch: feat/okx-shadow-acceptance-staging-preflight-v1
base_branch: develop
created: 2026-07-27
updated: 2026-07-27
related_pr: "#424"
owned_paths:
  - .github/workflows/ai-platform-okx-liquidation-shadow-acceptance-staging-preflight.yml
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE_STAGING_PREFLIGHT.md
  - tests/ai_platform_integration/test_liquidation_okx_shadow_acceptance_staging_preflight.py
  - docs/agents/tasks/FTAI-20260727-liquidation-okx-shadow-acceptance-staging-preflight-v1.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE.md
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE_EXECUTION.md
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE_STAGING_PREFLIGHT.md
search_first:
  - current develop and PR 424 mergeability and exact-head CI
  - established Synology staging runner, environment and durable-state mapping
optional_reads: []
---

# OKX shadow acceptance staging preflight v1

## Result

The inert exact-one-file Synology staging preflight is repository-ready. It validates the
established self-hosted runner, protected environment, durable state path, atomic storage
behavior, free space, public OKX endpoint access and absence of recognized trading
credentials without starting liquidation collection or creating the canonical 24-hour
request.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-27T09:58:00+02:00
head: 0cb7ed878eb2656f3f578759ae94d2b34a365b7f
base_develop: f21a258643d70b4387e366e8b466dbc56735f44f
branch: feat/okx-shadow-acceptance-staging-preflight-v1
pr: "#424"
status: ready
context_routes:
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE.md
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE_EXECUTION.md
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE_STAGING_PREFLIGHT.md
owned_paths:
  - .github/workflows/ai-platform-okx-liquidation-shadow-acceptance-staging-preflight.yml
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE_STAGING_PREFLIGHT.md
  - tests/ai_platform_integration/test_liquidation_okx_shadow_acceptance_staging_preflight.py
  - docs/agents/tasks/FTAI-20260727-liquidation-okx-shadow-acceptance-staging-preflight-v1.md
proven:
  - PR 417 merged the inert runner, evaluator and guarded 24-hour acceptance workflow infrastructure.
  - The established self-hosted runner is oteryn-synology-staging with the custom oteryn-staging label; the protected environment is synology-staging and exposes OTERYN_STAGING_STATE_DIR as /var/lib/oteryn-staging-state.
  - The merged 24-hour workflow targets generic unconfigured staging names, so its canonical request must not be created unchanged.
  - PR 424 adds exactly four preflight workflow, test, runbook and checkpoint files and contains neither a preflight request nor a 24-hour request.
  - The frozen preflight request is validated by exact object equality, preventing undeclared extra authorization fields.
  - The workflow performs no WebSocket subscription or liquidation collection and uploads only bounded non-sensitive readiness evidence.
  - Head b754e78e9a2109383e4b9c114f567a5ead491eba passed AI Platform CI 30246717303, Freqtrade CI 30246717323 and zizmor 30246717320.
  - Reconciled content head 0cb7ed878eb2656f3f578759ae94d2b34a365b7f is based on develop f21a258643d70b4387e366e8b466dbc56735f44f with no overlapping path changes.
derived:
  - A successful preflight can justify a separate workflow-mapping PR but cannot authorize the 24-hour run by itself.
  - The prospective durable root is /var/lib/oteryn-staging-state/okx-liquidation-acceptance with file URI file:///var/lib/oteryn-staging-state/okx-liquidation-acceptance.
  - The canonical 24-hour request remains blocked until terminal preflight evidence and a separately validated workflow mapping exist.
unknown:
  - Terminal preflight result on oteryn-synology-staging.
  - Whether the durable host path has a separately enforceable immutable snapshot or retention mechanism.
conflicts: []
first_failure:
  marker: preflight-not-yet-executed
  evidence: Repository validation is green, but no exact-one-file preflight request has yet run on the Synology staging boundary.
rejected_hypotheses:
  - Create the canonical 24-hour request before staging readiness and workflow mapping are verified.
  - Rename or mutate the existing self-hosted runner from repository code.
  - Run a short liquidation collection as a substitute for the non-collecting preflight.
  - Permit extra keys in the frozen preflight request contract.
  - Treat a passing storage write probe as proof of 24-hour source acceptance.
changed_paths:
  - .github/workflows/ai-platform-okx-liquidation-shadow-acceptance-staging-preflight.yml
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE_STAGING_PREFLIGHT.md
  - tests/ai_platform_integration/test_liquidation_okx_shadow_acceptance_staging_preflight.py
  - docs/agents/tasks/FTAI-20260727-liquidation-okx-shadow-acceptance-staging-preflight-v1.md
validation:
  - command: AI Platform CI exact-head validation
    result: PASS
    evidence: Run 30246717303 passed checkpoint validation, focused tests, Ruff, formatting, codespell and JSON checks on b754e78e9a2109383e4b9c114f567a5ead491eba.
  - command: Freqtrade CI exact-head validation
    result: PASS
    evidence: Run 30246717323 passed pre-commit, documentation, Python 3.11-3.14 tests, coverage, distributions and CI Gate on b754e78e9a2109383e4b9c114f567a5ead491eba.
  - command: zizmor exact-head workflow security analysis
    result: PASS
    evidence: Run 30246717320 passed on b754e78e9a2109383e4b9c114f567a5ead491eba.
blockers: []
next_action: Merge PR 424 only after final exact-head CI passes on the reconciled checkpoint head; then create the separate exact-one-file preflight request PR and close it without merge after terminal readiness evidence is captured.
```
