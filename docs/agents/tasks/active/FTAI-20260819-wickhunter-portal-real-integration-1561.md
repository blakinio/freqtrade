# FTAI-20260819 WickHunter Portal real integration (#1561)

Owning issue: #1561
Authority: ADR-023 + ADR-025

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-20T14:29:57+02:00
branch: fix/1561-wh09-observer-health
head: 85dea7c7e511b49ed0810f7d1571ccb7b18d08f4
pr: null
status: validating
context_routes:
  - issue #1561 Developer Quant MVP
  - merged PR #1619 WickHunter Portal real integration
  - merged PR #1629 Market Evidence canonical-root repair
  - failed v3 adoption run 32363278577 and browser run 32363278611
  - ADR-023 current Developer Quant product authority
  - ADR-025 Synology persistent-runtime authority
owned_paths:
  - ai_platform/portal/control_plane/wh09_runtime.py
  - ai_platform/portal/control_plane/wh09_runtime_observer.py
  - tests/ai_platform/portal/control_plane/test_wh09_runtime.py
  - tests/ci/test_portal_wickhunter_deployed_browser.py
  - .github/workflows/portal-wickhunter-wh09-adoption.yml
  - .github/workflows/portal-wickhunter-wh09-deployed-browser.yml
  - deploy/synology/portal-oidc/run-requests/wickhunter-wh09-portal-adoption-20260820-v4.json
  - docs/agents/tasks/active/FTAI-20260819-wickhunter-portal-real-integration-1561.md
risk: persistent_data=true; research_integrity=false; model_activation=false; auth_or_secrets=true; shared_synology_mutation=true; deployment=true; user_workflow_change=true; destructive_operation=false; real_capital=false; governance_or_ci=true
risk_gates: persistence_or_migration_validation; restart_and_recovery_validation; targeted_security_and_secret_boundary_validation; bounded_resource_ownership; pre_and_post_health_validation; durable_state_and_recovery_validation; artifact_or_image_provenance; target_specific_acceptance; real_applicable_e2e; exact_head_relevant_ci; policy_regression; trusted_base_self_validation; independent_audit
authority_freeze: trusted base develop@01bad9143822bda0c3c0ac6ef2b0078cce738651; unmerged workflow changes cannot waive trusted-base gates
proven:
  - PR #1619 merged at 85892ac9edba4f7ca70a0e65c60d26138f9ca7be
  - PR #1629 merged at 01bad9143822bda0c3c0ac6ef2b0078cce738651 after exact-head CI and fresh independent audit PASS
  - v3 run 32363278577 deployed exact Portal successfully with canonical Market Evidence root /volume1/docker/freqtrade/state/wickhunter-production-market-evidence
  - v3 exact Portal control image sha256:5f383889476bd1c8990d67f9ec543419ca93fceb320c2e70fed57fca2f525f0a became healthy at revision 01bad9143822bda0c3c0ac6ef2b0078cce738651
  - v3 exact Portal web image sha256:078e2732adf5c13c911017e8a5d5d3a51d6dfe1efa139a78b6b9092c1ff64f0f became healthy at revision 01bad9143822bda0c3c0ac6ef2b0078cce738651 with API mode and identity fixtures disabled
  - WH09 remained the same container 58a17f1fba176a8c20fd7e302bbe07ca204352bc405a83aaef13fbca278bb02f at image sha256:994f7bb98ff8489c003128a99fc988c27fd92543274e7fc348b945c5c707e9da and revision 1af35b4ccef6bbd06c771603a80760c342d334aa
  - WH09 direct runtime health recovered and remained healthy; zero-authority remained trading_credentials_present=false order_adapter_present=false execution_enabled=false orders_submitted=0 live_capital_authorized=false
  - v3 observer /healthz returned ready but required 4.52s, 5.37s, 6.29s and 9.75s while Docker health client timeout was 2s; full /evidence required 11.36s while Portal client timeout was 5s
  - run 32363278577 therefore failed closed exactly at Start private read-only WH09 observer and adopt runtime; browser run 32363278611 correctly stopped before Chromium
  - implementation 85dea7c7e511b49ed0810f7d1571ccb7b18d08f4 makes /healthz validate bounded self-hashed health identity and zero-authority without scanning decision history, while /evidence retains full decision validation and uses a bounded 30s private-observer timeout
  - fresh one-shot v4 adoption authorization keeps WH09 redeployment, PAPER activation, trading credentials, execution and live capital unauthorized
  - local observer tests passed 7 tests; deployed-browser tests passed 5 tests; Portal build-plane subset passed 3 tests; workflow plus risk-policy regression passed 13 tests
  - Ruff, mypy, compileall and git diff --check passed for changed implementation paths
derived: []
unknown:
  - exact-head CI result for repair PR head
  - fresh independent audit result for repair diff
  - post-merge v4 adoption, restart and idempotency acceptance
  - real deployed authenticated Chromium result and task-owned cleanup
conflicts:
  - issue #1561 stale ADR-024 dedicated-Linux prose conflicts with binding ADR-025 Synology runtime placement
first_failure:
  marker: WH09_OBSERVER_HEALTH_TIMEOUT
  evidence: v3 adoption run 32363278577 failed at the observer because /healthz scans the full 5800+ decision inventory; measured 4.52-9.75s exceeded its 2s client timeout, and /evidence at 11.36s exceeded the Portal client's 5s timeout
rejected_hypotheses:
  - rerun v3 unchanged; rejected because the one-shot authorization is consumed and exact failure is deterministic
  - only increase the Docker health timeout; rejected because it leaves an unboundedly expensive liveness path and the separate 5s Portal evidence client would still fail
  - weaken full decision-evidence validation; rejected because durable evidence integrity remains an acceptance gate
changed_paths:
  - ai_platform/portal/control_plane/wh09_runtime.py
  - ai_platform/portal/control_plane/wh09_runtime_observer.py
  - tests/ai_platform/portal/control_plane/test_wh09_runtime.py
  - tests/ci/test_portal_wickhunter_deployed_browser.py
  - .github/workflows/portal-wickhunter-wh09-adoption.yml
  - .github/workflows/portal-wickhunter-wh09-deployed-browser.yml
  - deploy/synology/portal-oidc/run-requests/wickhunter-wh09-portal-adoption-20260820-v4.json
  - docs/agents/tasks/active/FTAI-20260819-wickhunter-portal-real-integration-1561.md
validation:
  - command: focused WH09 observer pytest
    result: PASS
    evidence: 7 passed in 1.19s
  - command: deployed-browser plus Portal build-plane focused pytest
    result: PASS
    evidence: 5 passed plus 3 passed
  - command: workflow validation plus risk-policy regression
    result: PASS
    evidence: 13 passed in 1.15s
  - command: Ruff lint/format, mypy, compileall and git diff --check
    result: PASS
    evidence: changed Python and CI paths clean
blockers: []
next_action: Commit this checkpoint, push repair branch, open PR, obtain exact-head CI and fresh independent audit; merge only after both pass, then require v4 adoption plus real authenticated Chromium to pass before closeout.
```
