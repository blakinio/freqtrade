# FTAI-20260819 WickHunter Portal real integration (#1561)

Owning issue: #1561
Authority: ADR-023 + ADR-025

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-19T23:09:28+02:00
branch: feat/1561-wickhunter-portal-real-integration
head: b57a3321ed9cfcd375132d67b39cd0121701f490
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
  - deploy/synology/wickhunter-production-research-runtime/run-requests/retry-wh09-production-research-20260819-v7.json
  - deploy/synology/portal-oidc/run-requests/wickhunter-wh09-portal-adoption-20260819-v2.json
  - tests/ai_platform_integration/test_wickhunter_production_research_runtime_deploy.py
  - tests/ci/test_github_build_plane.py
  - docs/agents/tasks/active/FTAI-20260819-wickhunter-portal-real-integration-1561.md
risk: persistent_data=true; research_integrity=false; model_activation=false; auth_or_secrets=true; shared_synology_mutation=true; deployment=true; user_workflow_change=true; destructive_operation=false; real_capital=false; governance_or_ci=true
risk_gates: persistence_or_migration_validation; restart_and_recovery_validation; targeted_security_and_secret_boundary_validation; bounded_resource_ownership; pre_and_post_health_validation; durable_state_and_recovery_validation; artifact_or_image_provenance; target_specific_acceptance; real_applicable_e2e; exact_head_relevant_ci; policy_regression; trusted_base_self_validation; independent_audit
authority_freeze: trusted base develop@1af35b4ccef6bbd06c771603a80760c342d334aa; workflow/governance-sensitive changes remain governed by trusted-base controls until merge
proven:
  - develop remains 1af35b4ccef6bbd06c771603a80760c342d334aa
  - PR #1619 is open, draft and mergeable with base develop
  - PR #1619 remote head before this correction was 7b4570f7100da03fd77a76c0e604a4d54520f6d4
  - old-head pre-commit and Python 3.13 core failures reduce to Ruff formatting and checkpoint EOF findings
  - old-head Universal Portal chromium-journey was canceled; no application assertion failure was established from its terminal log
  - terminal Portal adoption now explicitly fails closed on missing current or post-restart decision and NO_TRADE evidence
  - issue #1561 remains open and its ADR-024 dedicated-Linux wording is superseded by ADR-025
  - no real-capital authority is authorized by this task
derived: []
unknown:
  - exact-head CI result for the new PR head after push
  - required final independent audit result after this correction
  - current Synology WH09/Portal mutable runtime state has not yet been revalidated in this continuation session
  - whether the accepted WH09 image reaches HEALTHY on existing durable state
  - deployed authenticated Chromium acceptance after merge
conflicts:
  - issue #1561 stale ADR-024 dedicated-Linux prose conflicts with binding ADR-025 Synology runtime placement
first_failure:
  marker: EXACT_HEAD_CI_PENDING
  evidence: new local correction is not yet pushed; exact-head GitHub checks have not run for b57a3321ed9cfcd375132d67b39cd0121701f490
rejected_hypotheses:
  - old-head core Python 3.13 failure demonstrated a runtime architecture defect; rejected because its terminal failure was Ruff format --check
changed_paths:
  - .github/workflows/ai-platform-wickhunter-wh09-production-research-runtime-deploy.yml
  - .github/workflows/portal-wickhunter-wh09-adoption.yml
  - deploy/synology/wickhunter-production-research-runtime/run-requests/retry-wh09-production-research-20260819-v7.json
  - deploy/synology/portal-oidc/run-requests/wickhunter-wh09-portal-adoption-20260819-v2.json
  - tests/ai_platform_integration/test_wickhunter_production_research_runtime_deploy.py
  - tests/ci/test_github_build_plane.py
  - docs/agents/tasks/active/FTAI-20260819-wickhunter-portal-real-integration-1561.md
validation:
  - command: ruff check + ruff format --check on changed Python tests
    result: PASS
    evidence: Ruff reports all checks passed and both files formatted
  - command: focused Portal/WickHunter/deployment pytest set under existing WSL task dependencies
    result: PASS
    evidence: 25 passed in 23.11s
  - command: pytest -q tests/ci/test_agent_risk_policy.py under existing WSL task dependencies
    result: PASS
    evidence: 9 passed in 0.53s
  - command: parse changed workflow YAML and bash -n every run block
    result: PASS
    evidence: both workflows parsed; 23 run steps pass bash -n
  - command: focused pre-commit ruff-format and end-of-file-fixer hooks
    result: PASS
    evidence: both hooks passed
  - command: git diff --check
    result: PASS
    evidence: no whitespace errors
blockers: []
next_action: Push the checkpoint commit to PR #1619 and obtain exact-head CI for the resulting remote head.
```
