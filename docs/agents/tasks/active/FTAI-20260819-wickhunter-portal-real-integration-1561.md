# FTAI-20260819 WickHunter Portal real integration (#1561)

Owning issue: #1561
Authority: ADR-023 + ADR-025

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-20T11:39:43+02:00
branch: fix/1561-portal-market-evidence-root
head: 7ed5ed080d22c32d24a20450d246b4b8bbfe3f14
pr: 1629
status: validating
context_routes:
  - issue #1561 Developer Quant MVP
  - merged PR #1619 WickHunter Portal real integration
  - PR #1629 Market Evidence root retry
  - ADR-023 current Developer Quant product authority
  - ADR-025 Synology persistent-runtime authority
owned_paths:
  - tools/agents/portal_supply_chain_runtime.py
  - tests/ai_platform/portal/deployment/test_portal_supply_chain_runtime_hooks.py
  - tests/ci/test_portal_wickhunter_deployed_browser.py
  - .github/workflows/portal-wickhunter-wh09-adoption.yml
  - .github/workflows/portal-wickhunter-wh09-deployed-browser.yml
  - deploy/synology/portal-oidc/run-requests/wickhunter-wh09-portal-adoption-20260820-v3.json
  - docs/agents/tasks/active/FTAI-20260819-wickhunter-portal-real-integration-1561.md
risk: persistent_data=true; research_integrity=false; model_activation=false; auth_or_secrets=true; shared_synology_mutation=true; deployment=true; user_workflow_change=true; destructive_operation=false; real_capital=false; governance_or_ci=true
risk_gates: persistence_or_migration_validation; restart_and_recovery_validation; targeted_security_and_secret_boundary_validation; bounded_resource_ownership; pre_and_post_health_validation; durable_state_and_recovery_validation; artifact_or_image_provenance; target_specific_acceptance; real_applicable_e2e; exact_head_relevant_ci; policy_regression; trusted_base_self_validation; independent_audit
authority_freeze: trusted base develop@85892ac9edba4f7ca70a0e65c60d26138f9ca7be; unmerged workflow changes cannot waive trusted-base gates
proven:
  - PR #1619 merged at 85892ac9edba4f7ca70a0e65c60d26138f9ca7be
  - Synology WH09 deployment run 32344698473 passed exact-image hardening two advancing cycles and zero-authority acceptance
  - Portal adoption run 32344698565 failed closed before observer/adoption/restart because deploy-approved selected a non-existent stale Market Evidence host root
  - failed run used /volume1/docker/freqtrade-staging-state/wickhunter-production-market-evidence
  - canonical runner state-bind resolver and its tests resolve /volume1/docker/freqtrade/state/wickhunter-production-market-evidence
  - implementation 7ed5ed080d22c32d24a20450d246b4b8bbfe3f14 injects the canonical resolver into deploy-approved before Market Evidence installation
  - fresh one-shot v3 adoption authorization is bound to the repaired path and keeps WH09 redeployment unauthorized
  - focused deploy Market Evidence supply-chain and browser tests passed 62 tests
  - risk-policy regression passed 9 tests
  - selected changed-file pre-commit passed mypy Ruff format EOF mixed-line-ending codespell and zizmor
  - workflow syntax routing registry lifecycle local references and pins validate successfully
  - no real-capital exchange-order withdrawal or automatic-promotion authority is authorized
derived: []
unknown:
  - exact-head CI result for final PR #1629 head
  - fresh independent audit result for final PR #1629 diff
  - post-merge v3 Portal adoption and restart acceptance
  - real deployed authenticated Chromium result and task-owned cleanup
conflicts:
  - issue #1561 stale ADR-024 dedicated-Linux prose conflicts with binding ADR-025 Synology runtime placement
first_failure:
  marker: PORTAL_MARKET_EVIDENCE_ROOT_MISMATCH
  evidence: run 32344698565 deploy-approved bound non-existent /volume1/docker/freqtrade-staging-state/wickhunter-production-market-evidence while the canonical runner state-bind resolver yields /volume1/docker/freqtrade/state/wickhunter-production-market-evidence
rejected_hypotheses:
  - create the missing stale directory; rejected because canonical resolver proves this is a storage migration path mismatch and fake data would violate fail-closed research integrity
  - rerun the v2 workflow unchanged; rejected because the exact old authorization SHA still contains the broken supply-chain deployment code
changed_paths:
  - tools/agents/portal_supply_chain_runtime.py
  - tests/ai_platform/portal/deployment/test_portal_supply_chain_runtime_hooks.py
  - tests/ci/test_portal_wickhunter_deployed_browser.py
  - .github/workflows/portal-wickhunter-wh09-adoption.yml
  - .github/workflows/portal-wickhunter-wh09-deployed-browser.yml
  - deploy/synology/portal-oidc/run-requests/wickhunter-wh09-portal-adoption-20260820-v3.json
  - docs/agents/tasks/active/FTAI-20260819-wickhunter-portal-real-integration-1561.md
validation:
  - command: focused Portal deploy Market Evidence supply-chain browser pytest set
    result: PASS
    evidence: 62 passed in 3.54s
  - command: risk-policy regression
    result: PASS
    evidence: 9 passed in 0.61s
  - command: changed-file Ruff lint and format plus workflow validator
    result: PASS
    evidence: Ruff passed and workflow syntax routing registry lifecycle local references and pins are valid
  - command: selected changed-file pre-commit
    result: PASS
    evidence: mypy Ruff format EOF mixed-line-ending debug AST trailing-whitespace codespell and zizmor passed
  - command: git diff --check
    result: PASS
    evidence: implementation commit 7ed5ed080d22c32d24a20450d246b4b8bbfe3f14 is whitespace clean
blockers: []
next_action: Push the checkpoint commit to PR #1629 and obtain exact-head CI for the resulting remote head; remediate only the first genuine failure before final independent audit.
```
