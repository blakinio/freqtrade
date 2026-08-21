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

## Context checkpoint — v6 continuation

```yaml
checkpoint_version: 1
updated_at: 2026-08-21T16:27:15+02:00
branch: fix/1561-browser-v6-runtime-contract-evidence
head: d1c8aafc1b5f3a8664e7a876bb75f5c8d90aab97
pr: 1656
status: blocked
context_routes:
  - issue #1561 Developer Quant MVP remains OPEN
  - PR #1656 v6 canonical-runtime-contract repair
  - PR #1658 independent exact-head audit (never merge)
owned_paths:
  - .github/workflows/portal-wickhunter-wh09-browser-retry-trigger.yml
  - ai_platform/portal/web/e2e/wickhunter-api-mode-ci.mjs
  - deploy/synology/portal-oidc/run-requests/wickhunter-wh09-browser-acceptance-20260821-v6.json
  - deploy/synology/portal-oidc/wickhunter-browser-accept-v6.sh
  - tests/ci/test_portal_wickhunter_browser_retry_trigger.py
risk: persistent_data=true; research_integrity=false; model_activation=false; auth_or_secrets=true; shared_synology_mutation=true; deployment=true; user_workflow_change=true; destructive_operation=false; real_capital=false; governance_or_ci=true
risk_gates: persistence_or_migration_validation; restart_and_recovery_validation; targeted_security_and_secret_boundary_validation; bounded_resource_ownership; pre_and_post_health_validation; durable_state_and_recovery_validation; artifact_or_image_provenance; target_specific_acceptance; real_applicable_e2e; policy_regression; trusted_base_self_validation; independent_audit
authority_freeze: trusted base develop@e715edb71ef7166c7e740b3adefd4f834b3b9972; unmerged CI changes cannot waive trusted-base gates
proven:
  - PR #1656 base is e715edb71ef7166c7e740b3adefd4f834b3b9972 and exact head is d1c8aafc1b5f3a8664e7a876bb75f5c8d90aab97
  - exact-head targeted Portal, supply-chain, CodeQL, zizmor, risk-aware and lightweight PR checks are successful
  - independent audit run 32480003641 job 96764097295 checked out d1c8aafc1b5f3a8664e7a876bb75f5c8d90aab97 and reported RESULT=PASS and FINDINGS=0
  - audit artifact 9446325722 (pr1656-independent-audit-v2-32480003641) has digest sha256:7a6026e1f047347c626966240f13037a8afe6c2b6a3678688f4a1585d65b844a and was downloaded and inspected
  - trusted develop run 32476975481 failed the same Binance trade-history call through CI_WEB_PROXY=http://152.67.66.8:13128 after the 300-second pytest timeout
  - direct probe on 2026-08-21T16:27:15+02:00 received HTTP 403 through that proxy and HTTP 200 from the public Binance time endpoint without it
  - PR #1656 run 32479855573 attempt 3 job 96797477564 has remained in-progress at its Tests step past its configured 30-minute timeout
  - real_capital remains false; no private trading credentials, order adapter, execution, orders, or capital authority were used
unknown:
  - policy-compliant terminal required-CI result after repairing the failed proxy boundary
  - post-merge deployed browser v6 evidence and cleanup
conflicts:
  - issue #1561 historical ADR-024 dedicated-Linux wording conflicts with binding ADR-025 Synology runtime authority
first_failure:
  marker: CI_WEB_PROXY_BINANCE_403
  evidence: CI workflow ci.yml hard-codes the proxy for Online / live compatibility tests; direct proxy probe returns HTTP 403, while direct public endpoint returns HTTP 200
rejected_hypotheses:
  - treat the PR failure as a product regression; rejected because trusted develop reproduces the same external proxy failure and the v6 diff contains no exchange/CCXT code
  - merge while CI is nonterminal; rejected because exact-final-head CI remains a required gate
blockers:
  - a smallest-scope CI proxy repair would move the #1656 head and invalidate its audit; repository AGENTS.md prohibits invoking an owner-funded AI audit without explicit current owner authorization for that exact use
next_action: Obtain explicit current owner authorization to trigger the required fresh independent AI audit after the smallest CI proxy-boundary repair, then update #1656, validate its exact final head, and continue merge and deployed acceptance.
```
