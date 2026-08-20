# FTAI-20260819 WickHunter Portal real integration (#1561)

Owning issue: #1561
Authority: ADR-023 + ADR-025

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-20T00:09:00+02:00
branch: feat/1561-wickhunter-portal-real-integration
head: 438de0b6747060f9488492aca4c1cfe307d63720
pr: 1619
status: validating
context_routes:
  - issue #1561 Developer Quant MVP
  - PR #1619 WickHunter Portal real integration
  - ADR-023 current Developer Quant product authority
  - ADR-025 Synology persistent-runtime authority
owned_paths:
  - .github/workflows/ai-platform-wickhunter-wh09-production-research-runtime-deploy.yml
  - .github/workflows/portal-wickhunter-wh09-adoption.yml
  - .github/workflows/portal-wickhunter-wh09-deployed-browser.yml
  - deploy/synology/wickhunter-production-research-runtime/run-requests/retry-wh09-production-research-20260819-v7.json
  - deploy/synology/portal-oidc/run-requests/wickhunter-wh09-portal-adoption-20260819-v2.json
  - ai_platform/portal/web/app/bots/page.tsx
  - ai_platform/portal/web/e2e/wickhunter-api-mode-ci.mjs
  - tests/ai_platform_integration/test_wickhunter_production_research_runtime_deploy.py
  - tests/ci/test_github_build_plane.py
  - tests/ci/test_portal_wickhunter_deployed_browser.py
  - docs/agents/tasks/active/FTAI-20260819-wickhunter-portal-real-integration-1561.md
risk: persistent_data=true; research_integrity=false; model_activation=false; auth_or_secrets=true; shared_synology_mutation=true; deployment=true; user_workflow_change=true; destructive_operation=false; real_capital=false; governance_or_ci=true
risk_gates: persistence_or_migration_validation; restart_and_recovery_validation; targeted_security_and_secret_boundary_validation; bounded_resource_ownership; pre_and_post_health_validation; durable_state_and_recovery_validation; artifact_or_image_provenance; target_specific_acceptance; real_applicable_e2e; exact_head_relevant_ci; policy_regression; trusted_base_self_validation; independent_audit
authority_freeze: trusted base develop@1af35b4ccef6bbd06c771603a80760c342d334aa; unmerged workflow changes cannot waive trusted-base gates
proven:
  - develop remains 1af35b4ccef6bbd06c771603a80760c342d334aa
  - PR #1619 remains open, draft and mergeable with base develop
  - previous exact head caf75be46a5f1eca5077dbfeb9e7ae6a8810557d passed an independent audit before the deployed-browser extension
  - terminal Portal adoption fails closed on missing current or post-restart decision and NO_TRADE evidence
  - deployed-browser acceptance no longer uses the high-risk workflow_run trigger
  - deployed-browser acceptance waits on GitHub-hosted compute for the exact adoption run at the same one-shot authorization SHA before Synology access
  - browser session is short-lived RoleName.USER only and exact task-owned identity rows are removed after acceptance
  - deployed browser targets https://quant.molehill.cloud and requires API mode with fixture identity disabled
  - WickHunter durable decision and NO_TRADE counters are rendered on the owner-facing bots page
  - zizmor passed after the workflow_run trigger was removed
  - no real-capital or exchange-order authority is authorized by this task
derived: []
unknown:
  - exact-head CI result for the final checkpoint head
  - fresh independent audit result for the final deployed-browser diff
  - post-merge Synology WH09 and Portal target acceptance
  - real deployed authenticated Chromium result and task-owned session cleanup
conflicts:
  - issue #1561 stale ADR-024 dedicated-Linux prose conflicts with binding ADR-025 Synology runtime placement
first_failure:
  marker: EXACT_HEAD_CI_PENDING
  evidence: implementation head 438de0b6747060f9488492aca4c1cfe307d63720 has the hardened trigger and exact Ruff formatting; checkpoint commit requires the final exact-head CI cycle
rejected_hypotheses:
  - PR-local Chromium against localhost can substitute for actual Synology-deployed browser acceptance; rejected because the owner contract requires the real deployed Portal
  - workflow_run is an acceptable privileged post-deploy trigger; rejected by zizmor dangerous-triggers and replaced with push plus exact-run polling
changed_paths:
  - .github/workflows/ai-platform-wickhunter-wh09-production-research-runtime-deploy.yml
  - .github/workflows/portal-wickhunter-wh09-adoption.yml
  - .github/workflows/portal-wickhunter-wh09-deployed-browser.yml
  - deploy/synology/wickhunter-production-research-runtime/run-requests/retry-wh09-production-research-20260819-v7.json
  - deploy/synology/portal-oidc/run-requests/wickhunter-wh09-portal-adoption-20260819-v2.json
  - ai_platform/portal/web/app/bots/page.tsx
  - ai_platform/portal/web/e2e/wickhunter-api-mode-ci.mjs
  - tests/ai_platform_integration/test_wickhunter_production_research_runtime_deploy.py
  - tests/ci/test_github_build_plane.py
  - tests/ci/test_portal_wickhunter_deployed_browser.py
  - docs/agents/tasks/active/FTAI-20260819-wickhunter-portal-real-integration-1561.md
validation:
  - command: focused Portal/WickHunter/deployment pytest set before deployed-browser extension
    result: PASS
    evidence: 25 passed in 23.11s on the prior implementation head
  - command: risk-policy regression before deployed-browser extension
    result: PASS
    evidence: 9 passed in 0.53s on the prior implementation head
  - command: previous exact-head independent audit at caf75be46a5f1eca5077dbfeb9e7ae6a8810557d
    result: PASS
    evidence: local qwen2.5-coder:14b reported zero P0/P1/P2 findings; invalidated as final gate by later browser changes
  - command: zizmor after removing workflow_run trigger
    result: PASS
    evidence: GitHub Actions Security Analysis succeeded on implementation head 438de0b6747060f9488492aca4c1cfe307d63720
  - command: exact-head CI for final checkpoint head
    result: NOT_RUN
    evidence: final cycle starts after this checkpoint commit
blockers: []
next_action: Inspect exact-head CI for PR #1619 after this checkpoint commit and remediate the first genuine failure; when all relevant jobs pass, run the fresh final independent audit.
```
