---
task_id: FTAI-20260818-github-build-plane-1608
repository: blakinio/freqtrade
issue: 1608
branch: infra/1608-github-build-plane-adr024
status: validating
execution_mode: github_only
trusted_base: 079193691f199964a67bd69391db953d619844df
supersedes_pr: 1569
pr: 1609
---

# ADR-024 hosted build-plane adoption

## Objective

Adopt the already reviewed implementation work from stale PR #1569 on the current ADR-024 base: Portal, WickHunter and canonical Liquid20 portable image build/scan/publication move to GitHub-hosted Linux while existing Synology jobs are retained only as transitional deployment compatibility until dedicated-Linux Phase C cutover.

## Authority and trust boundary

- Issue #1608 owns this bounded recovery/adoption task under parent Issue #1604.
- ADR-023 remains current Developer Quant product authority.
- ADR-024 is the binding runtime/deployment topology overlay.
- Root `AGENTS.md`, `AGENTS.override.md`, `docs/agents/RISK_BASED_EXECUTION_POLICY.json`, Prompting Standard v3 and Handover Standard v3 are frozen from `develop@079193691f199964a67bd69391db953d619844df` for governance/CI closeout.
- PR #1569, its task record, logs and comments are evidence only. Its old statement that Synology is the target runtime is superseded by ADR-024 and is not imported as authority.

## Non-goals

- no dedicated-Linux physical cutover or claim that such a host exists;
- no new real-money exchange execution, private order credentials, withdrawals or capital authority;
- no model activation;
- no destructive Synology cleanup;
- no broad workflow/package pruning;
- no rewriting of historical Synology deployment evidence.

## Risk

```yaml
risk:
  persistent_data: true
  research_integrity: false
  model_activation: false
  auth_or_secrets: false
  shared_synology_mutation: true
  deployment: true
  user_workflow_change: false
  destructive_operation: false
  real_capital: false
  governance_or_ci: true
risk_gates:
  - persistence_or_migration_validation
  - restart_and_recovery_validation
  - bounded_resource_ownership
  - pre_and_post_health_validation
  - durable_state_and_recovery_validation
  - artifact_or_image_provenance
  - target_specific_acceptance
  - policy_regression
  - trusted_base_self_validation
  - independent_audit
```

The elevated runtime gates are selected because the canonical Liquid20 `develop` push path will mutate the transitional Synology runtime if this change is merged. They do not authorize Phase-C dedicated-Linux deployment.

## Owned paths

- `.github/workflows/portal-oidc-public-deploy.yml`
- `.github/workflows/ai-platform-wickhunter-wh09-production-research-runtime-deploy.yml`
- `.github/workflows/liquidations-live-synology.yml`
- `.github/workflows/packages-cleanup.yml`
- `deploy/synology/liquid20/deploy-live.sh`
- `tests/ai_platform_integration/test_wickhunter_production_research_runtime_deploy.py`
- `tests/ci/test_github_build_plane.py`
- `docs/agents/tasks/active/FTAI-20260818-github-build-plane-1608.md`

## Acceptance

- Portal/WickHunter/Liquid20 portable image build/scan/publication executes on GitHub-hosted Linux rather than the Synology runner.
- Transitional Synology deploy jobs consume exact immutable GHCR image identities and do not silently rebuild under GitHub Actions.
- No-trading-credentials/no-order/no-capital invariants remain fail-closed.
- Liquid20 candidate-first validation, rollback, persistence and public-data health behavior remain intact.
- Fork package cleanup is allowlisted and bounded; no general prune or new recurring trigger is introduced.
- Tests describe Synology as transitional deployment compatibility, not target architecture.
- Exact-final-head relevant CI passes under the current trusted-base governance.
- Fresh independent audit has no unresolved material finding.
- If merge triggers canonical Liquid20 deployment, the exact post-merge run proves GH-hosted build -> immutable GHCR digest -> transitional Synology pull/deploy plus pre/post health, restart/persistence and rollback-relevant evidence.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-18T14:34:00+02:00
branch: infra/1608-github-build-plane-adr024
head: 81bef6e87cc67c5b956726a57e715708016573b1
pr: 1609
status: validating
context_routes:
  - Issue #1608 bounded B0 task
  - Issue #1604 runtime portability programme
  - Issue #1561 Developer Quant vertical slice
  - ADR-023 current product authority
  - ADR-024 runtime/deployment topology authority
  - superseded closed PR #1569 implementation evidence
owned_paths:
  - .github/workflows/portal-oidc-public-deploy.yml
  - .github/workflows/ai-platform-wickhunter-wh09-production-research-runtime-deploy.yml
  - .github/workflows/liquidations-live-synology.yml
  - .github/workflows/packages-cleanup.yml
  - deploy/synology/liquid20/deploy-live.sh
  - tests/ai_platform_integration/test_wickhunter_production_research_runtime_deploy.py
  - tests/ci/test_github_build_plane.py
  - docs/agents/tasks/active/FTAI-20260818-github-build-plane-1608.md
risk:
  persistent_data: true
  research_integrity: false
  model_activation: false
  auth_or_secrets: false
  shared_synology_mutation: true
  deployment: true
  user_workflow_change: false
  destructive_operation: false
  real_capital: false
  governance_or_ci: true
risk_gates:
  - persistence_or_migration_validation
  - restart_and_recovery_validation
  - bounded_resource_ownership
  - pre_and_post_health_validation
  - durable_state_and_recovery_validation
  - artifact_or_image_provenance
  - target_specific_acceptance
  - policy_regression
  - trusted_base_self_validation
  - independent_audit
authority_freeze:
  current_base_commit: 079193691f199964a67bd69391db953d619844df
  note: The task mutates CI/deployment workflows and must close under the trusted-base risk policy active when execution began.
proven:
  - current task branch was reconstructed directly from develop@079193691f199964a67bd69391db953d619844df
  - seven non-task implementation/test blobs from PR #1569 were recovered exactly before ADR-024 wording reconciliation
  - PR #1569 head 1a3ce7d28f1ee126869ac716cff1f56238eaf49d had successful Freqtrade CI 32132647901 and Risk-aware CI 32132648226
  - stale PR #1569 was 13 commits behind current develop and its old task authority treated Synology as target runtime
  - PR #1569 is now closed without merge and explicitly superseded by PR #1609
  - fresh PR #1609 targets exact current trusted base develop@079193691f199964a67bd69391db953d619844df
  - tests/ci/test_github_build_plane.py now describes Synology only as transitional deployment compatibility
  - Liquid20 canonical workflow currently triggers on develop changes to its workflow and deploy package and therefore makes post-merge target verification mandatory
unknown:
  - exact-final-head CI on PR #1609 after this checkpoint commit
  - post-merge GHCR package publication/pull result and transitional Synology Liquid20 deployment result
  - physical dedicated Linux target host and storage transport for Phase C
conflicts: []
first_failure:
  marker: none-current
  evidence: stale branch/authority conflict was resolved by current-base recovery and superseding PR #1569 rather than by force-rebase
rejected_hypotheses:
  - discard the verified #1569 build-plane implementation and reimplement it from scratch
  - force-rebase the stale shared #1569 branch
  - treat transitional Synology deployment success as dedicated-Linux cutover proof
changed_paths:
  - .github/workflows/portal-oidc-public-deploy.yml
  - .github/workflows/ai-platform-wickhunter-wh09-production-research-runtime-deploy.yml
  - .github/workflows/liquidations-live-synology.yml
  - .github/workflows/packages-cleanup.yml
  - deploy/synology/liquid20/deploy-live.sh
  - tests/ai_platform_integration/test_wickhunter_production_research_runtime_deploy.py
  - tests/ci/test_github_build_plane.py
  - docs/agents/tasks/active/FTAI-20260818-github-build-plane-1608.md
validation:
  - command: current-base blob recovery from PR #1569 onto develop@079193691f199964a67bd69391db953d619844df
    result: PASS
    evidence: Git tree cd58f71cc25c5116f982a162177fa9d8d155a583 and commit 0d092eda51387722368ee4c8a7ccfb8ce7a5e3eb
  - command: exact changed-scope review before PR
    result: PASS
    evidence: eight expected paths including the fresh v3 task record; obsolete #1569 task record not imported
  - command: exact-final-head CI
    result: NOT_RUN
    evidence: this checkpoint commit creates the validation head
blockers:
  - Phase C dedicated-Linux cutover remains blocked by unverified physical target; this does not block B0 hosted build-plane adoption
next_action: Verify PR #1609 exact-head CI and full final diff; remediate only concrete failures, then perform the selected independent audit before readiness.
```
