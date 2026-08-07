# FTAI-CA-1116 Portal exact-image supply-chain repair

```yaml
task_id: FTAI-CA-1116-portal-supply-chain
programme_id: FTAI-20260803-portal-remediation
repository: blakinio/freqtrade
issue: 1116
lane: freqtrade-portal
phase: finalization
status: blocked_external_ci_service
priority: P1
severity: medium
prompting_standard_version: 2.1
execution_policy_version: 2
task_kind: supply_chain_repair
context_pressure: high
decomposition_decision: phased
execution_mode: github_api_and_actions
run_scope: single_task
continuation_policy: stop_at_task_boundary
task_completion_policy: finalize_archive_and_continue
user_communication: low_noise
base_branch: develop
branch: repair/1116-portal-supply-chain
pull_request: 1307
claim_id: ftaica-1116-20260806T143700Z-gpt56
claim_state: claimed
feature_scope:
  type: infrastructure
  user_facing: false
  backend_required: false
  frontend_required: false
  integration_required: true
  e2e_required: true
  completion_claim: repository_supply_chain_boundary
shared_paths:
  - docs/ai_platform/portal/FEATURE_COMPLETENESS_LEDGER.json
  - docs/ai_platform/portal/FEATURE_COMPLETENESS_LEDGER.md
live_capital_authorized: false
withdrawals_enabled: false
protected_production_deployment_authorized: false
```

## Role and objective

Resolve Issue #1116 by making the exact final Portal web and control-plane images produce complete, secret-free SBOM, vulnerability, license and provenance evidence, and make repository CI fail on policy violations without weakening required checks.

## Acceptance inventory

- both final images are built from exact source and pinned base digests;
- SBOMs include final-image OS packages plus Python and Node dependencies;
- vulnerability and license policy run on exact final image IDs;
- every suppression is structured, justified, owned and expiry-bounded;
- provenance binds source SHA, Dockerfiles, base digests, manifests, scanner database and final image IDs;
- protected deployment consumes approved exact image IDs without rebuilding;
- current and previous approved images and matching evidence are retained for rollback;
- Portal manifests are covered by dependency-update automation;
- exact-image smoke proves API-mode boot and web-to-control-plane reachability;
- reports and artifacts exclude secrets and private infrastructure;
- focused tests, security analysis, exact-head required CI and independent final audit pass;
- canonical completeness ledger is updated and this task is archived before merge.

## Durable checkpoint

```yaml
checkpoint_version: 4
updated_at: 2026-08-06T16:35:00Z
status: blocked_external_ci_service
checkpoint_commit: 1adfde2b37a369b6c1c14d3268bd8c52a963ab72
pull_request: 1307
issue: 1116
proven:
  - exact-image SBOM, vulnerability, license and SLSA provenance implementation exists on PR 1307
  - Syft and Grype tooling and the Grype database are checksum/content bound
  - protected deployment consumes approved exact image IDs without rebuilding
  - rollback retention and evidence-path confinement implementation is locally compiled and tested
  - focused local validation passed with 14 tests and no material final-audit findings in the implemented rollback slice
  - self-cleaning finalization payload is durably staged on the task branch
blocker:
  type: external_service_incident
  service: GitHub Actions
  observed_failure: Service Unavailable while resolving action downloads; hosted and self-hosted runs are queued or failing to start
  official_status: Actions partial outage on 2026-08-06
blocked_terminal_actions:
  - apply the staged finalization commit and canonical ledger projection
  - execute exact-head required CI and security workflows
  - archive the task
  - merge PR 1307
  - close Issue 1116
manual_recovery_entrypoint: .github/workflows/ftai-1116-finalize-ubuntu-latest.yml
next_action: Dispatch the manual recovery workflow only after GitHub Actions can acquire runners; require terminal exact-head CI before merge.
```


## Final implementation checkpoint

```yaml
checkpoint_version: 3
updated_at: 2026-08-07T07:29:29Z
status: awaiting_exact_head_ci_and_final_audit
implementation_head: 98d92d89f1dac4c7287dd5a2cb86e0a9e7b8665e
pull_request: 1307
issue: 1116
proven:
  - exact final images produce SBOM, vulnerability, license and SLSA provenance evidence
  - Grype database content is frozen and bound to each approval
  - protected deployment consumes approved image IDs without rebuilding
  - current and previous approved image IDs and matching evidence are retained for rollback
  - approval evidence paths are confined to regular files in the approval directory
  - canonical completeness ledger removes Issue 1116 while retaining Issue 1139 as the remaining DR blocker
blockers: []
next_action: Require terminal exact-head CI, perform a fresh final diff audit, archive this task, merge PR 1307 and close Issue 1116.
```
