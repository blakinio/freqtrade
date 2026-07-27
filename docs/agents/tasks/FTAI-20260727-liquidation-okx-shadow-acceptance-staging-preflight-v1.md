---
task_id: FTAI-20260727-liquidation-okx-shadow-acceptance-staging-preflight-v1
status: ready
branch: fix/okx-preflight-canonical-state-path-20260727
base_branch: develop
created: 2026-07-27
updated: 2026-07-27
related_prs:
  - "#442"
  - "#446"
  - "#461"
  - "#464"
  - "#485"
  - "#531"
  - "#535"
owned_paths:
  - .github/workflows/ai-platform-okx-liquidation-shadow-acceptance-staging-preflight.yml
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE_STAGING_PREFLIGHT.md
  - tests/ai_platform_integration/test_liquidation_okx_shadow_acceptance_staging_preflight.py
  - tests/ai_platform/portal/deployment/test_freqtrade_synology_runner_isolation.py
  - docs/agents/tasks/FTAI-20260727-liquidation-okx-shadow-acceptance-staging-preflight-v1.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE.md
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE_EXECUTION.md
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE_STAGING_PREFLIGHT.md
search_first:
  - current develop and OKX acceptance ownership
  - terminal PR 531 preflight evidence
  - dedicated Freqtrade Synology runner contract
optional_reads: []
---

# OKX shadow acceptance staging preflight v1

## Goal

Complete the non-collecting staging readiness probe on the dedicated Freqtrade Synology runner without depending on an unset mutable GitHub variable.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-27T23:15:00+02:00
head: eba8181a7438622644087028e5005f4e41e5bafa
reconciled_develop: 351567d57760305b992fb1e441205dc32890dc2a
branch: fix/okx-preflight-canonical-state-path-20260727
pr: "#535"
status: ready
context_routes:
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE.md
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE_EXECUTION.md
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE_STAGING_PREFLIGHT.md
owned_paths:
  - .github/workflows/ai-platform-okx-liquidation-shadow-acceptance-staging-preflight.yml
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE_STAGING_PREFLIGHT.md
  - tests/ai_platform_integration/test_liquidation_okx_shadow_acceptance_staging_preflight.py
  - tests/ai_platform/portal/deployment/test_freqtrade_synology_runner_isolation.py
  - docs/agents/tasks/FTAI-20260727-liquidation-okx-shadow-acceptance-staging-preflight-v1.md
proven:
  - The dedicated runner contract uses runner name freqtrade-synology-staging, routing label freqtrade-staging, runner-visible state path /var/lib/freqtrade-staging-state and host path /volume1/docker/freqtrade/state.
  - PR 531 head ff46d0a9aca18c7f103242512944f3c08f932c3e added exactly the frozen request file.
  - Run 30303892424 job 90103281110 executed on freqtrade-synology-staging Linux X64; exact-one-file scope and trading-credential refusal passed.
  - Artifact 8667651053, archive digest sha256:15942015934615970df2783586afde47da8c146f1d6260a3882813de4b0a0dbb, recorded collection_executed false, execution_enabled false, orders_submitted 0 and trading_credentials_present false.
  - The readiness probe failed only because vars.FREQTRADE_STAGING_STATE_DIR resolved to an empty string; PR 531 was closed without merge.
  - PR 535 binds STAGING_STATE_DIR to the canonical dedicated-runner mount while retaining protected environment synology-staging and all exact equality, runner identity, Linux, existence, writability, workspace isolation, atomic I/O, free-space, endpoint and credential checks.
  - Exact head eba8181a7438622644087028e5005f4e41e5bafa passed AI Platform CI 30304630258, zizmor 30304630144, Build Freqtrade Synology Runner Image 30304629939 and Freqtrade CI 30304630029 including Python 3.11-3.14, coverage, build distributions and CI Gate.
  - Develop advanced only through residual-PyTorch checkpoint commit 351567d57760305b992fb1e441205dc32890dc2a, which is path-disjoint from this package.
derived:
  - The state path is frozen by the exact request and dedicated runner mount, so the mutable GitHub variable is redundant rather than an independent safety control.
  - Binding STAGING_STATE_DIR to /var/lib/freqtrade-staging-state preserves fail-closed runtime verification and does not bypass the protected environment.
  - A fresh exact-one-file trigger is required after merge; this infrastructure PR itself performs no collection.
unknown:
  - Terminal result of the fresh post-merge preflight.
  - Whether the canonical runner path passes writability, atomic create/fsync/rename/read-back and free-space checks.
  - Whether public OKX time and SWAP instrument endpoints are reachable from the dedicated runner.
  - Whether the durable host path has a separately enforceable immutable snapshot or retention mechanism.
conflicts: []
first_failure:
  marker: EMPTY_REDUNDANT_STATE_VARIABLE
  evidence: Run 30303892424 reached the correct runner and passed scope and credential checks, then reported state_dir as an empty string before storage or endpoint probes.
rejected_hypotheses:
  - Bypass or remove the protected synology-staging environment.
  - Add a fallback that silently accepts an arbitrary path.
  - Change the dedicated runner name, label or mount.
  - Create the 24-hour acceptance request before a complete passing preflight report.
  - Merge a one-file operational trigger into develop.
changed_paths:
  - .github/workflows/ai-platform-okx-liquidation-shadow-acceptance-staging-preflight.yml
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE_STAGING_PREFLIGHT.md
  - tests/ai_platform_integration/test_liquidation_okx_shadow_acceptance_staging_preflight.py
  - tests/ai_platform/portal/deployment/test_freqtrade_synology_runner_isolation.py
  - docs/agents/tasks/FTAI-20260727-liquidation-okx-shadow-acceptance-staging-preflight-v1.md
validation:
  - command: PR 531 terminal preflight
    result: FAIL_CLOSED
    evidence: Run 30303892424 produced artifact 8667651053 and isolated the empty-variable failure without collection or execution.
  - command: PR 535 exact-head repository CI on eba8181a7438622644087028e5005f4e41e5bafa
    result: PASS
    evidence: AI Platform CI 30304630258, zizmor 30304630144, runner image build 30304629939 and Freqtrade CI 30304630029 including CI Gate succeeded.
blockers: []
next_action: Merge PR 535 after final reconciled exact-head CI, then create a fresh exact-one-file OKX staging preflight trigger from current develop, inspect the bounded report, and close that trigger without merge.
```
