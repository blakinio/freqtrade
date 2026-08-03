# FTAI-20260803 Portal Remediation — Issue 1126

```yaml
task_id: FTAI-20260803-portal-remediation-1126
programme_id: FTAI-20260803-portal-remediation
issue: 1126
repository: blakinio/freqtrade
lane: freqtrade-portal
task_kind: implementation
phase: validate
status: validating
priority: high
prompting_standard_version: 2.1
execution_policy_version: 2
context_pressure: medium
decomposition_decision: single
execution_mode: github_only
run_scope: autonomous_task
continuation_policy: continue_until_real_stop
task_completion_policy: finalize_archive_and_continue
user_communication: terminal_only
feature_scope:
  type: backend_security_vertical_slice
  user_facing: true
  backend_required: true
  frontend_required: false
  integration_required: true
  e2e_required: true
branch: fix/portal-1126-ai-learning-permissions
base_branch: develop
base_head: 9b865a64897ef17004809ccf4973c7a930fe4314
pr: 1149
owned_paths:
  - ai_platform/portal/intelligence/service.py
  - ai_platform/portal/learning/service.py
  - ai_platform/portal/simulator/runner.py
  - tests/ai_platform/portal/test_ai_learning_authorization.py
  - tests/ai_platform/portal/intelligence/test_trade_intelligence_service.py
  - tests/ai_platform/portal/learning/test_learning_service.py
  - tests/ai_platform/portal/control_plane/test_api.py
  - tests/ai_platform/portal/simulator/test_universal_scenario.py
  - docs/ai_platform/portal/AI_LEARNING_PERMISSION_MATRIX.md
  - docs/agents/tasks/active/FTAI-20260803-portal-remediation-1126.md
  - docs/agents/programs/FTAI_PORTAL_REMEDIATION_PROGRAM.md
shared_path_leases: []
producer_dependencies:
  - existing RequestContext and canonical Permission vocabulary
  - existing PermissionDeniedError/require_permission authority
consumer_constraints:
  - do not add a competing authorization framework
  - do not add new permission enum values unless current vocabulary is proven insufficient
  - do not create the #1111 canonical audit writer
  - do not implement #1117 capability-aware UI
  - do not compose the missing #1102 production producer/runtime programme
live_capital_authorized: false
withdrawals_enabled: false
protected_production_deployment_authorized: false
```

## Finding and selected contract

On the exact base, `TradeIntelligenceService` and `LearningService` tenant-scoped records but did not call `require_permission()` in any public method. The public `/v1/trade-analysis`, `/v1/insights` and `/v1/learning/history` routes delegated directly to those services, so any authenticated tenant membership—including the built-in `service` role with only `bot.read`—could read AI/learning evidence. Existing writes and automatic evidence producers also lacked an explicit application-service permission/actor boundary.

The verified least-authority contract reuses the current vocabulary:

- reads: `model.read`;
- bounded hypothesis, experiment and non-promoting candidate writes: `model.train`;
- automatic decision/outcome intelligence production: `ActorType.SERVICE` plus `model.train`;
- model promotion remains separate under `model.promote`.

The deterministic universal simulator no longer derives producer authority from the requesting agent. It requires a separately injected trusted producer context and verifies tenant, service actor, `model.train`, request and correlation provenance before any scenario mutation.

## Acceptance inventory

- [x] Every public intelligence and learning service method enforces one documented permission and automatic producer methods enforce service actor type.
- [x] Intelligence/learning reads require `model.read` and deny service/custom memberships without it.
- [x] Human/agent bounded learning actions require `model.train` and do not require or imply `model.promote`.
- [x] Automatic decision/outcome producers require a tenant-bound trusted service identity with `model.train`.
- [x] Candidate registration remains `promoted=false`, `assigned_to_bot=false` and cannot activate runtime or live capital.
- [x] Permission checks occur before repository lookup/write.
- [x] Direct service and public API routes share the service authorization outcome.
- [x] Tests cover user, trader, analyst, model reviewer, admin, service and custom minimal-permission contexts.
- [x] Current `RequestContext` permissions are evaluated on every call; no permission cache was added.
- [x] Existing canonical Permission/authorization implementation is reused.
- [x] No competing denied-event/audit authority was created; #1111 remains the producer.
- [ ] Second exact-head heavy validation passes after first-attempt defect isolation.
- [ ] Fresh exact-head changed-path audit reports no material finding.
- [ ] PR merges, Issue #1126 closes, task archives and ownership releases.

## Safety

- Frontend visibility is never treated as authorization.
- Service identity is separately injected and cannot inherit browser/agent authority.
- No model promotion, bot assignment, runtime activation, private provider access, trading, withdrawal or live-capital effect is added.
- No AI/learning evidence, tenant data or credentials are logged in denied responses.

## Context checkpoint

```yaml
checkpoint_version: 2
updated_at: 2026-08-03T10:56:00Z
head: c62decc9f6745568886ebbd181d46aca67a8d361
branch: fix/portal-1126-ai-learning-permissions
pr: 1149
status: validating
context_routes:
  - issue #1126
  - ai_platform/portal/intelligence/service.py
  - ai_platform/portal/learning/service.py
  - ai_platform/portal/simulator/runner.py
  - docs/ai_platform/portal/AI_LEARNING_PERMISSION_MATRIX.md
proven:
  - all public intelligence and learning methods now use canonical model.read/model.train checks
  - automatic intelligence production additionally requires ActorType.SERVICE
  - public API routes inherit the same service denial mapping
  - universal simulator previously passed the requesting agent context into automatic intelligence and learning producers
  - simulator now requires a separately injected trusted producer context and validates tenant/actor/permission/request/correlation provenance
  - built-in service remains denied by default because its role grants only bot.read
  - candidate registration remains non-promoting and unassigned
  - first heavy validation reached the complete AI Platform suite; 1080 tests passed and 14 failures were isolated to stale legacy contexts plus simulator producer composition
derived:
  - adding model permissions to existing test identities is a fixture correction where those tests intentionally exercise authorized behaviour
  - injected producer context is required to avoid confused-deputy privilege derivation from a browser/agent request
unknown:
  - final exact-head CI and fresh audit outcome
conflicts: []
first_failure:
  marker: first-heavy-ai-platform-permission-fixture-and-simulator-composition
  evidence: run 30807054648 job 91664752081 on head 7cf442e877d027b1d4a0a56d7e2c4ce2bf6939b5
rejected_hypotheses:
  - weakening service authorization to preserve old tests; rejected
  - adding model.train to the requesting simulator agent; rejected as privilege inheritance
  - tenant equality is sufficient least privilege; rejected
changed_paths:
  - ai_platform/portal/intelligence/service.py
  - ai_platform/portal/learning/service.py
  - ai_platform/portal/simulator/runner.py
  - tests/ai_platform/portal/test_ai_learning_authorization.py
  - tests/ai_platform/portal/intelligence/test_trade_intelligence_service.py
  - tests/ai_platform/portal/learning/test_learning_service.py
  - tests/ai_platform/portal/control_plane/test_api.py
  - tests/ai_platform/portal/simulator/test_universal_scenario.py
  - docs/ai_platform/portal/AI_LEARNING_PERMISSION_MATRIX.md
  - docs/agents/tasks/active/FTAI-20260803-portal-remediation-1126.md
validation:
  - command: AI Platform CI run 30807054648
    tested_sha: 7cf442e877d027b1d4a0a56d7e2c4ce2bf6939b5
    result: FAIL_ISOLATED
    evidence: 14 failed, 1080 passed, 71 skipped; all failures mapped to stale permission fixtures or simulator use of request actor as automatic producer
  - command: GitHub Actions Security Analysis run 30807054695
    tested_sha: 7cf442e877d027b1d4a0a56d7e2c4ce2bf6939b5
    result: PASS
  - command: Portal Completeness Audit run 30807054565
    tested_sha: 7cf442e877d027b1d4a0a56d7e2c4ce2bf6939b5
    result: PASS
blockers:
  - none
next_action: Run the second exact-head validation wave on PR #1149 and isolate only the first relevant failure if any.
```
