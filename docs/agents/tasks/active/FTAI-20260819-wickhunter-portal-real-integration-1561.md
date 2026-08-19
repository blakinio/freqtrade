# FTAI-20260819 WickHunter Portal real integration (#1561)

Owning issue: #1561
Authority: ADR-023 + ADR-025

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-19T15:50:00+02:00
branch: feat/1561-wickhunter-portal-real-integration
head: 1af35b4ccef6bbd06c771603a80760c342d334aa
pr: none
status: implementing
context_routes:
  - issue #1561 Developer Quant MVP
  - issue #1089 Portal API-mode deployment finding
  - programme #1210 WickHunter
  - ADR-023 current Developer Quant product authority
  - ADR-025 Synology persistent-runtime authority
owned_paths:
  - .github/workflows/ai-platform-wickhunter-wh09-production-research-runtime-deploy.yml
  - .github/workflows/portal-wickhunter-wh09-adoption.yml
  - deploy/synology/wickhunter-production-research-runtime/run-requests/retry-wh09-production-research-20260819-v7.json
  - deploy/synology/portal-oidc/run-requests/wickhunter-wh09-portal-adoption-20260819-v2.json
  - tests/ai_platform_integration/test_wickhunter_production_research_runtime_deploy.py
  - tests/ci/test_github_build_plane.py
  - docs/agents/tasks/active/FTAI-20260819-wickhunter-portal-real-integration-1561.md
risk: persistent_data=true; research_integrity=false; model_activation=false; auth_or_secrets=true; shared_synology_mutation=true; deployment=true; user_workflow_change=true; destructive_operation=false; real_capital=false; governance_or_ci=true
risk_gates: persistence_or_migration_validation; restart_and_recovery_validation; bounded_resource_ownership; pre_and_post_health_validation; durable_state_and_recovery_validation; artifact_or_image_provenance; target_specific_acceptance; independent_audit; real_applicable_e2e; exact_head_relevant_ci; policy_regression; trusted_base_self_validation; targeted_security_and_secret_boundary_validation
authority_freeze: trusted base develop@1af35b4ccef6bbd06c771603a80760c342d334aa; workflow changes cannot waive base policy gates
proven:
  - develop head is 1af35b4ccef6bbd06c771603a80760c342d334aa
  - no open PR owns the exact WickHunter-to-Portal integration slice
  - live Portal web revision 0e7825bf860cd8011e1bd9207fcb0765baf8d52a runs PORTAL_WEB_DATA_MODE=fixture
  - live freqtrade-portal-control-plane is stopped
  - current develop contains the merged #1089 full authenticated control-plane and API-mode code repair
  - legacy WickHunter revision 108eff8149f3c5dba77bfcdeaea0c63c8a22b551 runs but Docker health fails because its healthcheck cannot import ai_platform
  - WH09 production-research revision 90cfc5ded10b0c6cb6406d00042817aca611e900 was started without recreation and remains fail-closed
  - fail-closed root cause is Liquid20 source events binance-usdm contradicts events_written
  - merged fix #1487 commit 584538e9867d38a17b3b1a27f7b9cce452af318a repairs legacy restart suffix reconciliation and is present in current develop
  - WH09 production-research mounts durable host state under /volume1/docker/freqtrade/state
  - issue #1561 remains open and its DEDICATED_LINUX wording is superseded by ADR-025
  - issue #1089 remains open but its repository repair was merged as commit 1ba7a5a4a
  - programme #1210 remains open
derived: []
unknown:
  - whether a WH09 image rebuilt from current develop reaches HEALTHY on the existing durable state
  - whether Portal PostgreSQL already contains canonical bot_id=wickhunter and matching RuntimeGeneration
  - whether current develop deploy can safely reconcile the stale live Portal without additional code changes
  - real deployed authenticated Chromium acceptance using a bounded task-owned read-only synthetic session after deployment
conflicts:
  - issue #1561 stale ADR-024 dedicated-Linux prose conflicts with binding ADR-025 Synology runtime placement
first_failure:
  marker: WH09_RUNTIME_HEALTH
  evidence: production-research WH09 is fail-closed on stale pre-#1487 image; Portal is also stale fixture-mode and will be reconciled after runtime health
rejected_hypotheses:
  - current develop still lacks #1089 composition repair; rejected because public_runtime.py composes create_identity_enabled_app/create_app and deploy.py sets API mode
changed_paths:
  - .github/workflows/ai-platform-wickhunter-wh09-production-research-runtime-deploy.yml
  - .github/workflows/portal-wickhunter-wh09-adoption.yml
  - deploy/synology/wickhunter-production-research-runtime/run-requests/retry-wh09-production-research-20260819-v7.json
  - deploy/synology/portal-oidc/run-requests/wickhunter-wh09-portal-adoption-20260819-v2.json
  - tests/ai_platform_integration/test_wickhunter_production_research_runtime_deploy.py
  - tests/ci/test_github_build_plane.py
  - docs/agents/tasks/active/FTAI-20260819-wickhunter-portal-real-integration-1561.md
validation:
  - command: live read-only Synology Docker preflight
    result: PASS
    evidence: exact container/image/runtime state captured before mutation
  - command: focused Portal/WickHunter/backend/deployment pytest set
    result: PASS
    evidence: 39 passed; public composition, bootstrap, runtime adoption, deploy contract, hosted-build policy
  - command: changed workflow YAML plus bash syntax validation
    result: PASS
    evidence: both workflows parse; 23 bash run steps pass bash -n
  - command: Ruff changed Python tests plus git diff --check and checkpoint validation
    result: PASS
    evidence: all checks passed; checkpoint valid
blockers: []
next_action: Commit the validated implementation on the dedicated branch, push it, and open a Draft PR to develop for exact-head CI before any runtime recreation.
```