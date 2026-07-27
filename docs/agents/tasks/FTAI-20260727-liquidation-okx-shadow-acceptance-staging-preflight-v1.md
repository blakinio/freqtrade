---
task_id: FTAI-20260727-liquidation-okx-shadow-acceptance-staging-preflight-v1
status: blocked
branch: docs/okx-preflight-terminal-blocker-20260727
base_branch: develop
created: 2026-07-27
updated: 2026-07-27
related_prs:
  - "#442"
  - "#446"
  - "#451"
  - "#458"
  - "#461"
  - "#464"
owned_paths:
  - docs/agents/tasks/FTAI-20260727-liquidation-okx-shadow-acceptance-staging-preflight-v1.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE.md
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE_EXECUTION.md
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE_STAGING_PREFLIGHT.md
search_first:
  - current develop and OKX acceptance ownership
  - terminal PR 442 workflow evidence
  - protected synology-staging environment configuration
optional_reads: []
---

# OKX shadow acceptance staging preflight v1

## Goal

Verify the established Synology self-hosted runner, protected environment, durable state path and public OKX endpoint access without starting liquidation collection or creating the canonical 24-hour request.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-27T13:56:00+02:00
head: PENDING
base_develop: ff304dfd483c45f5a85270d53e528521634bf684
branch: docs/okx-preflight-terminal-blocker-20260727
pr: "#464"
status: blocked
context_routes:
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE.md
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE_EXECUTION.md
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE_STAGING_PREFLIGHT.md
  - docs/agents/tasks/FTAI-20260725-portal-synology-lan-staging.md
owned_paths:
  - docs/agents/tasks/FTAI-20260727-liquidation-okx-shadow-acceptance-staging-preflight-v1.md
proven:
  - PR 461 passed AI Platform CI 30262418172, Freqtrade CI 30262418114 including CI Gate, and zizmor 30262418155 on exact head 9a9a47dfe5dd27189131f3cb34480dbd55bc2c78.
  - PR 461 merged as ff304dfd483c45f5a85270d53e528521634bf684 and routes the OKX preflight through the unique proven custom label freqtrade-staging while retaining exact runner-name and Linux checks inside the probe.
  - PR 442 was rebuilt directly from that develop head and added exactly the frozen request file at head 10b9e112e559c335b488df266400812c6eba798f.
  - Run 30263621388 job 89969071070 was assigned to runner freqtrade-synology-staging.
  - Exact-one-file scope validation and trading-credential refusal both passed.
  - The first runtime probe failed because STAGING_STATE_DIR, sourced from vars.OTERYN_STAGING_STATE_DIR in protected environment synology-staging, resolved to an empty value.
  - No bounded report artifact was produced because the failure occurred before durable storage or public OKX endpoint checks.
  - PR 442 contains terminal evidence and was closed without merge.
  - No WebSocket subscription, liquidation collection, raw market data, replay, model work, strategy work, execution or order activity occurred.
derived:
  - Runner identity, routing and exact request scope are no longer blockers.
  - The remaining blocker is protected environment configuration, not repository code or Synology runner availability.
  - Acceptance-workflow mapping and the canonical 24-hour request remain unauthorized until a fresh preflight produces a complete passing report.
unknown:
  - Whether /var/lib/oteryn-staging-state exists and is writable under the runner account after the protected variable is configured.
  - Whether the prospective durable root has at least 1 GiB free and passes atomic write, fsync, rename and read-back verification.
  - Whether public OKX time and SWAP instrument endpoints are reachable from the Synology runner.
  - Whether the durable host path has a separately enforceable immutable snapshot or retention mechanism.
conflicts: []
first_failure:
  marker: MISSING_PROTECTED_STAGING_STATE_DIR
  evidence: Run 30263621388 reached the Synology runner, passed exact scope and credential checks, then failed with STAGING_STATE_DIR empty while the frozen contract requires /var/lib/oteryn-staging-state.
rejected_hypotheses:
  - Treat the runner as offline.
  - Change or recreate the proven Synology runner.
  - Bypass the protected environment or hard-code a fallback that would conceal missing configuration.
  - Create an acceptance-workflow mapping or 24-hour request before a passing terminal report.
  - Merge the one-file trigger request into develop.
changed_paths:
  - docs/agents/tasks/FTAI-20260727-liquidation-okx-shadow-acceptance-staging-preflight-v1.md
validation:
  - command: PR 461 exact-head repository CI
    result: PASS
    evidence: AI Platform CI 30262418172, Freqtrade CI 30262418114 including CI Gate, and zizmor 30262418155 succeeded.
  - command: PR 442 exact-one-file trigger scope
    result: PASS
    evidence: Head 10b9e112e559c335b488df266400812c6eba798f changed exactly one request file and workflow scope validation succeeded.
  - command: trading credential refusal
    result: PASS
    evidence: Run 30263621388 completed the credential-refusal step successfully.
  - command: Synology staging readiness probe
    result: BLOCKED
    evidence: vars.OTERYN_STAGING_STATE_DIR resolved empty before storage or network probes; no report artifact was produced.
blockers:
  - Configure GitHub Environment synology-staging variable OTERYN_STAGING_STATE_DIR=/var/lib/oteryn-staging-state.
next_action: After the owner configures the protected variable, create a fresh exact-one-file preflight trigger from current develop, inspect the complete bounded report, close that trigger without merge, and proceed to acceptance-workflow mapping only if every readiness and safety field passes.
```
