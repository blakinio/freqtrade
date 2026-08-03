# FTAI-20260803 Portal Remediation — Issue 1126

```yaml
task_id: FTAI-20260803-portal-remediation-1126
programme_id: FTAI-20260803-portal-remediation
issue: 1126
repository: blakinio/freqtrade
lane: freqtrade-portal
task_kind: implementation
phase: reproduce
status: implementing
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
pr: none
owned_paths:
  - ai_platform/portal/intelligence/service.py
  - ai_platform/portal/learning/service.py
  - tests/ai_platform/portal/**intelligence**
  - tests/ai_platform/portal/**learning**
  - tests/ai_platform/portal/**control_plane**
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
  - do not compose the missing #1102 producer/runtime programme
live_capital_authorized: false
withdrawals_enabled: false
protected_production_deployment_authorized: false
```

## Finding reproduced

On the exact base, `TradeIntelligenceService` and `LearningService` tenant-scope records but do not call `require_permission()` in any public method. The public `/v1/trade-analysis`, `/v1/insights` and `/v1/learning/history` routes delegate directly to those services, so any authenticated tenant membership—including the built-in `service` role with only `bot.read`—can read AI/learning evidence. Existing write/producer methods likewise lack an application-service permission and actor boundary.

The canonical vocabulary already contains `model.read`, `model.train` and `model.promote`. This task begins with the least-authority hypothesis that AI/learning reads use `model.read`, bounded hypothesis/experiment/candidate creation uses `model.train`, and automatic trade-evidence production requires a tenant-bound `ActorType.SERVICE` plus `model.train`. Candidate registration remains non-promoting and cannot imply runtime activation. This hypothesis must be challenged against live call sites and tests before finalization.

## Acceptance inventory

- [ ] Every public intelligence and learning service method enforces one documented permission and, for automatic producer methods, an explicit actor-type policy.
- [ ] Intelligence/learning reads require `model.read` and deny a service/custom membership without it.
- [ ] Human bounded learning actions require `model.train` and do not require or imply `model.promote`.
- [ ] Automatic decision/outcome evidence producers require a trusted tenant-bound service identity with `model.train`; browser/user/trader/analyst authority cannot impersonate the producer.
- [ ] Candidate registration remains `promoted=false`, `assigned_to_bot=false` and cannot activate runtime or live capital.
- [ ] Permission checks occur before repository lookup/write so cross-tenant/resource-enumeration attempts fail without revealing record existence.
- [ ] Direct service calls and public API routes produce the same authorization outcome.
- [ ] Tests cover user, trader, analyst, model reviewer, admin, service and custom minimal-permission contexts.
- [ ] Permission removal is observed on the next request because authorization derives from the current `RequestContext`.
- [ ] Existing canonical Permission/authorization implementation is reused; no competing framework or broad permission migration is introduced.
- [ ] Existing audit/security behaviour is preserved; canonical denied-event expansion remains owned by #1111 unless an existing writer can be reused without new authority.
- [ ] Focused tests, full AI Platform CI, bounded API integration, exact-head repository CI, fresh changed-path audit and applicable Portal/API-mode E2E pass.
- [ ] PR merges, Issue #1126 closes, task archives and ownership releases.

## Safety

- Frontend visibility is never treated as authorization.
- Service identity cannot inherit browser cookies or arbitrary user authority.
- No model promotion, bot assignment, runtime activation, private provider access, trading, withdrawal or live-capital effect is added.
- No AI/learning evidence, tenant data or credentials are logged in denied responses.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-03T10:44:00Z
head: 9b865a64897ef17004809ccf4973c7a930fe4314
branch: fix/portal-1126-ai-learning-permissions
pr: none
status: implementing
context_routes:
  - issue #1126
  - ai_platform/portal/intelligence/service.py
  - ai_platform/portal/learning/service.py
  - ai_platform/portal/contracts/identity.py
  - ai_platform/portal/security/authorization.py
  - ai_platform/portal/control_plane/context.py
  - ai_platform/portal/control_plane/api_core.py
proven:
  - every public intelligence service method lacks require_permission
  - every public learning service method lacks require_permission
  - the three public read routes delegate directly to those services
  - built-in service role has only bot.read but currently reaches these reads
  - existing model.read/model.train/model.promote vocabulary and require_permission authority exist
  - no overlapping branch, open PR or durable task for issue 1126 was found
  - issue 1124 is terminal and develop exact head is 9b865a64897ef17004809ccf4973c7a930fe4314
derived:
  - existing model.read/model.train scopes are the smallest non-migrating permission matrix unless call-site evidence disproves it
  - service-only plus model.train is the narrow initial automatic-producer policy
unknown:
  - exact current test filenames and every internal producer call site, to resolve before mutation
  - whether an existing bounded audit/security emitter can record denial without claiming #1111 authority
conflicts: []
first_failure:
  marker: ai-learning-authenticated-membership-overreach
  evidence: tenant-only service methods and direct public route delegation
rejected_hypotheses:
  - tenant equality is sufficient least privilege; rejected
  - route/UI checks can replace service authorization; rejected
  - model.train implies promotion/runtime activation; rejected by separate model.promote boundary
changed_paths:
  - docs/agents/tasks/active/FTAI-20260803-portal-remediation-1126.md
validation:
  - command: static exact-base reproduction
    result: FAIL_EXPECTED
    evidence: no permission or actor checks in intelligence/learning service methods
blockers:
  - none
next_action: Resolve all intelligence/learning call sites and tests, then implement the smallest canonical model.read/model.train plus trusted-service producer matrix at the application-service boundary.
```
