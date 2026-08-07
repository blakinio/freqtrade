# FTAI-CA-1116 Portal exact-image supply-chain repair

```yaml
task_id: FTAI-CA-1116-portal-supply-chain
programme_id: FTAI-20260803-portal-remediation
repository: blakinio/freqtrade
issue: 1116
lane: freqtrade-portal
phase: archive_transition
status: complete_on_merge
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
ownership_release: on_merge
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

- both final images are built from exact source and pinned base/runtime digests;
- SBOMs include final-image OS packages plus Python and Node dependencies;
- vulnerability and license policy run on exact final image IDs;
- every suppression is structured, justified, owned and expiry-bounded;
- provenance binds source SHA, Dockerfiles, base digests, manifests, scanner database and final image IDs;
- protected deployment consumes approved exact image IDs without rebuilding after approval;
- current and previous approved images and matching evidence are retained for rollback;
- Portal manifests are covered by dependency-update automation;
- exact-image smoke proves API-mode boot and web-to-control-plane reachability;
- reports and artifacts exclude secrets and private infrastructure;
- focused tests, security analysis, exact-head required CI and independent final audit pass;
- canonical completeness ledger is reconciled and this task is archived before merge.

## Final implementation checkpoint

```yaml
checkpoint_version: 6
updated_at: 2026-08-07T10:34:00Z
status: awaiting_exact_head_ci_and_final_audit
pre_checkpoint_candidate: 00d2b1ede5ac813b11ff8e7f23bbc259620239a3
base_develop: 2525419f5023dbc9bc05fbdff5b3b29917c40eea
pull_request: 1307
issue: 1116
proven:
  - GitHub Actions incident recovery is complete; hosted runners execute normally
  - branch is merge-forwarded to current develop with behind_by zero
  - all one-shot recovery, style, lockfile, merge-forward and evidence-scan workflows are removed from the intended PR diff
  - exact final images produce SBOM, vulnerability, license and SLSA provenance evidence
  - Syft and Grype binaries and the Grype database are checksum/content bound
  - control-plane dependencies were upgraded to available fixed releases; only narrow expiry-bounded CPython suppressions without a stable fix remain
  - web Node runtime is refreshed and npm resolves Next plus the direct dependency to sharp 0.35.3 with no installed sharp below 0.35
  - focused supply-chain tooling passes Ruff and Python compilation after final polish
  - private-IP evidence detection is context-aware: endpoint-bearing fields remain blocked while SBOM versions, CPEs and PURLs are not misclassified
  - focused evidence-policy regression suite passes 19 tests and Ruff after the context-aware scan repair
  - protected deployment consumes approved image IDs without rebuilding after approval
  - current and previous approved image IDs and matching evidence are retained for rollback
  - approval evidence paths are confined to regular files in the approval directory
blockers: []
remaining_terminal_actions:
  - require terminal exact-head Freqtrade CI, Risk-aware component CI, CodeQL, zizmor and Portal Exact-Image Supply Chain
  - perform fresh final diff audit and confirm zero unresolved review threads
  - reconcile the canonical completeness ledger for Issue 1116 without elevating unrelated or external acceptance dimensions
  - archive this task and release ownership
  - rerun exact-head gates if archival changes the head
  - mark PR ready, merge only the verified head and close Issue 1116
next_action: Run exact-head CI from this user-authored checkpoint, then complete audit, ledger reconciliation, archival and merge.
```


## Final closeout evidence

```yaml
validated_implementation_head: ba7b339572bc9e2a96b50614b56037715ec53365
implementation_exact_head_ci:
  freqtrade_ci: 31172539595
  risk_aware_component_ci: 31172539863
  codeql: 31172539567
  zizmor: 31172539813
  portal_exact_image_supply_chain: 31172539652
implementation_gate_result: PASS
independent_final_audit: PASS_ZERO_MATERIAL_FINDINGS
unresolved_review_threads: 0
ledger_reconciliation:
  issue_1116_removed: true
  control_supply_chain_dr: PARTIAL
  remaining_dr_blocker: 1139
protected_target_acceptance_inferred: false
live_capital_authorized: false
protected_production_deployment_authorized: false
ownership_release: on_merge
final_archive_ci: REQUIRED_ON_ARCHIVE_HEAD
```
