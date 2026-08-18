---
task_id: FTAI-20260818-github-build-plane-1608
repository: blakinio/freqtrade
issue: 1608
branch: fix/1608-ghcr-liquid20-package-access
status: validating
execution_mode: github_only
trusted_base: 079193691f199964a67bd69391db953d619844df
repair_base: 6510077ea2e7a63c0d489f94391f461a3cab4ac1
supersedes_pr: 1569
implementation_pr: 1609
repair_pr: 1610
---

# ADR-024 hosted build-plane adoption

## Objective

Adopt the already reviewed implementation work from stale PR #1569 on the current ADR-024 base: Portal, WickHunter and canonical Liquid20 portable image build/scan/publication move to GitHub-hosted Linux while existing Synology jobs are retained only as transitional deployment compatibility until dedicated-Linux Phase C cutover.

## Authority and trust boundary

- Issue #1608 owns this bounded recovery/adoption task under parent Issue #1604.
- ADR-023 remains current Developer Quant product authority.
- ADR-024 is the binding runtime/deployment topology overlay.
- Root `AGENTS.md`, `AGENTS.override.md`, `docs/agents/RISK_BASED_EXECUTION_POLICY.json`, Prompting Standard v3 and Handover Standard v3 remain the governance authority for closeout.
- PR #1569, its task record, logs and comments are evidence only. Its old statement that Synology is the target runtime is superseded by ADR-024 and is not imported as authority.
- PR #1609 is the merged implementation authority for the hosted build-plane slice. PR #1610 owns only the bounded post-merge GHCR package-publication repair.

## Non-goals

- no dedicated-Linux physical cutover or claim that such a host exists;
- no new real-money exchange execution, private order credentials, withdrawals or capital authority;
- no model activation;
- no destructive Synology cleanup;
- no broad workflow/package pruning;
- no rewriting of historical Synology deployment evidence;
- no PAT, new repository secret or manual GHCR ACL bypass to repair package publication.

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

The elevated runtime gates are selected because the canonical Liquid20 `develop` push path mutates the transitional Synology runtime only after hosted image publication succeeds. They do not authorize Phase-C dedicated-Linux deployment.

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
- Exact-final-head relevant CI passes on the repair PR.
- Fresh independent audit has no unresolved material finding.
- The real post-merge Liquid20 run proves GitHub-hosted build -> immutable repo-owned GHCR digest -> transitional Synology pull/deploy plus pre/post health, restart/persistence and rollback-relevant evidence.

## Post-merge GHCR publication repair

- Implementation PR #1609 merged as `6510077ea2e7a63c0d489f94391f461a3cab4ac1` after exact-head CI and an independent final-diff audit passed.
- Canonical `Liquidations Live Synology` run `32142491012` then proved the exact Liquid20 image builds on GitHub-hosted Ubuntu but failed before any Synology deployment mutation because legacy package `ghcr.io/blakinio/liquid20-collector` rejected `GITHUB_TOKEN` with `permission_denied: write_package`.
- Build job `95728248094` built image ID `sha256:d478b8350c4760b46716f57b6d7285ba73b8286f848901c8c17aa9bc9582b571`; deploy job `95728391444` was skipped, so the transitional Synology runtime remained unchanged.
- Repair PR #1610 moves only Liquid20 publication and immutable-digest consumption to fresh repository-owned package `ghcr.io/blakinio/freqtrade-liquid20-collector`. The legacy package is left untouched as historical/external package state.
- No PAT, new secret, package-permission bypass, capital authority or dedicated-Linux cutover is introduced.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-18T16:13:36+02:00
branch: fix/1608-ghcr-liquid20-package-access
head: eb103c3c9380c5682ad564c0ef0f16a7160211bc
pr: 1610
status: validating
context_routes:
  - Issue #1608 bounded B0 task
  - Issue #1604 runtime portability programme
  - Issue #1561 Developer Quant vertical slice
  - ADR-023 current product authority
  - ADR-024 runtime/deployment topology authority
  - merged PR #1609 hosted build-plane implementation
  - repair PR #1610 repo-owned Liquid20 GHCR package
owned_paths:
  - .github/workflows/liquidations-live-synology.yml
  - .github/workflows/packages-cleanup.yml
  - deploy/synology/liquid20/deploy-live.sh
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
  original_task_base: 079193691f199964a67bd69391db953d619844df
  repair_base: 6510077ea2e7a63c0d489f94391f461a3cab4ac1
  note: PR #1610 is a bounded repair of the real post-merge publication failure from PR #1609; it does not reopen architecture authority.
proven:
  - PR #1569 was closed without merge and superseded by current-base PR #1609
  - PR #1609 exact head 8f8b745eb8c1734af855b2c3ebe5cc51bdf98a59 passed Freqtrade CI, Risk-aware CI, Portal exact-image supply-chain, CodeQL, zizmor and independent final-diff audit before merge
  - PR #1609 squash-merged to develop as 6510077ea2e7a63c0d489f94391f461a3cab4ac1
  - post-merge run 32142491012 executed the Liquid20 image build on GitHub-hosted Ubuntu and failed only at legacy GHCR package publication with permission_denied: write_package
  - deploy job 95728391444 was skipped in that failed run, leaving the transitional Synology runtime unchanged
  - repair changes retain GITHUB_TOKEN packages write/read permissions and move Liquid20 only to ghcr.io/blakinio/freqtrade-liquid20-collector
  - deploy-live.sh repair commit changed exactly one digest-regex line and preserved candidate-first, rollback, persistence and no-capital logic
  - liquidations-live-synology.yml repair commit changed exactly the publish repository and exact digest-regex lines
unknown:
  - exact-final-head CI result on PR #1610 after checkpoint and temporary-scaffolding cleanup
  - whether the fresh repo-owned GHCR package accepts first publication from the develop push GITHUB_TOKEN
  - real post-merge Synology target acceptance result after PR #1610 merge
  - physical dedicated Linux target host and storage transport for Phase C
conflicts: []
first_failure:
  marker: ghcr-write-package
  evidence: run 32142491012 build job 95728248094 returned permission_denied: write_package for ghcr.io/blakinio/liquid20-collector before deploy; Synology mutation did not occur
rejected_hypotheses:
  - add a PAT or new repository secret merely to bypass the legacy package ACL
  - manually weaken package permissions or immutable-image checks
  - rebuild the collector on the Synology deploy runner as a fallback
  - treat transitional Synology deployment success as dedicated-Linux cutover proof
changed_paths:
  - .github/workflows/liquidations-live-synology.yml
  - .github/workflows/packages-cleanup.yml
  - deploy/synology/liquid20/deploy-live.sh
  - tests/ci/test_github_build_plane.py
  - docs/agents/tasks/active/FTAI-20260818-github-build-plane-1608.md
validation:
  - command: PR #1609 exact-final-head CI and independent audit
    result: PASS
    evidence: head 8f8b745eb8c1734af855b2c3ebe5cc51bdf98a59; Freqtrade CI 32137313022 and later required CI Gate 95727845196; Risk-aware CI green; audit comment 5328418939 PASS
  - command: canonical post-merge Liquidations Live Synology gate
    result: FAIL_SAFE
    evidence: run 32142491012; hosted image build PASS; GHCR push failed permission_denied: write_package; deploy job 95728391444 SKIPPED
  - command: exact repair patch inspection
    result: PASS
    evidence: workflow commit eb103c3c9380c5682ad564c0ef0f16a7160211bc changes two GHCR path lines only; deploy commit 7adfb2e2736a00c13943921edea08aab5ef80e9b changes one GHCR digest-regex line only
  - command: PR #1610 exact-final-head CI
    result: NOT_RUN
    evidence: this checkpoint commit creates a new validation head
blockers:
  - no current B0 blocker is accepted until PR #1610 exact-head CI and the real post-merge target gate run
  - Phase C dedicated-Linux cutover remains blocked by unverified physical target and is outside #1608 closeout
next_action: Remove the temporary GHCR repair request/executor from PR #1610, verify the final five-file diff and exact-head CI/audit, then merge and require the real post-merge hosted-build -> immutable GHCR -> Synology deploy gate to pass before closing #1608.
```
