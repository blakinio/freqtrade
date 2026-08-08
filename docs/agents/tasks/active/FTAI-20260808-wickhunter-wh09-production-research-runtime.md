# FTAI-20260808 — WH09 Production Research Runtime

```yaml
task_id: FTAI-20260808-wickhunter-wh09-production-research-runtime
project_lane: freqtrade-wickhunter
programme: WickHunter WH09
policy_version: 2
prompting_standard_version: 2.1
task_kind: implementation
feature_scope:
  type: data_pipeline
  user_facing: false
  backend_required: true
  frontend_required: false
  integration_required: true
  e2e_required: true
  completion_claim: internal_only
execution_mode: chat_github_actions
run_scope: autonomous_program
continuation_policy: continue_until_real_stop
task_completion_policy: finalize_archive_and_continue
implementation_authorized: true
internal_demo_production_deployment_authorized: true
status: waiting
base_branch: develop
trusted_base_sha: 46cd873ccb0c60ec88657d9e7eccb18a93737fd5
branch: diagnose/wickhunter-wh09-runtime-health-20260808
related_issue: 1386
related_pr: 1394
implementation_pr: 1387
implementation_merge_commit: ec0f53cc4df7dfcf008f5f7a4e6ab3733a2cefe5
prior_synology_compat_pr: 1392
prior_synology_compat_merge_commit: c64df386a4fa3ba739b6eaa1a223ca798a7bcae2
no_trade_confidence: 0.60
protected_holdout_accessed: false
test_used_for_selection: false
automatic_promotion_enabled: false
trading_credentials_present: false
order_adapter_present: false
real_exchange_execution_enabled: false
orders_submitted: 0
live_capital_authorized: false
```

## Objective

Deploy one persistent internal-production WH09 research/SHADOW runtime using demo/non-capital data that continuously observes the existing Liquid20 market-data path, performs frozen H900 model inference without weakening `no_trade_confidence=0.60`, journals every eligible decision including `NO_TRADE`, and materializes leakage-safe research outcomes after the frozen `900 s` horizon for future challenger training and operator observation.

The runtime may maintain simulated SHADOW state and outcomes. It may not submit exchange orders, use trading credentials, instantiate a real order adapter, automatically promote a model, or allocate live capital.

## Acceptance inventory

- `A1`: frozen threshold remains exactly `0.60`; no threshold override or bypass exists.
- `A2`: research model identity is explicit and immutable; loading it does not create candidate/PAPER promotion state.
- `A3`: every eligible live/demo decision is durably journaled, including `NO_TRADE`, with model/parameter/dataset/code identities and reason codes.
- `A4`: raw model probability and calibrated confidence are both available in research telemetry without changing execution semantics.
- `A5`: 900 s outcomes are materialized only after the horizon from chronological observations; future data cannot enter decision-time features. Due directional observations remain labelable even after their symbol leaves the current Liquid20 universe.
- `A6`: restart is idempotent and does not duplicate immutable decision/outcome records.
- `A7`: operator telemetry exposes health, decision/no-trade counts, confidence distribution summary, labeled outcome statistics, model/data identities and zero-authority state.
- `A8`: deployment is hardened, internal, demo/non-capital, and contains no trading credential/order/exchange-execution path.
- `A9`: focused/component tests, fresh audit and real internal deployment E2E pass on the exact implementation.
- `A10`: final merged/deployed state records `automatic_promotion_enabled=false`, `trading_credentials_present=false`, `order_adapter_present=false`, `real_exchange_execution_enabled=false`, `orders_submitted=0`, `live_capital_authorized=false`.

## Frozen H900 identity

```yaml
package_id: wickhunter-wh09-candidate-materialization-20260808-r1-h900s-7b23a958fd4d
package_manifest_sha256: 9f5ba852e33915678ca085c2eeafbf526457a079ba8f6f2fb7c1097f1d20ab79
model_artifact_sha256: 0488eaea68a316e3659e3b9e2fcea667eb57de87a22888ce396d112a5c075d2e
model_hash: eddd12e3d0c5922547df89d9fa3d8556b8131a62c3cb8057c5a20c66747a240b
parameter_hash: 014b471b9ccc663c3551a151353ae7cd932bd43ed48b9fbf239baad3483e2c11
runtime_commit: ec0f53cc4df7dfcf008f5f7a4e6ab3733a2cefe5
```

## Evidence and current diagnostic state

- Runtime implementation PR `#1387` merged at `ec0f53cc4df7dfcf008f5f7a4e6ab3733a2cefe5`; dedicated implementation audit run `31262860311`, job `93116251497`, passed with zero open material findings.
- Deployment-control/retry work `#1390` and `#1391` established the protected Synology route and exact-image semantics.
- Synology compatibility PR `#1392` merged at `c64df386a4fa3ba739b6eaa1a223ca798a7bcae2`, removing only the unsupported CPU-CFS/NanoCPUs quota.
- Protected deployment run `31275253098`, job `93147659559`, passed immutable authorization, authorized Compose snapshot, exact runtime checkout, credential/zero-authority/host-path checks and successfully created/started the WH09 container.
- Exact deployed identity from that run: container `6724290d3078f09fc82c434e239d2d8afd3686ddedd27ff7d400834538cfbfe0`; image `sha256:c5a67281912e262a183dd7a5804609a2f69ca356d5eb98e4a5a8da169e07a749`; source revision `ec0f53cc4df7dfcf008f5f7a4e6ab3733a2cefe5`.
- Final E2E verification timed out after 720 seconds with `WH09 deployment E2E did not reach two advances: health is not a regular file`; no PASS report was emitted.
- Synology also discarded the requested PIDs limit because the kernel/cgroup lacks that capability; this remains a separate hardening caveat before final acceptance.
- Exact-head continuation audit on 2026-08-09 found a P1 in the prior diagnostic selector: GitHub Actions does not expose per-commit `added`, `modified`, and `removed` fields in the push payload available to workflows, so event-array-only classification could incorrectly select the normal deploy job for diagnostic v4.
- Repair commit `ba391c90b23cbb017240a94192af8b15276445f2` derives diagnostic-v4 selection from the exact Git `before` -> `after` push range. It requires exact path equality, unshallows the checkout only if the `before` commit is unavailable, and fails classification closed when the range cannot be proven.
- Validation repair `40a6bc310d9ffcedfa3992e511f3b71c284fce33` preserves that behavior while making Git output strictly typed UTF-8 and satisfying mypy/Ruff/pre-commit.
- Regression-gate commit `6c5682f282c195acf88709a810e128303c3f9c64` moves the classifier regression into `tests/ci`, so the mandatory lightweight routing gate executes it instead of only linting it.
- Focused regression coverage models an Actions-style push payload without changed-file arrays, proves whole-push exact-path detection, rejects `.bak` lookalikes and rejects an unprovable/null `before` SHA.
- Diagnostic v4 remains bound to the exact failed run/job, original 64-character container ID and exact image ID. Container discovery uses `docker ps -aq --no-trunc`; secret-free identity evidence is created before identity fail-fast; the diagnostic path contains no start/stop/restart/recreate/remove/kill command.
- Fresh independent review on exact head `90237857d73afb60dbd99ae640ff977d774323bb` found two checkpoint-contract P2s only: unsupported validation result labels and missing required anti-stall counters. This checkpoint repair normalizes those fields without changing runtime, diagnostic, model, threshold or authority semantics.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-09T00:56:05+02:00
head: UNKNOWN
branch: diagnose/wickhunter-wh09-runtime-health-20260808
pr: 1394
status: waiting
context_routes:
  - docs/agents/PROMPTING_STANDARD.md
  - docs/agents/PROMPTING_HANDOVER.md
  - docs/agents/AUTONOMOUS_PROGRAM_CONTINUATION.md
  - .github/workflows/ai-platform-wickhunter-wh09-production-research-runtime-deploy.yml
  - tools/ci/classify_wickhunter_wh09_deploy_request.py
  - tests/ai_platform_integration/test_wickhunter_production_research_runtime_deploy.py
  - tests/ci/test_wickhunter_wh09_deploy_classifier.py
owned_paths:
  - .github/workflows/ai-platform-wickhunter-wh09-production-research-runtime-deploy.yml
  - deploy/synology/wickhunter-production-research-runtime/run-requests/diagnose-wh09-production-research-20260808-v4.json
  - tools/ci/classify_wickhunter_wh09_deploy_request.py
  - tests/ai_platform_integration/test_wickhunter_production_research_runtime_deploy.py
  - tests/ci/test_wickhunter_wh09_deploy_classifier.py
  - docs/agents/tasks/active/FTAI-20260808-wickhunter-wh09-production-research-runtime.md
proven:
  - H900 model and runtime identities remain frozen
  - no_trade_confidence remains 0.60
  - PAPER and all real trading authority remain disabled for the deployed WH09 generation
  - exact WH09 container was created and started on internal Synology by run 31275253098
  - the first actionable deployment failure is absence of runtime operator health.json after container start
  - diagnostic-v4 routing no longer trusts GitHub Actions commit changed-file arrays
  - diagnostic-v4 routing derives exact path membership from the Git push before/after range and fails closed if that range cannot be proven
  - classifier regression is part of the mandatory lightweight routing test suite
  - diagnostic-v4 is bound to the exact recorded container and image and cannot recreate or restart it
  - identity-discovery evidence is persisted before container cardinality or identity fail-fast
derived:
  - after exact-final-head CI and fresh review, merging the diagnostic-only PR can inspect the existing failed deployment without changing runtime authority or recreating the container
unknown:
  - why the started container never produced health.json
  - whether telemetry.json exists independently
  - whether the exact container is currently running restarting or exited
  - whether an enforceable alternative to PIDs limiting exists on this Synology kernel
conflicts: []
first_failure:
  marker: RUNTIME_HEALTH_FILE_ABSENT_AFTER_CONTAINER_START
  evidence: deployment run 31275253098 job 93147659559 timed out after 720 seconds because health.json was not a regular file
rejected_hypotheses:
  - Synology CPU-CFS incompatibility is the remaining health failure; the container starts after the CPU-CFS repair
  - diagnostic mode may be selected by commit-message text or filename substrings
  - GitHub Actions push payload commit changed-file arrays are a valid routing authority
  - an identity mismatch may fail before any diagnostic artifact exists
changed_paths:
  - .github/workflows/ai-platform-wickhunter-wh09-production-research-runtime-deploy.yml
  - deploy/synology/wickhunter-production-research-runtime/run-requests/diagnose-wh09-production-research-20260808-v4.json
  - tools/ci/classify_wickhunter_wh09_deploy_request.py
  - tests/ai_platform_integration/test_wickhunter_production_research_runtime_deploy.py
  - tests/ci/test_wickhunter_wh09_deploy_classifier.py
  - docs/agents/tasks/active/FTAI-20260808-wickhunter-wh09-production-research-runtime.md
validation:
  - command: pre-repair exact-head CI on c198c3725ade5d1f0e62408344d4b5f700fb4eff
    result: NOT_APPLICABLE
    evidence: superseded by the later continuation audit finding on GitHub Actions push-payload routing and repair commit ba391c90b23cbb017240a94192af8b15276445f2
  - command: bounded classifier validation on 40a6bc310d9ffcedfa3992e511f3b71c284fce33
    result: PASS
    evidence: lightweight compile+mypy, Ruff/format, routing/workflow validation and full pre-commit passed; the later test move changes the final closure head but does not invalidate this bounded result
  - command: exact final head CI and independent review after checkpoint-contract repair
    result: NOT_RUN
    evidence: resolve PR #1394 live head after this checkpoint repair and require all applicable exact-head gates plus a fresh independent review before merge
blockers:
  - exact-final-head CI and fresh independent review must pass after this checkpoint repair
next_action: Resolve PR #1394 live head after this checkpoint repair, require exact-final-head CI and a fresh independent review with zero material P1/P2, squash-merge only if green, then consume the diagnostic-v4 Synology artifact before any redeploy or runtime mutation.
invocation_started_at: 2026-08-09T00:25:00+02:00
last_progress_at: 2026-08-09T00:56:05+02:00
ci_checks_for_current_head: 0
unchanged_state_checks: 0
identical_failure_retries: 0
repair_cycles_for_current_gate: 3
context_reconstruction_attempts: 1
stall_warnings: 0
```
