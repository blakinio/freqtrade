---
task_id: FTAI-20260727-liquidation-okx-shadow-acceptance-staging-preflight-v1
status: blocked
branch: docs/okx-staging-preflight-terminal-blocker-20260727
base_branch: develop
created: 2026-07-27
updated: 2026-07-27
related_prs:
  - "#442"
  - "#446"
  - "#451"
  - "#458"
  - "#461"
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
  - current develop and open OKX acceptance ownership
  - PR 442 workflow state
  - proven Synology runner executions
optional_reads: []
---

# OKX shadow acceptance staging preflight v1

## Goal

Verify the established Synology self-hosted runner, protected environment, durable state path and public OKX endpoint access without starting liquidation collection or creating the canonical 24-hour request.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-27T13:55:00+02:00
head: PENDING
base_develop: ff304dfd483c45f5a85270d53e528521634bf684
branch: docs/okx-staging-preflight-terminal-blocker-20260727
pr: PENDING
status: blocked
context_routes:
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE.md
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE_EXECUTION.md
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE_STAGING_PREFLIGHT.md
  - docs/agents/tasks/FTAI-20260725-portal-synology-lan-staging.md
owned_paths:
  - docs/agents/tasks/FTAI-20260727-liquidation-okx-shadow-acceptance-staging-preflight-v1.md
proven:
  - PR 461 merged as ff304dfd483c45f5a85270d53e528521634bf684 after exact-head AI Platform CI, Freqtrade CI including CI Gate, and zizmor passed.
  - The guarded workflow now routes only through custom label freqtrade-staging while retaining exact runner-name and Linux checks inside the probe.
  - Canonical current-develop request head 10b9e112e559c335b488df266400812c6eba798f changed exactly one request file.
  - Run 30263621388 was assigned to runner freqtrade-synology-staging.
  - Exact-one-file scope validation and trading-credential refusal passed.
  - The readiness probe failed because OTERYN_STAGING_STATE_DIR from environment synology-staging resolved to an empty value instead of /var/lib/oteryn-staging-state.
  - Artifact upload was skipped; storage atomicity, free space and public OKX endpoint readiness remain unproven.
  - PR 442 was closed without merge after terminal evidence was recorded.
  - No liquidation collection, raw market-data capture, replay, model work, strategy work, execution or order submission occurred.
derived:
  - Runner routing and exact request scope are now proven.
  - The current first failure is protected-environment configuration, not runner availability, routing, request content or stale concurrency.
  - Acceptance-workflow mapping and a 24-hour request remain unauthorized until a fresh preflight produces a complete passing report.
unknown:
  - Whether synology-staging can be configured with OTERYN_STAGING_STATE_DIR=/var/lib/oteryn-staging-state.
  - Whether the prospective durable root is writable and has at least 1 GiB free.
  - Whether public OKX endpoints are reachable from the Synology runner.
  - Whether the durable host path has a separately enforceable immutable snapshot or retention mechanism.
conflicts: []
first_failure:
  marker: EMPTY_PROTECTED_STAGING_STATE_DIR
  evidence: Run 30263621388 reached freqtrade-synology-staging and passed scope and credential checks, but job logs show STAGING_STATE_DIR empty before the runtime readiness probe failed.
rejected_hypotheses:
  - Treat the runner as offline.
  - Recreate or rename the working Synology runner.
  - Fall back to a GitHub-hosted runner or remove the protected environment.
  - Merge the one-file trigger request into develop.
  - Create acceptance-workflow mapping or a 24-hour request before a passing preflight.
validation:
  - command: PR 461 exact-head repository CI
    result: PASS
    evidence: AI Platform CI, Freqtrade CI including CI Gate, and zizmor passed before merge ff304dfd483c45f5a85270d53e528521634bf684.
  - command: canonical current-develop PR 442 preflight run 30263621388
    result: FAIL
    evidence: Runner assignment, exact-one-file validation and credential refusal passed; OTERYN_STAGING_STATE_DIR resolved empty and the report artifact was not produced.
blockers:
  - Configure GitHub Environment synology-staging variable OTERYN_STAGING_STATE_DIR with exact value /var/lib/oteryn-staging-state.
next_action: Configure the protected environment variable, create a new exact-one-file trigger from current develop, rerun the bounded preflight, inspect the terminal report, and proceed to acceptance-workflow mapping only after every readiness and safety field passes.
```
